PARSE_REQUEST_PROMPT = """
Analyze this Slack command for a buy/sell bot: "{query}"
Extract the intent and the product the user is looking for.
Return as JSON with keys: "intent", "product".
"""

ANALYZE_POST_PROMPT = """
Analyze this Slack post and its replies for any buy/sell items mentioned.

Guidelines for Items:
- A "Sale" item is when someone is selling something (e.g., "Selling Macbook", "FS: iPhone").
- A "Seeking" item is when someone is looking to buy something (e.g., "WTB: iPad", "Anyone have a desk?").
- If a post is just casual conversation and does NOT mention any specific items for sale or being sought, return an empty list of items.

Guidelines for Status:
- Text wrapped in tildes (e.g., ~Macbook Pro~) is a strong indicator that the item is SOLD or NO LONGER AVAILABLE.
- Reactions like [Reactions: heavy_check_mark], [Reactions: white_check_mark], [Reactions: moneybag], or [Reactions: x] on the post or thread replies usually mean the deal is done (SOLD).
- If multiple items are listed, check if only specific ones have strikethrough formatting.

Post (with reactions): "{message_text}"
Replies (with reactions): "{thread_replies_text}"

Extract a list of items. For each item, extract:
- product_name (string)
- price (number or "unknown")
- features (list of strings)
- status (must be "Available", "Sold", or "Pending")
- post_type (must be exactly "Sale" or "Seeking")

Return as JSON with a key "items" which is a list of objects, each with the keys above.
"""
