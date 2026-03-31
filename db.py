from typing import List, Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select
import time

class SlackPost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slack_ts: str = Field(index=True, unique=True)
    channel_id: str
    product_name: str
    price: str
    status: str
    features: str  # Stored as comma-separated or JSON string for simplicity here
    last_updated: float = Field(default_factory=time.time)

sqlite_file_name = "buyerbot.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def save_post(post_data: SlackPost):
    with Session(engine) as session:
        # Check if already exists
        statement = select(SlackPost).where(SlackPost.slack_ts == post_data.slack_ts)
        existing = session.exec(statement).first()
        if existing:
            # Update existing
            existing.product_name = post_data.product_name
            existing.price = post_data.price
            existing.status = post_data.status
            existing.features = post_data.features
            existing.last_updated = time.time()
            session.add(existing)
        else:
            session.add(post_data)
        session.commit()

def search_posts(product_query: str) -> List[SlackPost]:
    with Session(engine) as session:
        statement = select(SlackPost).where(SlackPost.product_name.contains(product_query))
        return list(session.exec(statement).all())
