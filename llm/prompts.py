PARSE_REQUEST_PROMPT = """
Analyze this Slack command for a buy/sell bot: "{query}"
Extract the intent and the product the user is looking for.
Return ONLY JSON with keys: "intent", "product". Do not include any other text or preamble.
"""

IS_LISTING_PROMPT = """
Does the following Slack post contain one or more items being offered for sale?
Answer "YES" if it is a listing for an item, even if it might already be sold.
Answer "NO" if it is just a question, a comment, or a general message.

Post: "{message_text}"
Replies: "{thread_replies_text}"

Respond with ONLY "YES" or "NO".
"""

ANALYZE_POST_PROMPT = """
Extract all items for sale from the Slack post and its replies.

Post: "{message_text}"
Replies: "{thread_replies_text}"

Fill in this structure:

{{
  "items": [
    {{
      "product_name": "",
      "price": "",
      "features": [],
      "status": ""
    }}
  ]
}}

Rules:
- A post may contain multiple items. Add each to the items list.
- price: number or "unknown".
- features: list of descriptive attributes.
- status:
    "Sold" if strikethrough (~like this~) OR reactions include heavy_check_mark, white_check_mark, moneybag, x.
    "Available" if no sold indicators.
- If no items, return {{ "items": [] }}.
- Output only the JSON. No explanations.
```

Do not add any explanation or extra text. Only return the JSON.
"""
