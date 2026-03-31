import json
import httpx
from typing import Dict, List
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = f"{base_url}/api/generate"

    def _call_ollama(self, prompt: str) -> Dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        try:
            response = httpx.post(self.base_url, json=payload, timeout=30.0)
            response.raise_for_status()
            return json.loads(response.json()["response"])
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

    def analyze_post(self, message_text: str, thread_replies: List[str]) -> Dict:
        replies_text = "\n".join(thread_replies)
        prompt = f"""
        Analyze this Slack post and its replies for a buy/sell item.
        Post: "{message_text}"
        Replies: "{replies_text}"
        
        Extract product name, price (number or "unknown"), features (list), and status (Available, Sold, or Pending).
        Return as JSON with keys: "product_name", "price", "features", "status".
        """
        return self._call_ollama(prompt)
