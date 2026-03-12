from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import Article, Bookmark, Category, User


def serialize_article(article: Article, user_id: int | None = None) -> Article:
    article.is_bookmarked = False
    if user_id is not None:
        article.is_bookmarked = any(bookmark.user_id == user_id for bookmark in article.bookmarks)
    return article


def get_feed(db: Session, user_id: int | None, category: str | None, limit: int = 20) -> tuple[list[Article], int]:
    query = (
        db.query(Article)
        .options(joinedload(Article.category), joinedload(Article.source), joinedload(Article.bookmarks))
        .order_by(desc(Article.published_at))
    )

    if category:
        query = query.join(Article.category).filter(func.lower(Category.name) == category.lower())

    articles = query.limit(limit * 2).all()

    if user_id:
        user = db.query(User).options(joinedload(User.preferences)).filter(User.id == user_id).first()
        preferred_ids = {pref.id for pref in user.preferences} if user else set()

        def score(article: Article) -> tuple[int, int, object]:
            preference_bonus = 100 if article.category_id in preferred_ids else 0
            return (preference_bonus + article.popularity_score, article.popularity_score, article.published_at)

        articles = sorted(articles, key=score, reverse=True)
    else:
        articles = sorted(articles, key=lambda article: (article.popularity_score, article.published_at), reverse=True)

    deduped: list[Article] = []
    seen_keys: set[str] = set()
    for article in articles:
        if article.dedupe_key in seen_keys:
            continue
        seen_keys.add(article.dedupe_key)
        deduped.append(serialize_article(article, user_id))
        if len(deduped) == limit:
            break

    return deduped, len(deduped)


def search_articles(db: Session, query_text: str, user_id: int | None) -> list[Article]:
    query = (
        db.query(Article)
        .options(joinedload(Article.category), joinedload(Article.source), joinedload(Article.bookmarks))
        .join(Article.category)
        .join(Article.source)
        .filter(
            or_(
                Article.title.ilike(f"%{query_text}%"),
                Article.summary.ilike(f"%{query_text}%"),
                Category.name.ilike(f"%{query_text}%"),
            )
        )
        .order_by(desc(Article.published_at))
    )
    return [serialize_article(article, user_id) for article in query.all()]


def add_bookmark(db: Session, user_id: int, article_id: int) -> None:
    exists = db.query(Bookmark).filter(Bookmark.user_id == user_id, Bookmark.article_id == article_id).first()
    if not exists:
        db.add(Bookmark(user_id=user_id, article_id=article_id))
        db.commit()


def remove_bookmark(db: Session, user_id: int, article_id: int) -> bool:
    bookmark = db.query(Bookmark).filter(Bookmark.user_id == user_id, Bookmark.article_id == article_id).first()
    if not bookmark:
        return False
    db.delete(bookmark)
    db.commit()
    return True


def get_bookmarks(db: Session, user_id: int) -> list[Article]:
    articles = (
        db.query(Article)
        .join(Bookmark, Bookmark.article_id == Article.id)
        .options(joinedload(Article.category), joinedload(Article.source), joinedload(Article.bookmarks))
        .filter(Bookmark.user_id == user_id)
        .order_by(desc(Bookmark.created_at))
        .all()
    )
    return [serialize_article(article, user_id) for article in articles]


def update_user_preferences(db: Session, user_id: int, category_ids: list[int]) -> User | None:
    user = db.query(User).options(joinedload(User.preferences)).filter(User.id == user_id).first()
    if not user:
        return None
    categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
    user.preferences = categories
    db.commit()
    db.refresh(user)
    return user
