#!/usr/bin/env python3
"""
Enterprise RSS Scraper with:
✓ URL deduplication
✓ Feed health scoring + auto-disable
✓ Full article extraction
✓ Language detection
✓ Hugging Face dataset upload
"""

import json
import os
import ssl
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict

import feedparser
from huggingface_hub import HfApi, create_repo
from newspaper import Article
from langdetect import detect, LangDetectException

# ===================== SSL FIX =====================
ssl._create_default_https_context = ssl._create_unverified_context

# ===================== CONFIG =====================
DATA_DIR = "data"
STATE_DIR = "state"
MAX_FILE_SIZE = 90 * 1024 * 1024
MAX_FEED_FAILURES = 3

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not set")

api = HfApi()

Path(DATA_DIR).mkdir(exist_ok=True)
Path(STATE_DIR).mkdir(exist_ok=True)

# ===================== RSS SOURCES =====================
NEWS_SOURCES = {
    "tech": [
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/rss",
        "https://techcrunch.com/feed/",
        "https://arstechnica.com/feed/",
    ],
    "finance": [
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://www.reuters.com/finance/rss",
        "https://www.ft.com/rss/home",
    ],
    "education": [
        "https://www.sciencedaily.com/rss/education_learning.xml",
        "https://medium.com/feed/tag/education",
    ],
    "entertainment": [
        "https://variety.com/feed/",
        "https://deadline.com/feed/",
    ],
    "politics": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.reuters.com/world/rss",
        "https://www.theguardian.com/world/rss",
    ],
}

# ===================== STATE =====================
SEEN_URLS_FILE = f"{STATE_DIR}/seen_urls.json"
FEED_HEALTH_FILE = f"{STATE_DIR}/feed_health.json"

seen_urls = set(json.load(open(SEEN_URLS_FILE))) if os.path.exists(SEEN_URLS_FILE) else set()
feed_health = json.load(open(FEED_HEALTH_FILE)) if os.path.exists(FEED_HEALTH_FILE) else defaultdict(int)

# ===================== HELPERS =====================

def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def extract_article_text(url: str) -> str:
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text.strip()
    except Exception:
        return ""


def manage_storage(category: str) -> str:
    file_path = f"{DATA_DIR}/{category}.jsonl"
    if os.path.exists(file_path) and os.path.getsize(file_path) >= MAX_FILE_SIZE:
        os.remove(file_path)
    return file_path


def ensure_repo(repo_id: str):
    try:
        api.repo_info(repo_id, repo_type="dataset", token=HF_TOKEN)
    except Exception:
        create_repo(repo_id, repo_type="dataset", exist_ok=True, token=HF_TOKEN)

# ===================== FETCH =====================

def fetch_news(category: str, sources: list[str]) -> list[dict]:
    print(f"  > Fetching {category}")
    articles = []

    for source in sources:
        if feed_health.get(source, 0) >= MAX_FEED_FAILURES:
            print(f"    ⚠ Skipped unhealthy feed: {source}")
            continue

        try:
            feed = feedparser.parse(source)

            if feed.bozo or not feed.entries:
                feed_health[source] += 1
                continue

            for entry in feed.entries[:5]:
                url = entry.get("link")
                if not url:
                    continue

                h = url_hash(url)
                if h in seen_urls:
                    continue

                full_text = extract_article_text(url)
                lang = detect_language(full_text or entry.get("summary", ""))

                article = {
                    "title": entry.get("title", ""),
                    "link": url,
                    "summary": entry.get("summary", ""),
                    "content": full_text,
                    "language": lang,
                    "category": category,
                    "source": source,
                    "published": entry.get("published", ""),
                    "fetched_at": datetime.utcnow().isoformat(),
                }

                articles.append(article)
                seen_urls.add(h)

        except Exception:
            feed_health[source] += 1

    return articles

# ===================== SAVE + UPLOAD =====================

def save_and_upload(category: str, articles: list[dict]):
    if not articles:
        print(f"  ⚠ No new articles for {category}")
        return

    file_path = manage_storage(category)

    with open(file_path, "a", encoding="utf-8") as f:
        for a in articles:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    repo_id = f"Sachin21112004/news-{category}-dataset"
    ensure_repo(repo_id)

    api.upload_file(
        path_or_fileobj=file_path,
        path_in_repo=f"{category}.jsonl",
        repo_id=repo_id,
        repo_type="dataset",
        token=HF_TOKEN,
    )

    print(f"  ✓ Saved & uploaded {len(articles)} articles")

# ===================== MAIN =====================

def main():
    print(f"Pipeline started at {datetime.utcnow().isoformat()}")

    for category, sources in NEWS_SOURCES.items():
        print(f"\n--- {category.upper()} ---")
        articles = fetch_news(category, sources)
        save_and_upload(category, articles)

    json.dump(list(seen_urls), open(SEEN_URLS_FILE, "w"))
    json.dump(feed_health, open(FEED_HEALTH_FILE, "w"), indent=2)

    print("\n✓ PIPELINE COMPLETED")

if __name__ == "__main__":
    main()
