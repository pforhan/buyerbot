import pytest
from sqlmodel import Session, select, create_engine, SQLModel
from db import Post, Item, save_items_for_post, search_items, get_user_items, update_item_status, create_db_and_tables
import db

@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(db, "engine", engine)

def test_direct_listing_creation():
    # Setup: Create a direct listing
    ts = "direct_123"
    channel_id = "C123"
    team_id = "T123"
    user_id = "U123"
    items_data = [{
        "product_name": "Test Item",
        "price": "100",
        "features": ["Feature A"],
        "status": "Available"
    }]
    
    post = save_items_for_post(ts, channel_id, team_id, user_id, items_data, is_direct=True)
    assert post.is_direct is True
    assert post.slack_ts == ts

    # Verify search prioritization
    # Create a non-direct listing with a newer timestamp but similar name
    save_items_for_post("parsed_456", channel_id, team_id, "U456", [{
        "product_name": "Test Item Parsed",
        "price": "50",
        "status": "Available"
    }], is_direct=False)
    
    results = search_items("Test", channel_id, team_id)
    assert len(results) >= 2
    # The direct listing should be first
    assert results[0].post.is_direct is True
    assert "Test Item" == results[0].product_name

def test_status_filtering():
    channel_id = "C_FILTER"
    team_id = "T123"
    save_items_for_post("ts_sold", channel_id, team_id, "U1", [{
        "product_name": "Sold Item",
        "price": "10",
        "status": "Sold"
    }], is_direct=True)
    
    save_items_for_post("ts_avail", channel_id, team_id, "U1", [{
        "product_name": "Available Item",
        "price": "20",
        "status": "Available"
    }], is_direct=True)
    
    results = search_items("Item", channel_id, team_id)
    # Should only find the available one
    assert len(results) == 1
    assert results[0].product_name == "Available Item"

def test_get_user_items():
    user_id = "U_MANAGE"
    team_id = "T123"
    save_items_for_post("ts_m1", "C1", team_id, user_id, [{"product_name": "My Item"}], is_direct=True)
    
    items = get_user_items(user_id, team_id)
    assert len(items) == 1
    assert items[0].product_name == "My Item"
