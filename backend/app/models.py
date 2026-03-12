from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


user_preferences = Table(
    "user_preferences",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("Category", secondary=user_preferences, back_populates="users")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)
    homepage_url = Column(String(500), nullable=False)
    articles = relationship("Article", back_populates="source")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    articles = relationship("Article", back_populates="category")
    users = relationship("User", secondary=user_preferences, back_populates="preferences")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(255), nullable=True)
    url = Column(String(1000), nullable=False, unique=True)
    image_url = Column(String(1000), nullable=True)
    summary = Column(Text, nullable=False)
    content_snippet = Column(Text, nullable=True)
    dedupe_key = Column(String(255), nullable=False, index=True)
    popularity_score = Column(Integer, nullable=False, default=0)
    published_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    source = relationship("Source", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    bookmarks = relationship("Bookmark", back_populates="article", cascade="all, delete-orphan")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="bookmarks")
    article = relationship("Article", back_populates="bookmarks")
