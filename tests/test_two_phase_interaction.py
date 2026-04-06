import pytest
from unittest.mock import MagicMock, patch
from llm.ollama import OllamaProvider

def test_ollama_two_phase_calls():
    """
    Verify that OllamaProvider calls is_listing first and skips extraction if it returns False.
    """
    provider = OllamaProvider()
    
    # Mock _call_ollama
    # First call (is_listing) returns NO
    provider._call_ollama = MagicMock(return_value={"raw": "NO"})
    
    items = provider.analyze_post("This is just chatter", [])
    
    # Should have called _call_ollama once for is_listing
    assert provider._call_ollama.call_count == 1
    assert items == []
    
    # Second call (is_listing) returns YES
    provider._call_ollama.reset_mock()
    
    # Mock return values for two calls: 
    # 1. is_listing (YES)
    # 2. analyze_post (JSON result)
    provider._call_ollama.side_effect = [
        {"raw": "YES"},
        {"items": [{"product_name": "Macbook", "price": 1000, "status": "Available"}]}
    ]
    
    items = provider.analyze_post("FS: Macbook $1000", [])
    
    # Should have called _call_ollama twice
    assert provider._call_ollama.call_count == 2
    assert len(items) == 1
    assert items[0]["product_name"] == "Macbook"

def test_ollama_two_phase_case_insensitivity():
    """
    Verify that YES/NO detection is case-insensitive.
    """
    provider = OllamaProvider()
    
    # Mock returns "yes" (lowercase)
    provider._call_ollama = MagicMock(side_effect=[
        {"raw": "yes"},
        {"items": [{"product_name": "iPhone", "price": 500, "status": "Available"}]}
    ])
    
    items = provider.analyze_post("iPhone $500", [])
    assert len(items) == 1
    assert provider._call_ollama.call_count == 2
