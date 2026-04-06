PARSE_REQUEST_PROMPT = """
Analyze this Slack command for a buy/sell bot: "{query}"
Extract the intent and the product the user is looking for.
Return ONLY JSON with keys: "intent", "product". Do not include any other text or preamble.
"""

IS_LISTING_PROMPT = """
Does the following Slack post offer items for sale?
Answer "YES" if the post clearly indicates items are being offered for sale by:
- Stating "for sale", "selling", "offering", or similar phrases.
- Listing specific items with prices.
- Listing specific items with an explicit offer to negotiate or a request for offers (e.g., "make offer", "best offer").

Answer "NO" if the post is primarily:
- A question or general comment.
- A general announcement, project update, or link to a resource.
- A user mention.
- A request to buy or an inquiry about availability, without offering items.

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
- price: number or "make offer" or "unknown".
- features: list of descriptive attributes.
- status:
    "Sold" if strikethrough (~like this~) OR reactions include heavy_check_mark, white_check_mark, moneybag, x.
    "Available" if no sold indicators.
- If no items, return {{ "items": [] }}.
- Output only the JSON. No explanations.
```

Do not add any explanation or extra text. Only return the JSON.
"""
