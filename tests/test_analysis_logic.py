import pytest
from llm.mock import MockProvider

def test_mock_analyze_sale_item():
    provider = MockProvider()
    msg_text = "FS: Macbook Pro 2021, $1200."
    items = provider.analyze_post(msg_text, [])
    
    assert len(items) == 1
    assert items[0]["product_name"] == "Macbook"
    assert items[0]["status"] == "Available"

def test_mock_analyze_conversational_post():
    provider = MockProvider()
    msg_text = "Hey guys, when is the next meetup?"
    items = provider.analyze_post(msg_text, [])
    
    # Conversations should return an empty list
    assert isinstance(items, list)
    assert len(items) == 0

def test_mock_analyze_multiple_items():
    provider = MockProvider()
    msg_text = "Selling iPhone and a Macbook."
    
    items = provider.analyze_post(msg_text, [])
    
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
