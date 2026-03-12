import os

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from app.database import Base, SessionLocal, engine, get_db
from app.models import Category, User
from app.schemas import ArticleResponse, BookmarkRequest, FeedResponse, MessageResponse, UserResponse, UpdatePreferencesRequest
from app.seed import ensure_base_data, seed_database
from app.services import add_bookmark, get_bookmarks, get_feed, remove_bookmark, search_articles, update_user_preferences


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


app = FastAPI(title="NewsPulse API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_base_data(db)
        if os.getenv("SEED_DATA", "true").lower() == "true":
            seed_database(db)
    finally:
        db.close()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name.asc()).all()


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int
