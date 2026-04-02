import os
import time
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from llm import MockProvider, OllamaProvider
from db import (
    create_db_and_tables, 
    search_items, 
    save_items_for_post, 
    get_user_items, 
    update_item_status, 
    update_item_details, 
    delete_post
)
from processor import sync_channel
from logger import log_basic

load_dotenv()

# Initialize Slack App
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Select LLM Provider
provider_type = os.environ.get("LLM_PROVIDER", "mock").lower()
log_basic(f"Initializing with LLM_PROVIDER: {provider_type}")

if provider_type == "ollama":
    llm = OllamaProvider(model=os.environ.get("OLLAMA_MODEL", "llama3"))
else:
    llm = MockProvider()

# --- UI Helpers ---

def get_overview_modal(channel_id):
    return {
        "type": "modal",
        "callback_id": "overview_modal",
        "private_metadata": channel_id,
        "title": {"type": "plain_text", "text": "BuyerBot Overview"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Welcome to BuyerBot! What would you like to do?"},
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "Add Listing (Sale)"}, "action_id": "open_add_modal", "style": "primary"},
                    {"type": "button", "text": {"type": "plain_text", "text": "Seeking Item (WTB)"}, "action_id": "open_seeking_modal"},
                    {"type": "button", "text": {"type": "plain_text", "text": "My Listings"}, "action_id": "open_my_listings"},
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "Sync Channel History"}, "action_id": "trigger_sync"},
                ]
            }
        ]
    }

def get_item_modal(title, callback_id, post_type="Sale", context=None):
    context = context or {}
    item_id = context.get("item_id", "")
    channel_id = context.get("channel_id", "")
    
    # Store channel_id or item_id in private_metadata
    # For edit, we use item_id. For add, we use channel_id.
    private_metadata = str(item_id) if item_id else channel_id

    return {
        "type": "modal",
        "callback_id": callback_id,
        "private_metadata": private_metadata,
        "title": {"type": "plain_text", "text": title},
        "submit": {"type": "plain_text", "text": "Submit"},
        "blocks": [
            {
                "type": "input",
                "block_id": "product_name_block",
                "element": {"type": "plain_text_input", "action_id": "product_name", "initial_value": context.get("product_name", "")},
                "label": {"type": "plain_text", "text": "Product Name"},
            },
            {
                "type": "input",
                "block_id": "price_block",
                "element": {"type": "plain_text_input", "action_id": "price", "initial_value": context.get("price", "")},
                "label": {"type": "plain_text", "text": "Price"},
            },
            {
                "type": "input",
                "block_id": "features_block",
                "element": {"type": "plain_text_input", "multiline": True, "action_id": "features", "initial_value": context.get("features", "")},
                "label": {"type": "plain_text", "text": "Features/Description"},
            },
            {
                "type": "input",
                "block_id": "type_block",
                "element": {
                    "type": "static_select",
                    "action_id": "post_type",
                    "initial_option": {
                        "text": {"type": "plain_text", "text": post_type},
                        "value": post_type
                    },
                    "options": [
                        {"text": {"type": "plain_text", "text": "Sale"}, "value": "Sale"},
                        {"text": {"type": "plain_text", "text": "Seeking"}, "value": "Seeking"},
                    ]
                },
                "label": {"type": "plain_text", "text": "Listing Type"},
            }
        ]
    }

def format_listing_blocks(item, owner_id):
    quote_box = ">>> " if item.post_type == "Sale" else "> "
    prefix = "📦 *NEW LISTING*" if item.post_type == "Sale" else "🔍 *SEEKING ITEM*"
    
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{prefix} from <@{owner_id}>:\n{quote_box}*Product*: {item.product_name}\n{quote_box}*Price*: {item.price}\n{quote_box}*Features*: {item.features}"
            }
        }
    ]

# --- Command Handlers ---

@app.command("/buyerbot")
def handle_command(ack, body, respond, command, client):
    ack()
    text = command["text"].strip()
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    trigger_id = body["trigger_id"]
    
    if not text:
        client.views_open(trigger_id=trigger_id, view=get_overview_modal(channel_id))
        return

    parts = text.split(" ", 1)
    subcommand = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if subcommand == "add":
        handle_add_listing(args, user_id, channel_id, trigger_id, client, respond, "Sale")
    elif subcommand == "seeking":
        handle_add_listing(args, user_id, channel_id, trigger_id, client, respond, "Seeking")
    elif subcommand in ["list", "manage"]:
        handle_list_user_items(user_id, respond)
    elif subcommand == "search":
        handle_search(args, channel_id, respond)
    elif subcommand == "help":
        respond("Usage:\n`/buyerbot add <description>`\n`/buyerbot seeking <description>`\n`/buyerbot list` (manage your items)\n`/buyerbot search <query>`")
    else:
        # Default to search if it doesn't look like a subcommand
        handle_search(text, channel_id, respond)

def handle_add_listing(text, user_id, channel_id, trigger_id, client, respond, post_type):
    if not text:
        client.views_open(
            trigger_id=trigger_id, 
            view=get_item_modal(f"Add {post_type}", "add_item_modal", post_type, {"channel_id": channel_id})
        )
        return

    # Try analysis
    items_analysis = llm.analyze_post(text, [])
    if not items_analysis:
        respond(f"I couldn't parse that {post_type} entry correctly. Try being more specific, or just use `/buyerbot {post_type.lower()}` to open the form.")
        return

    # Post to channel publicly
    for item_data in items_analysis:
        item_data["post_type"] = post_type
        # Explicitly ensure newly added items are "Available"
        item_data["status"] = "Available"
        
        # We need a dummy object to format
        from db import Item
        features_str = item_data.get("features", [])
        if isinstance(features_str, list):
            features_str = ", ".join(features_str)
            
        dummy_item = Item(
            product_name=item_data.get("product_name", "Unknown"), 
            price=str(item_data.get("price", "unknown")), 
            features=features_str,
            post_type=post_type,
            status="Available", # Required by model constructor
            post_id=0 # Temporary post_id for model constructor
        )
        
        text = f"New {post_type} listing: {dummy_item.product_name}"
        result = client.chat_postMessage(channel=channel_id, text=text, blocks=format_listing_blocks(dummy_item, user_id))
        ts = result["ts"]
        
        save_items_for_post(slack_ts=ts, channel_id=channel_id, user_id=user_id, items_data=[item_data], is_direct=True)
    
    respond(f"✅ Listing created in <#{channel_id}>!")

def get_user_listing_blocks(items):
    blocks = [{"type": "header", "text": {"type": "plain_text", "text": "My Listings"}}, {"type": "divider"}]
    
    for item in items:
        status_emoji = "✅" if item.status == "Available" else "💰" if item.status == "Sold" else "⚪"
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{status_emoji} *{item.product_name}* ({item.post_type}) - {item.price}\nStatus: _{item.status}_"},
            "accessory": {
                "type": "overflow",
                "action_id": "listing_overflow_action",
                "options": [
                    {"text": {"type": "plain_text", "text": "Mark Sold"}, "value": f"sold:{item.id}"},
                    {"text": {"type": "plain_text", "text": "Mark Obsolete"}, "value": f"obsolete:{item.id}"},
                    {"text": {"type": "plain_text", "text": "Edit"}, "value": f"edit:{item.id}"},
                    {"text": {"type": "plain_text", "text": "Delete"}, "value": f"delete:{item.id}"}
                ]
            }
        })
    return blocks

def handle_list_user_items(user_id, respond):
    items = get_user_items(user_id)
    if not items:
        respond("You don't have any listings yet. Use `/buyerbot add` to create one!")
        return

    blocks = get_user_listing_blocks(items)
    respond(blocks=blocks)

def handle_search(query, channel_id, respond):
    parsed = llm.parse_request(query)
    product = parsed.get("product", query)
    matches = search_items(product, channel_id)
    
    if not matches:
        respond(f"No active matches found for '{product}'.")
        return
        
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"Results for '{product}':"}},
        {"type": "divider"}
    ]
    
    for item in matches:
        seller_mention = f"<@{item.post.user_id}>" if item.post else "Unknown"
        is_direct_badge = " [Direct Listing]" if item.post and item.post.is_direct else ""
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Product*: {item.product_name}{is_direct_badge}\n"
                    f"*Type*: {item.post_type} | *Price*: {item.price}\n"
                    f"*User*: {seller_mention}\n"
                    f"*Features*: {item.features}"
                )
            }
        })
        
    respond(blocks=blocks)

# --- Action & View Handlers ---

@app.action("open_add_modal")
def action_handle_open_add(ack, body, client):
    ack()
    # If this came from a modal (overview), private_metadata might contain channel_id
    channel_id = body.get("view", {}).get("private_metadata", "")
    client.views_update(view_id=body["view"]["id"], view=get_item_modal("Add Listing", "add_item_modal", "Sale", {"channel_id": channel_id}))

@app.action("open_seeking_modal")
def action_handle_open_seeking(ack, body, client):
    ack()
    channel_id = body.get("view", {}).get("private_metadata", "")
    client.views_update(view_id=body["view"]["id"], view=get_item_modal("Seeking Item", "add_item_modal", "Seeking", {"channel_id": channel_id}))

@app.action("open_my_listings")
def action_open_my_listings(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    items = get_user_items(user_id)
    
    if not items:
        # Show a simple modal or push a message
        client.views_update(
            view_id=body["view"]["id"],
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "My Listings"},
                "close": {"type": "plain_text", "text": "Close"},
                "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "You don't have any listings yet. Use `/buyerbot add` to create one!"}}]
            }
        )
        return

    blocks = get_user_listing_blocks(items)
    client.views_update(
        view_id=body["view"]["id"],
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "My Listings"},
            "close": {"type": "plain_text", "text": "Close"},
            "blocks": blocks
        }
    )

@app.action("trigger_sync")
def action_trigger_sync(ack, body, client):
    ack()
    channel_id = body.get("view", {}).get("private_metadata", "")
    user_id = body["user"]["id"]
    
    if not channel_id:
         client.chat_postEphemeral(channel=user_id, user=user_id, text="Please use `/buyerbot sync` in a specific channel.")
         return

    client.views_update(
         view_id=body["view"]["id"],
         view={
             "type": "modal",
             "title": {"type": "plain_text", "text": "Syncing..."},
             "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "Channel sync has started. You can close this window; results will appear in the channel."}}],
             "close": {"type": "plain_text", "text": "Close"}
         }
    )
    
    sync_channel(app.client, channel_id, llm)
    client.chat_postEphemeral(channel=channel_id, user=user_id, text="Sync complete!")

@app.action("listing_overflow_action")
def handle_overflow(ack, body, respond, client):
    ack()
    user_id = body["user"]["id"]
    channel_id = body.get("view", {}).get("private_metadata", "") or body.get("channel", {}).get("id", "")
    
    selected_option = body["actions"][0]["selected_option"]["value"]
    action_type, item_id_str = selected_option.split(":")
    item_id = int(item_id_str)
    
    def safe_respond(msg):
        # If we have a response_url (respond works), use it.
        # Otherwise fall back to chat_postEphemeral.
        try:
            respond(msg)
        except ValueError:
            if channel_id:
                client.chat_postEphemeral(channel=channel_id, user=user_id, text=msg)
    
    if action_type == "sold":
        update_item_status(item_id, "Sold")
        safe_respond(f"Item marked as Sold.")
    elif action_type == "obsolete":
        update_item_status(item_id, "Obsolete")
        safe_respond(f"Item marked as Obsolete.")
    elif action_type == "delete":
        from db import Item, Session, engine
        with Session(engine) as session:
            item = session.get(Item, item_id)
            if item:
                delete_post(item.post_id)
                safe_respond("Listing deleted.")
    elif action_type == "edit":
        from db import Item, Session, engine
        with Session(engine) as session:
            item = session.get(Item, item_id)
            if item:
                initial_data = {
                    "item_id": item.id,
                    "product_name": item.product_name,
                    "price": item.price,
                    "features": item.features
                }
                if "view" in body:
                    client.views_update(
                        view_id=body["view"]["id"],
                        view=get_item_modal(f"Edit {item.product_name}", "edit_item_modal", item.post_type, initial_data)
                    )
                else:
                    client.views_open(
                        trigger_id=body["trigger_id"], 
                        view=get_item_modal(f"Edit {item.product_name}", "edit_item_modal", item.post_type, initial_data)
                    )

@app.view("add_item_modal")
def handle_add_item_submit(ack, body, client, view):
    ack()
    user_id = body["user"]["id"]
    channel_id = view.get("private_metadata", "")
    if not channel_id:
        # Fallback if no channel_id provided
        return

    values = view["state"]["values"]
    product_name = values["product_name_block"]["product_name"]["value"]
    price = values["price_block"]["price"]["value"]
    features = values["features_block"]["features"]["value"]
    post_type = values["type_block"]["post_type"]["selected_option"]["value"]
    
    # Save dummy item for formatting
    from db import Item
    dummy_item = Item(product_name=product_name, price=price, features=features, post_type=post_type)
    
    text = f"New {post_type} listing: {dummy_item.product_name}"
    result = client.chat_postMessage(channel=channel_id, text=text, blocks=format_listing_blocks(dummy_item, user_id))
    ts = result["ts"]
    
    save_items_for_post(
        slack_ts=ts, 
        channel_id=channel_id, 
        user_id=user_id, 
        items_data=[{
            "product_name": product_name,
            "price": price,
            "features": features,
            "status": "Available"
        }],
        is_direct=True
    )

@app.view("edit_item_modal")
def handle_edit_item_submit(ack, body, view):
    ack()
    item_id = int(view.get("private_metadata", "0"))
    if not item_id:
        return

    values = view["state"]["values"]
    product_name = values["product_name_block"]["product_name"]["value"]
    price = values["price_block"]["price"]["value"]
    features = values["features_block"]["features"]["value"]
    post_type = values["type_block"]["post_type"]["selected_option"]["value"]
    
    update_item_details(item_id, product_name, price, features, post_type)

@app.command("/buyerbot-sync")
def handle_sync(ack, respond, command):
    ack()
    channel_id = command["channel_id"]
    user_id = command["user_id"]
    log_basic(f"Received /buyerbot-sync command from {user_id} for channel {channel_id}")
    respond("Syncing channel history... this may take a moment.")
    try:
        sync_channel(app.client, channel_id, llm)
        respond("Sync complete!")
    except Exception as e:
        log_basic(f"Sync failed: {e}")
        respond(f"Sync failed: {e}")

if __name__ == "__main__":
    create_db_and_tables()
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()
