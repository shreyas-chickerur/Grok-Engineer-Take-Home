import os
import datetime as dt
from typing import Optional, List

from sqlalchemy import create_engine, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DB_PATH = os.getenv("DB_PATH", "./data/app.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, future=True)

class Base(DeclarativeBase):
    pass

class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stage: Mapped[str] = mapped_column(String(40), default="new")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
    interactions: Mapped[List["Interaction"]] = relationship(back_populates="lead", cascade="all, delete-orphan")

class Interaction(Base):
    __tablename__ = "interactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    kind: Mapped[str] = mapped_column(String(40))  # e.g., qualification, outreach, note
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    lead: Mapped[Lead] = relationship(back_populates="interactions")

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()
