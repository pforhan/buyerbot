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
        status = "Available"
        if "sold" in text or any("sold" in r.lower() for r in thread_replies):
            status = "Sold"
        
        # Simple extraction
        items = []
        if "macbook" in text:
            items.append({
                "product_name": "Macbook",
                "price": "Check post",
                "features": [],
                "status": status,
            })
        if "iphone" in text:
            items.append({
                "product_name": "iPhone",
                "price": "Check post",
                "features": [],
                "status": status,
            })
            
        if not items:
            items.append({
                "product_name": "Unknown Product",
                "price": "Check post",
                "features": [],
                "status": status,
            })

        return items
