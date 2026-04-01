import pytest
from llm.mock import MockProvider

def test_mock_analyze_sale_item():
    provider = MockProvider()
    msg_text = "FS: Macbook Pro 2021, $1200."
    items = provider.analyze_post(msg_text, [])
    
    assert len(items) == 1
    assert items[0]["product_name"] == "Macbook"
    assert items[0]["post_type"] == "Sale"
    assert items[0]["status"] == "Available"

def test_mock_analyze_seeking_item():
    provider = MockProvider()
    msg_text = "WTB: Macbook Pro 2021."
    items = provider.analyze_post(msg_text, [])
    
    assert len(items) == 1
    assert items[0]["product_name"] == "Macbook"
    assert items[0]["post_type"] == "Seeking"

def test_mock_analyze_conversational_post():
    provider = MockProvider()
    msg_text = "Hey guys, when is the next meetup?"
    items = provider.analyze_post(msg_text, [])
    
    # Conversations should return an empty list
    assert isinstance(items, list)
    assert len(items) == 0

def test_mock_analyze_multiple_types():
    provider = MockProvider()
    msg_text = "Selling iPhone, but looking for a Macbook."
    # Our mock is simple, it'll probably mark both with the same type if it checks the whole text.
    # But let's check how it behaves.
    
    # Wait, my mock check for post_type was:
    # if any(keyword in text for keyword in ["wtb", "looking for", "anyone have", "want to buy"]):
    #     post_type = "Seeking"
    
    items = provider.analyze_post(msg_text, [])
    # In this case, "looking for" is present, so it might mark both as Seeking.
    # Real LLM would handle this better. 
    # For the mock, just checking it returns SOMETHING for both.
    
    assert len(items) == 2
    products = [i["product_name"] for i in items]
    assert "iPhone" in products
    assert "Macbook" in products

def test_mock_sold_status():
    provider = MockProvider()
    msg_text = "~Macbook Pro 2021~"
    items = provider.analyze_post(msg_text, [])
    
    assert len(items) == 1
    assert items[0]["status"] == "Sold"
