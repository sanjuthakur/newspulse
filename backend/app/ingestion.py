import asyncio
import hashlib
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

import httpx
from sqlalchemy.orm import Session

from app.models import Article, Category, Source
from app.seed import get_or_create_category, get_or_create_source, upsert_article


RSS_FEEDS = [
    {
        "name": "BBC",
        "source_type": "rss",
        "homepage_url": "https://www.bbc.com",
        "feed_url": "http://feeds.bbci.co.uk/news/rss.xml",
    },
    {
        "name": "BBC Technology",
        "source_type": "rss",
        "homepage_url": "https://www.bbc.com/news/technology",
        "feed_url": "http://feeds.bbci.co.uk/news/technology/rss.xml",
    },
    {
        "name": "TechCrunch",
        "source_type": "rss",
        "homepage_url": "https://techcrunch.com",
        "feed_url": "https://techcrunch.com/feed/",
    },
    {
        "name": "The Verge",
        "source_type": "rss",
        "homepage_url": "https://www.theverge.com",
        "feed_url": "https://www.theverge.com/rss/index.xml",
    },
]

KEYWORD_CATEGORIES = {
    "Technology": ["ai", "software", "app", "device", "startup", "chip", "cloud", "openai", "google", "apple", "microsoft"],
    "Finance": ["market", "stocks", "inflation", "interest rate", "fed", "bank", "crypto", "bond"],
    "Business": ["company", "earnings", "merger", "revenue", "industry", "supply chain"],
    "Politics": ["election", "government", "policy", "minister", "president", "senate"],
    "Sports": ["match", "league", "team", "football", "cricket", "nba", "fifa"],
    "Entertainment": ["movie", "tv", "music", "streaming", "show", "celebrity", "game"],
    "Science": ["research", "study", "science", "climate", "space", "physics", "biology"],
    "World": ["war", "global", "international", "world", "diplomat", "border", "shipping"],
}


def get_ingestion_interval_seconds() -> int:
    minutes = int(os.getenv("INGESTION_INTERVAL_MINUTES", "30"))
    return max(minutes, 5) * 60


def should_enable_ingestion() -> bool:
    return os.getenv("ENABLE_RSS_INGESTION", "true").lower() == "true"


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def pick_text(entry: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_whitespace(strip_html(value))
    return ""


def parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        return datetime.now(timezone.utc)


def categorize_article(title: str, summary: str) -> str:
    haystack = f"{title} {summary}".lower()
    for category, keywords in KEYWORD_CATEGORIES.items():
        if any(keyword in haystack for keyword in keywords):
            return category
    return "World"


def summarize_entry(title: str, summary: str, description: str) -> tuple[str, str]:
    base_text = summary or description or title
    base_text = normalize_whitespace(strip_html(base_text))
    snippet = base_text[:240].rsplit(" ", 1)[0].strip() if len(base_text) > 240 else base_text
    final_summary = base_text[:320].rsplit(" ", 1)[0].strip() if len(base_text) > 320 else base_text
    return final_summary or title, snippet or title


def calculate_popularity(title: str, summary: str, published_at: datetime) -> int:
    score = 50
    recency_hours = max((datetime.now(timezone.utc) - published_at).total_seconds() / 3600, 0)
    score += max(0, 36 - int(recency_hours)) // 2
    haystack = f"{title} {summary}".lower()
    for keyword in ("breaking", "live", "openai", "ai", "market", "election", "climate"):
        if keyword in haystack:
            score += 5
    return min(score, 100)


def build_dedupe_key(url: str, title: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "")
    slug = parsed.path.rstrip("/").split("/")[-1]
    if slug:
        return f"{host}-{slug}"[:255]
    return f"{host}-{hashlib.sha1(title.encode('utf-8')).hexdigest()[:24]}"[:255]


def parse_rss(xml_text: str) -> list[dict[str, str]]:
    root = ElementTree.fromstring(xml_text)
    entries: list[dict[str, str]] = []

    for item in root.findall(".//item"):
        entry: dict[str, str] = {
            "title": item.findtext("title", default="").strip(),
            "link": item.findtext("link", default="").strip(),
            "author": item.findtext("author", default="").strip() or item.findtext("{http://purl.org/dc/elements/1.1/}creator", default="").strip(),
            "description": item.findtext("description", default="").strip(),
            "published": item.findtext("pubDate", default="").strip(),
        }
        media = item.find("{http://search.yahoo.com/mrss/}content")
        thumbnail = item.find("{http://search.yahoo.com/mrss/}thumbnail")
        if media is not None and media.attrib.get("url"):
            entry["image_url"] = media.attrib["url"].strip()
        elif thumbnail is not None and thumbnail.attrib.get("url"):
            entry["image_url"] = thumbnail.attrib["url"].strip()
        entries.append(entry)

    return entries


async def fetch_feed(client: httpx.AsyncClient, feed: dict[str, str]) -> list[dict[str, str]]:
    response = await client.get(feed["feed_url"], timeout=20.0, follow_redirects=True)
    response.raise_for_status()
    return parse_rss(response.text)


async def ingest_all_sources(db: Session) -> dict[str, Any]:
    categories = {name: get_or_create_category(db, name) for name in KEYWORD_CATEGORIES}
    categories.setdefault("World", get_or_create_category(db, "World"))

    ingested = 0
    sources_processed = 0
    failures: list[str] = []

    async with httpx.AsyncClient(headers={"User-Agent": "NewsPulseBot/1.0"}) as client:
        for feed in RSS_FEEDS:
            try:
                source = get_or_create_source(db, feed["name"], feed["source_type"], feed["homepage_url"])
                entries = await fetch_feed(client, feed)
                sources_processed += 1
                for entry in entries[:25]:
                    url = pick_text(entry, "link")
                    title = pick_text(entry, "title")
                    if not url or not title:
                        continue
                    description = pick_text(entry, "description")
                    summary, snippet = summarize_entry(title, description, description)
                    category_name = categorize_article(title, summary)
                    category = categories.get(category_name) or categories["World"]
                    published_at = parse_datetime(entry.get("published"))
                    payload = {
                        "title": title,
                        "author": pick_text(entry, "author") or None,
                        "url": url,
                        "image_url": pick_text(entry, "image_url") or None,
                        "summary": summary,
                        "content_snippet": snippet,
                        "dedupe_key": build_dedupe_key(url, title),
                        "popularity_score": calculate_popularity(title, summary, published_at),
                        "published_at": published_at,
                        "source": source,
                        "category": category,
                    }
                    upsert_article(db, payload)
                    ingested += 1
                db.commit()
            except (httpx.HTTPError, ElementTree.ParseError, ValueError) as exc:
                failures.append(f"{feed['name']}: {exc}")
                db.rollback()

    return {
        "sources_processed": sources_processed,
        "articles_ingested": ingested,
        "failures": failures,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }


async def run_ingestion_loop(session_factory) -> None:
    while True:
        db = session_factory()
        try:
            await ingest_all_sources(db)
        finally:
            db.close()
        await asyncio.sleep(get_ingestion_interval_seconds())
