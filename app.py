import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from llm import MockProvider, OllamaProvider
from db import create_db_and_tables, search_posts
from processor import sync_channel

load_dotenv()

# Initialize Slack App
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Select LLM Provider
provider_type = os.environ.get("LLM_PROVIDER", "mock").lower()

if provider_type == "ollama":
    llm = OllamaProvider(model=os.environ.get("OLLAMA_MODEL", "llama3"))
else:
    llm = MockProvider()

@app.command("/buyerbot")
def handle_command(ack, respond, command):
    ack()
    
    query_text = command["text"]
    channel_id = command["channel_id"]
    
    # Optional: Sync before searching? Or keep a separate sync command.
    # For now, let's just search.
    respond(f"Searching for items related to: {query_text}...")
    
    # 1. Parse request with LLM
    parsed = llm.parse_request(query_text)
    product = parsed.get("product", query_text) # Fallback to original text
    
    # 2. Search DB
    matches = search_posts(product)
    
    if not matches:
        respond("No matches found in the history.")
        return
        
    # 3. Format response
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Found {len(matches)} matches for '{product}':"
            }
        },
        {"type": "divider"}
    ]
    
    for post in matches:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Product*: {post.product_name}\n*Price*: {post.price}\n*Status*: {post.status}\n*Features*: {post.features}"
            }
        })
        
    respond(blocks=blocks)

@app.command("/buyerbot-sync")
def handle_sync(ack, respond, command):
    ack()
    channel_id = command["channel_id"]
    respond("Syncing channel history... this may take a moment.")
    
    try:
        sync_channel(app.client, channel_id, llm)
        respond("Sync complete!")
    except Exception as e:
        respond(f"Sync failed: {e}")

if __name__ == "__main__":
    # Create DB tables
    create_db_and_tables()
    
    # Start Socket Mode
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()
