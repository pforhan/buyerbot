import json
import httpx
from typing import Dict, List
from .base import LLMProvider
from logger import log_full

class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = f"{base_url}/api/generate"

    def _call_ollama(self, prompt: str) -> Dict:
        log_full(f"Ollama Prompt: {prompt}")
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        try:
            response = httpx.post(self.base_url, json=payload, timeout=30.0)
            response.raise_for_status()
            raw_response = response.json()["response"]
            log_full(f"Ollama Raw Response: {raw_response}")
            return json.loads(raw_response)
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return {}

    def parse_request(self, query: str) -> Dict:
        prompt = f"""
        Analyze this Slack command for a buy/sell bot: "{query}"
        Extract the intent and the product the user is looking for.
        Return as JSON with keys: "intent", "product".
        """
        return self._call_ollama(prompt)

    def analyze_post(self, message_text: str, thread_replies: List[str]) -> List[Dict]:
        replies_text = "\n".join(thread_replies)
        prompt = f"""
        Analyze this Slack post and its replies for any buy/sell items mentioned.
        A single post may contain multiple items for sale.
        
        Post: "{message_text}"
        Replies: "{replies_text}"
        
        Extract a list of items. For each item, extract product name, price (number or "unknown"), 
        features (list), and status (Available, Sold, or Pending).
        
        Return as JSON with a key "items" which is a list of objects, each with keys: 
        "product_name", "price", "features", "status".
        """
        result = self._call_ollama(prompt)
        return result.get("items", [])
