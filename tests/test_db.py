import pytest
from sqlmodel import Session, select, create_engine, SQLModel
from db import Post, Item, save_items_for_post, search_items
import time

# Use a memory-based SQLite for testing
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_search_items_segmentation(monkeypatch):
    # Setup - use an in-memory database
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    # Import 'db' to mock its engine
    import db
    monkeypatch.setattr(db, "engine", engine)

    # 1. Save items in channel A
    save_items_for_post(
        slack_ts="ts1", 
        channel_id="C_ALFA", 
        team_id="T123",
        user_id="U_ALFA", 
        items_data=[{"product_name": "Macbook", "price": 1000, "status": "Available"}]
    )
    
    # 2. Save items in channel B with same product name
    save_items_for_post(
        slack_ts="ts2", 
        channel_id="C_BRAVO", 
        team_id="T123",
        user_id="U_BRAVO", 
        items_data=[{"product_name": "Macbook", "price": 2000, "status": "Available"}]
    )

    # 3. Search in channel A
    results_a = search_items("Macbook", "C_ALFA", "T123")
    assert len(results_a) == 1
    assert results_a[0].product_name == "Macbook"
    assert results_a[0].price == "1000"
    
    # 4. Search in channel B
    results_b = search_items("Macbook", "C_BRAVO", "T123")
    assert len(results_b) == 1
    assert results_b[0].product_name == "Macbook"
    assert results_b[0].price == "2000"
    
    # 5. Search for something non-existent in channel A
    results_none = search_items("iPhone", "C_ALFA", "T123")
    assert len(results_none) == 0
