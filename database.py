from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    user_type = Column(String, default="normal")
    created_at = Column(DateTime, default=datetime.utcnow)
    pro_expiry = Column(DateTime, nullable=True)
    channel_id = Column(String, nullable=True)
    channel_verified = Column(Boolean, default=False)
    daily_views = Column(Integer, default=0)
    daily_reactions = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)

class ReactionBot(Base):
    __tablename__ = "reaction_bots"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
