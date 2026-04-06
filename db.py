from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship, create_engine, Session, select
from sqlalchemy.orm import selectinload
import time

# --- Content Database (Posts, Items) ---
sqlite_file_name = "buyerbot.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

# --- Installation Database (Slack Workspace Tokens) ---
install_sqlite_file = "installations.db"
install_sqlite_url = f"sqlite:///{install_sqlite_file}"
install_engine = create_engine(install_sqlite_url)

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slack_ts: str = Field(index=True, unique=True)
    channel_id: str = Field(index=True)
    team_id: str = Field(index=True)
    user_id: str
    last_updated: float = Field(default_factory=time.time)
    is_direct: bool = Field(default=False)
    
    items: List["Item"] = Relationship(back_populates="post")

class SlackInstallation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: str = Field(index=True, unique=True)
    team_name: Optional[str] = None
    bot_token: str
    bot_id: str
    bot_user_id: str
    installer_user_id: str
    installed_at: float = Field(default_factory=time.time)

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id")
    product_name: str = Field(default="Unknown")
    price: str = Field(default="unknown")
    status: str = Field(default="Available")
    features: str = Field(default="")
    
    post: Post = Relationship(back_populates="items")

def create_db_and_tables():
    # Only create specific tables in each database
    Post.__table__.create(engine, checkfirst=True)
    Item.__table__.create(engine, checkfirst=True)
    SlackInstallation.__table__.create(install_engine, checkfirst=True)

def save_items_for_post(slack_ts: str, channel_id: str, team_id: str, user_id: str, items_data: List[dict], is_direct: bool = False):
    with Session(engine) as session:
        # Check if post already exists
        statement = select(Post).where(Post.slack_ts == slack_ts)
        post = session.exec(statement).first()
        
        if post:
            # Update existing post user/channel just in case
            post.user_id = user_id
            post.channel_id = channel_id
            post.team_id = team_id
            post.last_updated = time.time()
            post.is_direct = is_direct
            
            # For simplicity in this update, we'll clear existing items for this post and re-add
            for existing_item in post.items:
                session.delete(existing_item)
            post.items = []
        else:
            post = Post(slack_ts=slack_ts, channel_id=channel_id, team_id=team_id, user_id=user_id, is_direct=is_direct)
            session.add(post)
            session.flush() # Get the post.id
        
        for item_data in items_data:
            item = Item(
                post_id=post.id,
                product_name=item_data.get("product_name", "Unknown"),
                price=str(item_data.get("price", "unknown")),
                status=item_data.get("status") or "Available",
                features=", ".join(item_data.get("features", [])) if isinstance(item_data.get("features"), list) else str(item_data.get("features", ""))
            )
            session.add(item)
            
        session.commit()
        session.refresh(post) # Ensure post is usable outside
        return post

def search_items(product_query: str, channel_id: str, team_id: str) -> List[Item]:
    with Session(engine) as session:
        statement = (
            select(Item)
            .options(selectinload(Item.post)) # Eager load Post
            .join(Post)
            .where(Post.channel_id == channel_id)
            .where(Post.team_id == team_id)
            .where(Item.product_name.contains(product_query))
            .where(Item.status.in_(["Available", "Pending"])) # Hide Sold/Obsolete
            .order_by(Post.is_direct.desc(), Post.last_updated.desc()) # Direct first
        )
        return list(session.exec(statement).all())

def get_user_items(user_id: str, team_id: str) -> List[Item]:
    with Session(engine) as session:
        statement = (
            select(Item)
            .options(selectinload(Item.post)) # Eager load Post
            .join(Post)
            .where(Post.user_id == user_id)
            .where(Post.team_id == team_id)
            .order_by(Post.last_updated.desc())
        )
        return list(session.exec(statement).all())

from slack_sdk.oauth.installation_store import InstallationStore, Installation, Bot
from slack_sdk.oauth.installation_store.sqlite3 import SQLite3InstallationStore

class SQLModelInstallationStore(InstallationStore):
    def __init__(self, engine):
        self.engine = engine

    def save(self, installation: Installation):
        with Session(self.engine) as session:
            statement = select(SlackInstallation).where(SlackInstallation.team_id == installation.team_id)
            existing = session.exec(statement).first()
            
            data = {
                "team_id": installation.team_id,
                "team_name": installation.team_name,
                "bot_token": installation.bot_token,
                "bot_id": installation.bot_id,
                "bot_user_id": installation.bot_user_id,
                "installer_user_id": installation.user_id,
                "installed_at": time.time()
            }
            
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                new_inst = SlackInstallation(**data)
                session.add(new_inst)
            session.commit()

    def find_bot(self, *, enterprise_id: Optional[str], team_id: Optional[str], is_enterprise_install: Optional[bool] = False) -> Optional[Bot]:
        with Session(self.engine) as session:
            statement = select(SlackInstallation).where(SlackInstallation.team_id == team_id)
            inst = session.exec(statement).first()
            if inst:
                return Bot(
                    app_id=None,
                    enterprise_id=enterprise_id,
                    team_id=inst.team_id,
                    bot_token=inst.bot_token,
                    bot_id=inst.bot_id,
                    bot_user_id=inst.bot_user_id,
                    bot_scopes=None,
                    installed_at=inst.installed_at
                )
            return None

    def find_installation(self, *, enterprise_id: Optional[str], team_id: Optional[str], user_id: Optional[str] = None, is_enterprise_install: Optional[bool] = False) -> Optional[Installation]:
        # Minimal implementation for bot-only apps
        with Session(self.engine) as session:
            statement = select(SlackInstallation).where(SlackInstallation.team_id == team_id)
            inst = session.exec(statement).first()
            if inst:
                return Installation(
                    app_id=None,
                    enterprise_id=enterprise_id,
                    team_id=inst.team_id,
                    bot_token=inst.bot_token,
                    bot_id=inst.bot_id,
                    bot_user_id=inst.bot_user_id,
                    user_id=inst.installer_user_id,
                    bot_scopes=None,
                    installed_at=inst.installed_at
                )
            return None

def update_item_status(item_id: int, status: str):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if item:
            item.status = status
            item.post.last_updated = time.time()
            session.commit()
            return True
        return False

def update_item_details(item_id: int, product_name: str, price: str, features: str):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if item:
            item.product_name = product_name
            item.price = price
            item.features = features
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
