from typing import List
from slack_sdk import WebClient
from llm import LLMProvider
from db import SlackPost, save_post

def sync_channel(client: WebClient, channel_id: str, llm: LLMProvider):
    """
    Fetch history from a channel and analyze posts.
    """
    response = client.conversations_history(channel=channel_id, limit=50)
    messages = response.get("messages", [])
    
    for msg in messages:
        # Ignore bots and subtype messages (like join/leave)
        if msg.get("bot_id") or msg.get("subtype"):
            continue
            
        ts = msg.get("ts")
        text = msg.get("text", "")
        
        # Fetch thread replies if any
        replies = []
        if msg.get("thread_ts") or msg.get("reply_count", 0) > 0:
            reply_resp = client.conversations_replies(channel=channel_id, ts=ts)
            replies = [r.get("text", "") for r in reply_resp.get("messages", [])[1:]] # Skip main post
            
        # Analyze with LLM
        analysis = llm.analyze_post(text, replies)
        
        # Save to DB
        if analysis:
            post = SlackPost(
                slack_ts=ts,
                channel_id=channel_id,
                product_name=analysis.get("product_name", "Unknown"),
                price=str(analysis.get("price", "unknown")),
                status=analysis.get("status", "Available"),
                features=", ".join(analysis.get("features", []))
            )
            save_post(post)
