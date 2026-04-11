import pytest
from sqlmodel import Session, create_engine, SQLModel
from db import save_items_for_post, search_items, Item
import db

def test_search_by_tags_and_category(monkeypatch):
    # Setup - use an in-memory database
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(db, "engine", engine)

    # 1. Save item with specific category and tags
    save_items_for_post(
        slack_ts="ts1", 
        channel_id="C1", 
        team_id="T1",
        user_id="U1", 
        items_data=[{
            "product_name": "Ultra Book", 
            "price": "1000", 
            "status": "Available",
            "category": "Computers",
            "tags": ["laptop", "slim", "silver"]
        }]
    )
    
    # 2. Search by category
    results_cat = search_items("Computers", "C1", "T1")
    assert len(results_cat) == 1
    assert results_cat[0].product_name == "Ultra Book"
    
    # 3. Search by tag
    results_tag = search_items("slim", "C1", "T1")
    assert len(results_tag) == 1
    assert results_tag[0].product_name == "Ultra Book"
    
    # 4. Search by partial tag
    results_partial = search_items("silv", "C1", "T1")
    assert len(results_partial) == 1
    assert results_partial[0].product_name == "Ultra Book"

    # 5. Search by product name (still works)
    results_name = search_items("Ultra", "C1", "T1")
    assert len(results_name) == 1
    assert results_name[0].product_name == "Ultra Book"

def test_mock_provider_tags():
    from llm.mock import MockProvider
    provider = MockProvider()
    items = provider.analyze_post("FS: Macbook", [])
    
    assert len(items) == 1
    assert items[0]["category"] == "Electronics"
    assert "Apple" in items[0]["tags"]
