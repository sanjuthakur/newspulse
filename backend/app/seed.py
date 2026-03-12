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
            "url": "https://www.bloomberg.com/news/articles/2025-03-05/nvidia-ai-server-maker-hon-hai-posts-25-jump-in-two-month-sales",
            "image_url": "https://images.example.com/chips.jpg",
            "summary": "Manufacturers are increasing packaging and fabrication capacity as cloud providers ramp AI infrastructure spending.",
            "content_snippet": "The investment cycle is expected to continue through the next planning period.",
            "dedupe_key": "chipmakers-ai-demand",
            "popularity_score": 90,
            "published_at": now - timedelta(hours=2),
            "source": source_map["Bloomberg"],
            "category": category_map["Business"],
        },
        {
            "title": "Researchers publish climate model showing sharper coastal risk",
            "author": "Liam Hughes",
            "url": "https://www.bbc.com/news/science-environment",
            "image_url": "https://images.example.com/climate.jpg",
            "summary": "A new model suggests some coastal regions may face flood thresholds earlier than prior projections indicated.",
            "content_snippet": "The paper focuses on compounding factors like storm surge and land subsidence.",
            "dedupe_key": "climate-coastal-risk",
            "popularity_score": 80,
            "published_at": now - timedelta(hours=3, minutes=5),
            "source": source_map["BBC"],
            "category": category_map["Science"],
        },
        {
            "title": "Premier league clubs push deeper into streaming partnerships",
            "author": "Olivia Reed",
            "url": "https://www.bbc.com/sport/football",
            "image_url": "https://images.example.com/sports.jpg",
            "summary": "Clubs are packaging behind-the-scenes content and match-adjacent programming for global streaming audiences.",
            "content_snippet": "The strategy aims to diversify revenue beyond traditional broadcast contracts.",
            "dedupe_key": "streaming-sports-partnerships",
            "popularity_score": 67,
            "published_at": now - timedelta(hours=4, minutes=12),
            "source": source_map["BBC"],
            "category": category_map["Sports"],
        },
        {
            "title": "Election campaign messaging shifts toward cost-of-living issues",
            "author": "Ethan Brooks",
            "url": "https://www.reuters.com/world/us/",
            "image_url": "https://images.example.com/politics.jpg",
            "summary": "Campaign teams are concentrating on wages, housing, and utility costs as voter priorities harden.",
            "content_snippet": "Recent polling suggests economic concerns remain dominant across key districts.",
            "dedupe_key": "election-cost-of-living",
            "popularity_score": 72,
            "published_at": now - timedelta(hours=5, minutes=25),
            "source": source_map["Reuters"],
            "category": category_map["Politics"],
        },
        {
            "title": "Studios bet on game adaptations to revive franchise growth",
            "author": "Sophia Nguyen",
            "url": "https://www.theverge.com/news/670547/clash-of-clans-netflix-animated-adaptation",
            "image_url": "https://images.example.com/entertainment.jpg",
            "summary": "Entertainment companies are using game franchises to build cross-platform audiences and subscription retention.",
            "content_snippet": "Executives say existing fandoms reduce launch risk in a fragmented market.",
            "dedupe_key": "game-adaptations-growth",
            "popularity_score": 61,
            "published_at": now - timedelta(hours=6, minutes=40),
            "source": source_map["The Verge"],
            "category": category_map["Entertainment"],
        },
        {
            "title": "Regional leaders call for coordinated response to shipping disruption",
            "author": "Grace Lewis",
            "url": "https://www.reuters.com/world/",
            "image_url": "https://images.example.com/world.jpg",
            "summary": "Governments are coordinating shipping security, insurance support, and route planning to limit delays.",
            "content_snippet": "Analysts say supply chain strain may reappear if disruptions persist.",
            "dedupe_key": "shipping-disruption-response",
            "popularity_score": 84,
            "published_at": now - timedelta(hours=7),
            "source": source_map["Reuters"],
            "category": category_map["World"],
        },
    ]
    for article in articles:
        upsert_article(db, article)
    db.commit()
