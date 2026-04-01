from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship, create_engine, Session, select
from sqlalchemy.orm import selectinload
import time

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slack_ts: str = Field(index=True, unique=True)
    channel_id: str = Field(index=True)
    user_id: str
    last_updated: float = Field(default_factory=time.time)
    is_direct: bool = Field(default=False)
    
    items: List["Item"] = Relationship(back_populates="post")

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id")
    product_name: str
    price: str
    status: str
    features: str
    post_type: str = Field(default="Sale") # "Sale" or "Seeking"
    
    post: Post = Relationship(back_populates="items")

sqlite_file_name = "buyerbot.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def save_items_for_post(slack_ts: str, channel_id: str, user_id: str, items_data: List[dict], is_direct: bool = False):
    with Session(engine) as session:
        # Check if post already exists
        statement = select(Post).where(Post.slack_ts == slack_ts)
        post = session.exec(statement).first()
        
        if post:
            # Update existing post user/channel just in case
            post.user_id = user_id
            post.channel_id = channel_id
            post.last_updated = time.time()
            post.is_direct = is_direct
            
            # For simplicity in this update, we'll clear existing items for this post and re-add
            for existing_item in post.items:
                session.delete(existing_item)
            post.items = []
        else:
            post = Post(slack_ts=slack_ts, channel_id=channel_id, user_id=user_id, is_direct=is_direct)
            session.add(post)
            session.flush() # Get the post.id
        
        for item_data in items_data:
            item = Item(
                post_id=post.id,
                product_name=item_data.get("product_name", "Unknown"),
                price=str(item_data.get("price", "unknown")),
                status=item_data.get("status", "Available"),
                features=", ".join(item_data.get("features", [])) if isinstance(item_data.get("features"), list) else str(item_data.get("features", "")),
                post_type=item_data.get("post_type", "Sale")
            )
            session.add(item)
            
        session.commit()
        session.refresh(post) # Ensure post is usable outside
        return post

def search_items(product_query: str, channel_id: str) -> List[Item]:
    with Session(engine) as session:
        statement = (
            select(Item)
            .options(selectinload(Item.post)) # Eager load Post
            .join(Post)
            .where(Post.channel_id == channel_id)
            .where(Item.product_name.contains(product_query))
            .where(Item.status.in_(["Available", "Pending"])) # Hide Sold/Obsolete
            .order_by(Post.is_direct.desc(), Post.last_updated.desc()) # Direct first
        )
        return list(session.exec(statement).all())

def get_user_items(user_id: str) -> List[Item]:
    with Session(engine) as session:
        statement = (
            select(Item)
            .options(selectinload(Item.post)) # Eager load Post
            .join(Post)
            .where(Post.user_id == user_id)
            .order_by(Post.last_updated.desc())
        )
        return list(session.exec(statement).all())

def update_item_status(item_id: int, status: str):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if item:
            item.status = status
            item.post.last_updated = time.time()
            session.commit()
            return True
        return False

def update_item_details(item_id: int, product_name: str, price: str, features: str, post_type: str):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if item:
            item.product_name = product_name
            item.price = price
            item.features = features
            item.post_type = post_type
            item.post.last_updated = time.time()
            session.commit()
            return True
        return False

def delete_post(post_id: int):
    with Session(engine) as session:
        post = session.get(Post, post_id)
        if post:
            for item in post.items:
                session.delete(item)
            session.delete(post)
            session.commit()
            return True
        return False
