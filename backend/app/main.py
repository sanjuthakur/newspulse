import os

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from app.database import Base, SessionLocal, engine, get_db
from app.models import Category, User
from app.schemas import (
    ArticleResponse,
    BookmarkRequest,
    FeedResponse,
    MessageResponse,
    UpdatePreferencesRequest,
    UserResponse,
)
from app.seed import ensure_base_data, seed_database
from app.services import (
    add_bookmark,
    get_bookmarks,
    get_feed,
    remove_bookmark,
    search_articles,
    update_user_preferences,
)


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
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.preferences)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/api/users/{user_id}/preferences", response_model=UserResponse)
def set_preferences(user_id: int, payload: UpdatePreferencesRequest, db: Session = Depends(get_db)):
    user = update_user_preferences(db, user_id, payload.category_ids)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/news", response_model=FeedResponse)
def news_feed(
    user_id: int | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    items, total = get_feed(db, user_id=user_id, category=category, limit=limit)
    return FeedResponse(items=items, total=total)


@app.get("/api/search", response_model=list[ArticleResponse])
def search(q: str = Query(min_length=1), user_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    return search_articles(db, q, user_id)


@app.get("/api/bookmarks", response_model=list[ArticleResponse])
def list_bookmarks(user_id: int = Query(...), db: Session = Depends(get_db)):
    return get_bookmarks(db, user_id)


@app.post("/api/bookmarks", response_model=MessageResponse)
def create_bookmark(payload: BookmarkRequest, db: Session = Depends(get_db)):
    add_bookmark(db, payload.user_id, payload.article_id)
    return MessageResponse(message="Bookmark saved")


@app.delete("/api/bookmarks/{article_id}", response_model=MessageResponse)
def delete_bookmark(article_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    removed = remove_bookmark(db, user_id, article_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return MessageResponse(message="Bookmark removed")
