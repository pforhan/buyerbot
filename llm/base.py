from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class LLMProvider(ABC):
    @abstractmethod
    def parse_request(self, query: str) -> Dict:
        """
        Extract intent and entities from user query.
        Example return: {"intent": "search", "product": "macbook"}
        """
        pass

    @abstractmethod
    def analyze_post(self, message_text: str, thread_replies: List[str]) -> List[Dict]:
        """
        Extract product, features, price, status, and post_type from a post.
        Returns a list of items found in the post. Returns an empty list if no items found.
        Example return: [{
            "product_name": "Macbook Pro 2021",
            "price": 1200,
            "features": ["16GB RAM", "512GB SSD"],
            "status": "Available",
            "post_type": "Sale"
        }]
        """
        pass
