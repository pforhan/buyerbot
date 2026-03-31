PARSE_REQUEST_PROMPT = """
Analyze this Slack command for a buy/sell bot: "{query}"
Extract the intent and the product the user is looking for.
Return as JSON with keys: "intent", "product".
"""

ANALYZE_POST_PROMPT = """
Analyze this Slack post and its replies for any buy/sell items mentioned.

Guidelines for Status:
- Text wrapped in tildes (e.g., ~Macbook Pro~) is a strong indicator that the item is SOLD or NO LONGER AVAILABLE.
- Reactions like [Reactions: heavy_check_mark], [Reactions: white_check_mark], [Reactions: moneybag], or [Reactions: x] on the post or thread replies usually mean the deal is done (SOLD).
- If multiple items are listed, check if only specific ones have strikethrough formatting.

Post (with reactions): "{message_text}"
Replies (with reactions): "{thread_replies_text}"

Extract a list of items. For each item, extract product name, price (number or "unknown"), 
features (list), and status (Available, Sold, or Pending).

Return as JSON with a key "items" which is a list of objects, each with keys: 
"product_name", "price", "features", "status".
"""
