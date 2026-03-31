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

    def analyze_post(self, message_text: str, thread_replies: List[str]) -> Dict:
        # Mock analysis
        text = message_text.lower()
        status = "Available"
        if "sold" in text or any("sold" in r.lower() for r in thread_replies):
            status = "Sold"
        
        # Simple extraction
        product = "Unknown Product"
        if "macbook" in text:
            product = "Macbook"
        elif "iphone" in text:
            product = "iPhone"

        return {
            "product_name": product,
            "price": "Check post",
            "features": [],
            "status": status,
            "raw_text": message_text
        }
