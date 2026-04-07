from typing import List, Dict
from slack_sdk import WebClient
from llm import LLMProvider
from db import save_items_for_post
from logger import log_basic

def _get_text_with_reactions(msg: Dict) -> str:
    text = msg.get("text", "")
    reactions = msg.get("reactions", [])
    if reactions:
        reaction_names = [r.get("name") for r in reactions]
        text += f" [Reactions: {', '.join(reaction_names)}]"
    return text

def sync_channel(client: WebClient, channel_id: str, team_id: str, llm: LLMProvider):
    """
    Fetch history from a channel and analyze posts.
    """
    log_basic(f"Starting sync for channel: {channel_id} (team: {team_id})")
    
    # Get the bot's own user ID to ignore its posts
    bot_user_id = None
    try:
        auth_resp = client.auth_test()
        bot_user_id = auth_resp.get("user_id")
    except Exception as e:
        log_basic(f"Warning: Could not fetch bot user ID: {e}")

    response = client.conversations_history(channel=channel_id, limit=50)
    messages = response.get("messages", [])
    
    msg_count = 0
    item_count = 0
    processed_threads = set()
    
    for msg in messages:
        user_id = msg.get("user", "Unknown")
        
        # Ignore bots and subtype messages (like join/leave)
        # Also specifically ignore the bot's own user ID
        if msg.get("bot_id") or msg.get("subtype") or (bot_user_id and user_id == bot_user_id):
            continue
            
        ts = msg.get("ts")
        thread_ts = msg.get("thread_ts")
        
        # Determine the root of the thread to avoid duplicate processing
        root_ts = thread_ts if thread_ts else ts
        if root_ts in processed_threads:
            continue
        processed_threads.add(root_ts)

        # Fetch the full thread (or just the single message if not a thread)
        # conversations_replies returns the root message as the first element
        if thread_ts or msg.get("reply_count", 0) > 0:
            reply_resp = client.conversations_replies(channel=channel_id, ts=root_ts)
            thread_messages = reply_resp.get("messages", [])
        else:
            thread_messages = [msg]

        if not thread_messages:
            continue

        root_msg = thread_messages[0]
        root_user_id = root_msg.get("user", "Unknown")
        
        # Re-check bot status for the root message if we started from a reply
        if root_msg.get("bot_id") or (bot_user_id and root_user_id == bot_user_id):
            continue

        text = _get_text_with_reactions(root_msg)
        replies = []
        
        for r in thread_messages[1:]:
            r_user = r.get("user")
            if r.get("bot_id") or (bot_user_id and r_user == bot_user_id):
                continue
            replies.append(_get_text_with_reactions(r))
            
        # Analyze with LLM (returns a list of items)
        items_analysis = llm.analyze_post(text, replies)
        
        # Save to DB
        if items_analysis:
            msg_count += 1
            item_count += len(items_analysis)
            save_items_for_post(
                slack_ts=root_ts,
                channel_id=channel_id,
                team_id=team_id,
                user_id=root_user_id,
                items_data=items_analysis
            )
            
    log_basic(f"Sync complete. Processed {msg_count} messages, found {item_count} items.")
    return msg_count, item_count
