from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Article, Category, Source, User


def get_or_create_category(db: Session, name: str) -> Category:
    category = db.query(Category).filter(Category.name == name).first()
    if category:
        return category
    category = Category(name=name)
    db.add(category)
    db.flush()
    return category


def get_or_create_source(db: Session, name: str, source_type: str, homepage_url: str) -> Source:
    source = db.query(Source).filter(Source.name == name).first()
    if source:
        source.source_type = source_type
        source.homepage_url = homepage_url
        db.flush()
        return source
    source = Source(name=name, source_type=source_type, homepage_url=homepage_url)
    db.add(source)
    db.flush()
    return source


def upsert_article(db: Session, payload: dict) -> None:
    article = db.query(Article).filter(Article.dedupe_key == payload["dedupe_key"]).first()
    if article:
        for key, value in payload.items():
            setattr(article, key, value)
        return
    db.add(Article(**payload))


def ensure_base_data(db: Session) -> dict[str, Category]:
    category_names = [
        "World",
        "Technology",
        "Finance",
        "Business",
        "Politics",
        "Sports",
        "Entertainment",
        "Science",
    ]
    categories = [get_or_create_category(db, name) for name in category_names]
    category_map = {category.name: category for category in categories}

    demo_user = db.query(User).filter(User.email == "demo@newspulse.app").first()
    if not demo_user:
        demo_user = User(email="demo@newspulse.app", name="Demo User")
        db.add(demo_user)
    demo_user.name = "Demo User"
    demo_user.preferences = [
        category_map["Technology"],
        category_map["Finance"],
        category_map["Science"],
    ]
    db.commit()

    return category_map


def seed_database(db: Session) -> None:
    category_map = ensure_base_data(db)

    sources = [
        get_or_create_source(db, "Reuters", "rss", "https://www.reuters.com"),
        get_or_create_source(db, "BBC", "rss", "https://www.bbc.com"),
        get_or_create_source(db, "TechCrunch", "api", "https://techcrunch.com"),
        get_or_create_source(db, "The Verge", "website", "https://www.theverge.com"),
        get_or_create_source(db, "Bloomberg", "api", "https://www.bloomberg.com"),
    ]

    source_map = {source.name: source for source in sources}
    now = datetime.now(timezone.utc)

    articles = [
        {
            "title": "OpenAI releases developer tooling for enterprise teams",
            "author": "Mia Carter",
            "url": "https://techcrunch.com/2025/03/11/openai-launches-new-tools-to-help-businesses-build-ai-agents/",
            "image_url": "https://images.example.com/openai.jpg",
            "summary": "Enterprise-focused tooling ships with governance controls, deployment analytics, and stronger API observability.",
            "content_snippet": "The release is aimed at teams standardizing AI development across internal platforms.",
            "dedupe_key": "openai-enterprise-tooling",
            "popularity_score": 95,
            "published_at": now - timedelta(minutes=22),
            "source": source_map["TechCrunch"],
            "category": category_map["Technology"],
        },
        {
            "title": "Federal Reserve signals caution as inflation cools unevenly",
            "author": "Noah Bennett",
            "url": "https://www.reuters.com/markets/us/",
            "image_url": "https://images.example.com/fed.jpg",
            "summary": "Policymakers held their line on rates while indicating that labor and services inflation remain key watch points.",
            "content_snippet": "Markets reacted modestly as investors reassessed the timing of future cuts.",
            "dedupe_key": "fed-inflation-update",
            "popularity_score": 88,
            "published_at": now - timedelta(hours=1, minutes=10),
            "source": source_map["Reuters"],
            "category": category_map["Finance"],
        },
        {
            "title": "Global chipmakers expand capacity to meet AI server demand",
            "author": "Ava Patel",
            "url": "https://www.bloomberg.com/news/articles/2025-03-05/nvidia-ai-server-maker-hon
