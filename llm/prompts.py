PARSE_REQUEST_PROMPT = """
Analyze this Slack command for a buy/sell bot: "{query}"
Extract the intent and the product the user is looking for.
Return ONLY JSON with keys: "intent", "product". Do not include any other text or preamble.
"""

ANALYZE_POST_PROMPT = """
Extract all items for sale from the Slack post and its replies.

Post: "{message_text}"
Replies: "{thread_replies_text}"

Return ONLY this JSON format:

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
- A post may contain multiple items. Extract each separately into the items list.
- price: number or "unknown".
- features: list of descriptive attributes.
- status:
    "Sold" if strikethrough (~like this~) OR reactions include heavy_check_mark, white_check_mark, moneybag, x.
    "Available" if no sold indicators.
    "Pending" only if explicitly stated.
- If no items, return {{ "items": [] }}.
- Output only the JSON. No explanations.
```

Do not add any explanation or extra text. Only return the JSON.
"""
