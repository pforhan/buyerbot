from typing import List
from slack_sdk import WebClient
from llm import LLMProvider
from db import save_items_for_post
from logger import log_basic

def sync_channel(client: WebClient, channel_id: str, llm: LLMProvider):
    """
    Fetch history from a channel and analyze posts.
    """
    log_basic(f"Starting sync for channel: {channel_id}")
    response = client.conversations_history(channel=channel_id, limit=50)
    messages = response.get("messages", [])
    
    msg_count = 0
    item_count = 0
    
    for msg in messages:
        # Ignore bots and subtype messages (like join/leave)
        if msg.get("bot_id") or msg.get("subtype"):
            continue
            
        ts = msg.get("ts")
        text = msg.get("text", "")
        user_id = msg.get("user", "Unknown")
        
        # Fetch thread replies if any
        replies = []
        if msg.get("thread_ts") or msg.get("reply_count", 0) > 0:
            reply_resp = client.conversations_replies(channel=channel_id, ts=ts)
            replies = [r.get("text", "") for r in reply_resp.get("messages", [])[1:]] # Skip main post
            
        # Analyze with LLM (returns a list of items)
        items_analysis = llm.analyze_post(text, replies)
        
        # Save to DB
        if items_analysis:
            msg_count += 1
            item_count += len(items_analysis)
            save_items_for_post(
                slack_ts=ts,
                channel_id=channel_id,
                user_id=user_id,
                items_data=items_analysis
            )
            
    log_basic(f"Sync complete. Processed {msg_count} messages, found {item_count} items.")
