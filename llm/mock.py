from typing import Dict, List
from .base import LLMProvider

class MockProvider(LLMProvider):
    def parse_request(self, query: str) -> Dict:
        # Very simple mock parsing
        query = query.lower()
        product = "unknown"
        if "macbook" in query:
            product = "macbook"
        elif "iphone" in query:
            product = "iphone"
            
        return {
            "intent": "search",
            "product": product,
            "raw_query": query
        }

    def analyze_post(self, message_text: str, thread_replies: List[str]) -> List[Dict]:
        # Mock analysis
        text = message_text.lower()
        all_text = (text + " " + " ".join(r.lower() for r in thread_replies))
        
        status = "Available"
        post_type = "Sale"
        
        # Check for Seeking: "wtb", "looking for", "anyone have"
        if any(keyword in text for keyword in ["wtb", "looking for", "anyone have", "want to buy"]):
            post_type = "Seeking"
        
        # Check for "sold" indicators: "sold" keyword, strikethrough ~, or checkmark reaction
        if (
            "sold" in all_text or 
            "~" in message_text or 
            "heavy_check_mark" in all_text or 
            "white_check_mark" in all_text or
            "moneybag" in all_text
        ):
            if post_type == "Sale":
                status = "Sold"
            else:
                status = "Fulfilled" # Or just keep Pending/Available
        
        # Simple extraction
        items = []
        if "macbook" in text:
            items.append({
                "product_name": "Macbook",
                "price": "Check post",
                "features": [],
                "status": status,
                "post_type": post_type
            })
        if "iphone" in text:
            items.append({
                "product_name": "iPhone",
                "price": "Check post",
                "features": [],
                "status": status,
                "post_type": post_type
            })
            
        return items
