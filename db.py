from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship, create_engine, Session, select
import time

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slack_ts: str = Field(index=True, unique=True)
    channel_id: str = Field(index=True)
    user_id: str
    last_updated: float = Field(default_factory=time.time)
    
    items: List["Item"] = Relationship(back_populates="post")

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id")
    product_name: str
    price: str
    status: str
    features: str
    
    post: Post = Relationship(back_populates="items")

sqlite_file_name = "buyerbot.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def save_items_for_post(slack_ts: str, channel_id: str, user_id: str, items_data: List[dict]):
    with Session(engine) as session:
        # Check if post already exists
        statement = select(Post).where(Post.slack_ts == slack_ts)
        post = session.exec(statement).first()
        
        if post:
            # Update existing post user/channel just in case
            post.user_id = user_id
            post.channel_id = channel_id
            post.last_updated = time.time()
            
            # For simplicity in this update, we'll clear existing items for this post and re-add
            # A more surgical update could match by product name if needed
            for existing_item in post.items:
                session.delete(existing_item)
            post.items = []
        else:
            post = Post(slack_ts=slack_ts, channel_id=channel_id, user_id=user_id)
            session.add(post)
            session.flush() # Get the post.id
        
        for item_data in items_data:
            item = Item(
                post_id=post.id,
                product_name=item_data.get("product_name", "Unknown"),
                price=str(item_data.get("price", "unknown")),
                status=item_data.get("status", "Available"),
                features=", ".join(item_data.get("features", [])) if isinstance(item_data.get("features"), list) else str(item_data.get("features", ""))
            )
            session.add(item)
            
        session.commit()

def search_items(product_query: str, channel_id: str) -> List[Item]:
    with Session(engine) as session:
        statement = (
            select(Item)
            .join(Post)
            .where(Post.channel_id == channel_id)
            .where(Item.product_name.contains(product_query))
        )
        return list(session.exec(statement).all())
