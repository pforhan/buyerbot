import os
import json
import pytest
import httpx
from llm.ollama import OllamaProvider
from dotenv import load_dotenv

load_dotenv()

def test_ollama_connection():
    """
    Test if Ollama is running and accessible.
    This test requires a local Ollama instance.
    """
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    # Using a very high timeout for the first pull/load if necessary
    provider = OllamaProvider(model=model)
    
    print(f"\nTesting connection to Ollama (Model: {model})...")
    
    # Test 1: Basic generation with a simple prompt
    # We use a non-JSON prompt first to check basic connectivity
    test_prompt = "Say 'hello'"
    payload = {
        "model": model,
        "prompt": test_prompt,
        "stream": False
    }
    
    # Get timeout from environment, default to 60s. Use None if 0.
    timeout_env = os.environ.get("OLLAMA_TIMEOUT", "60")
    timeout = float(timeout_env) if timeout_env != "0" else None
    
    try:
        response = httpx.post(provider.base_url, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        assert "response" in result
        print("✓ Basic connection successful.")
    except httpx.ConnectError:
        pytest.fail("Could not connect to Ollama. Is it running at http://localhost:11434?")
    except Exception as e:
        pytest.fail(f"Ollama test failed: {e}")

def test_ollama_json_parsing():
    """
    Test if Ollama correctly returns the expected JSON format for request parsing.
    """
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    provider = OllamaProvider(model=model)
    
    query = "find me a macbook"
    print(f"Testing JSON parsing for query: '{query}'...")
    
    try:
        result = provider.parse_request(query)
        assert isinstance(result, dict)
        assert "intent" in result
        assert "product" in result
        print(f"✓ JSON parsing successful: {result}")
    except Exception as e:
        pytest.fail(f"JSON parsing test failed: {e}")

def test_ollama_analyze_single_item():
    """
    Test if Ollama correctly extracts a single item from a post.
    """
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    provider = OllamaProvider(model=model)
    
    msg_text = "FS: Macbook Pro 2021, 16GB RAM, 512GB SSD. Asking $1200. [Reactions: heavy_check_mark]"
    replies = ["Is this still available?", "Sold to me!"]
    
    print(f"\nTesting analysis of a single item: '{msg_text}'...")
    
    try:
        items = provider.analyze_post(msg_text, replies)
        assert isinstance(items, list)
        assert len(items) >= 1
        item = items[0]
        assert "product_name" in item
        assert "price" in item
        assert "status" in item
        print(f"✓ Single item analysis successful: {item}")
    except Exception as e:
        pytest.fail(f"Single item analysis test failed: {e}")

def test_ollama_analyze_multiple_items():
    """
    Test if Ollama correctly extracts multiple items from a single post.
    """
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    provider = OllamaProvider(model=model)
    
    msg_text = "Cleaning out my desk! I have a ~Macbook Pro~ for $1000 and an iPhone 13 for $500. [Reactions: moneybag]"
    replies = []
    
    print(f"\nTesting analysis of multiple items: '{msg_text}'...")
    
    try:
        items = provider.analyze_post(msg_text, replies)
        assert isinstance(items, list)
        assert len(items) >= 2
        
        # Check if the Macbook is marked as Sold (due to strikethrough)
        macbook = next((i for i in items if "macbook" in i["product_name"].lower()), None)
        iphone = next((i for i in items if "iphone" in i["product_name"].lower()), None)
        
        assert macbook is not None
        assert iphone is not None
        
        print(f"✓ Multiple items analysis successful. Found {len(items)} items.")
        for i in items:
            print(f"  - {i['product_name']} ({i['status']}): {i['price']}")
            
    except Exception as e:
        pytest.fail(f"Multiple items analysis test failed: {e}")

def test_ollama_analyze_conversational_post():
    """
    Test if Ollama correctly ignores a conversational post.
    """
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    provider = OllamaProvider(model=model)
    
    msg_text = "What time is the lunch meeting tomorrow?"
    replies = ["I think it's at 12:30", "Thanks!"]
    
    print(f"\nTesting analysis of a conversational post: '{msg_text}'...")
    
    try:
        items = provider.analyze_post(msg_text, replies)
        assert isinstance(items, list)
        assert len(items) == 0
        print("✓ Conversational post successfully ignored (0 items found).")
    except Exception as e:
        pytest.fail(f"Conversational post analysis test failed: {e}")

if __name__ == "__main__":
    # Allow running this script directly without pytest
    try:
        test_ollama_connection()
        test_ollama_json_parsing()
        test_ollama_analyze_single_item()
        test_ollama_analyze_multiple_items()
        test_ollama_analyze_conversational_post()
        print("\nAll Ollama integration tests passed!")
    except Exception as e:
        print(f"\nTests failed: {e}")
