import json
import httpx
from typing import Dict, List
from .base import LLMProvider
from .prompts import PARSE_REQUEST_PROMPT, ANALYZE_POST_PROMPT
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
        prompt = PARSE_REQUEST_PROMPT.format(query=query)
        return self._call_ollama(prompt)

    def analyze_post(self, message_text: str, thread_replies: List[str]) -> List[Dict]:
        thread_replies_text = "\n".join(thread_replies)
        prompt = ANALYZE_POST_PROMPT.format(
            message_text=message_text,
            thread_replies_text=thread_replies_text
        )
        result = self._call_ollama(prompt)
        return result.get("items", [])
