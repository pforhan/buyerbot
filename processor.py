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
    
    for msg in messages:
        user_id = msg.get("user", "Unknown")
        
        # Ignore bots and subtype messages (like join/leave)
        # Also specifically ignore the bot's own user ID
        if msg.get("bot_id") or msg.get("subtype") or (bot_user_id and user_id == bot_user_id):
            continue
            
        ts = msg.get("ts")
        text = _get_text_with_reactions(msg)
        
        # Fetch thread replies if any
        replies = []
        if msg.get("thread_ts") or msg.get("reply_count", 0) > 0:
            reply_resp = client.conversations_replies(channel=channel_id, ts=ts)
            reply_msgs = reply_resp.get("messages", [])[1:] # Skip main post
            
            # Filter out bot replies
            for r in reply_msgs:
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
                slack_ts=ts,
                channel_id=channel_id,
                team_id=team_id,
                user_id=user_id,
                items_data=items_analysis
            )
            
    log_basic(f"Sync complete. Processed {msg_count} messages, found {item_count} items.")
