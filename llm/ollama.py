import os
import json
import httpx
from typing import Dict, List
from .base import LLMProvider
from .prompts import PARSE_REQUEST_PROMPT, ANALYZE_POST_PROMPT, IS_LISTING_PROMPT
from logger import log_full

class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = f"{base_url}/api/generate"

    def _call_ollama(self, prompt: str, is_json: bool = True) -> Dict:
        log_full(f"Ollama Prompt: {prompt}")
        
        # Get timeout from environment, default to 60s. Use None if 0.
        timeout_env = os.environ.get("OLLAMA_TIMEOUT", "60")
        timeout = float(timeout_env) if timeout_env != "0" else None
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if is_json:
            payload["format"] = "json"
            
        try:
            response = httpx.post(self.base_url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            # Handle standard Ollama 'response' or models using 'thinking' field (like Qwen-VL)
            raw_content = data.get("response", "")
            if not raw_content and "thinking" in data:
                raw_content = data.get("thinking", "")
            
            log_full(f"Ollama Raw Content: {raw_content}")
            
            if not is_json:
                return {"raw": raw_content.strip()}
            
            # Try to handle Markdown or prefix/suffix text
            processed_content = raw_content.strip()
            
            # Find the first { or [ and last } or ]
            start_idx = processed_content.find('{')
            if start_idx == -1:
                start_idx = processed_content.find('[')
            
            end_idx = processed_content.rfind('}')
            if end_idx == -1:
                end_idx = processed_content.rfind(']')
                
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_part = processed_content[start_idx:end_idx+1]
                try:
                    return json.loads(json_part)
                except json.JSONDecodeError:
                    log_full(f"Ollama JSON extraction failed on snippet: {json_part}")
            
            # Fallback to direct parse
            return json.loads(raw_content)
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            if 'response' in locals():
                log_full(f"DEBUG: Raw response content: {response.text}")
            return {}

    def parse_request(self, query: str) -> Dict:
        prompt = PARSE_REQUEST_PROMPT.format(query=query)
        return self._call_ollama(prompt)

    def is_listing(self, message_text: str, thread_replies: List[str]) -> bool:
        thread_replies_text = "\n".join(thread_replies)
        prompt = IS_LISTING_PROMPT.format(
            message_text=message_text,
            thread_replies_text=thread_replies_text
        )
        result = self._call_ollama(prompt, is_json=False)
        raw_response = result.get("raw", "").upper()
        return "YES" in raw_response

    def analyze_post(self, message_text: str, thread_replies: List[str]) -> List[Dict]:
        # Phase 1: Detection
        if not self.is_listing(message_text, thread_replies):
            return []
            
        # Phase 2: Extraction
        thread_replies_text = "\n".join(thread_replies)
        prompt = ANALYZE_POST_PROMPT.format(
            message_text=message_text,
            thread_replies_text=thread_replies_text
        )
        result = self._call_ollama(prompt)
        if isinstance(result, list):
            return result
        return result.get("items", [])
