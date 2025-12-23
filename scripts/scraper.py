#!/usr/bin/env python3
import json
import os
import time
from datetime import datetime
from pathlib import Path
from huggingface_hub import HfApi
import feedparser

# --- CONFIGURATION ---
DATA_DIR = 'data'
MAX_FILE_SIZE = 90 * 1024 * 1024  # 90 MB
HF_TOKEN = os.getenv('HF_TOKEN')
api = HfApi()

# --- SOURCES ---
NEWS_SOURCES = {
    'tech': [
        'https://feeds.theverge.com/theverge/index.xml',
        'https://feeds.wired.com/feed/rss/wired',
        'https://feeds.techcrunch.com/',
        'https://feeds.9to5google.com/9to5google/feed'
    ],
    'finance': [
        'https://feeds.bloomberg.com/markets/news.rss',
        'https://feeds.reuters.com/finance',
        'https://feeds.wsj.com/xml/rss/3_7085.xml',
        'https://feeds.yahoo.com/finance'
    ],
    'education': [
        'https://feeds.edx.org/feed',
        'https://feeds.sciencedaily.com/feed',
        'https://feeds.coursera.org/feed',
        'https://feeds.medium.com/feed/learning'
    ],
    'entertainment': [
        'https://feeds.variety.com/feed',
        'https://feeds.deadline.com/feed',
        'https://feeds.hollywoodreporter.com/feed',
        'https://feeds.ign.com/feed'
    ],
    'political': [
        'https://feeds.bbc.com/news/world/rss.xml',
        'https://feeds.cnn.com/cnn/cnn_topstories',
        'https://feeds.reuters.com/politics',
        'https://feeds.theguardian.com/world/rss'
    ]
}

def fetch_news(category, sources):
    """Fetch news from RSS feeds."""
    articles = []
    print(f"  > Fetching {category} news...")
    for source in sources:
        try:
            feed = feedparser.parse(source)
            if not feed.entries: continue
            
            # Get latest 5 articles
            for entry in feed.entries[:5]:
                articles.append({
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', source),
                    'description': entry.get('summary', 'No summary'),
                    'category': category,
                    'source': source,
                    'published': entry.get('published', str(datetime.now())),
                    'fetched_at': str(datetime.now())
                })
        except Exception as e:
            print(f"    ! Error reading {source}: {e}")
    return articles

def manage_github_storage(category):
    """
    Manages the local file in the GitHub repo.
    If file > 90MB, delete it (rotate).
    """
    Path(DATA_DIR).mkdir(exist_ok=True)
    filename = f"{DATA_DIR}/{category}.jsonl"
    
    if os.path.exists(filename):
        size_mb = os.path.getsize(filename) / (1024 * 1024)
        if size_mb >= 90:
            print(f"  ♻ ROTATING: File {filename} is {size_mb:.2f}MB. Deleting to start fresh.")
            os.remove(filename)
        else:
            print(f"  ✓ STORAGE: File {filename} is {size_mb:.2f}MB. Appending...")
    
    return filename

def save_and_upload(category, articles):
    """Saves to GitHub folder first, then uploads to HF."""
    if not articles: return

    # 1. Save to GitHub Storage (Append Mode)
    filename = manage_github_storage(category)
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            for article in articles:
                f.write(json.dumps(article) + '\n')
        print(f"  ✓ SAVED: Added {len(articles)} articles to {filename}")
    except Exception as e:
        print(f"  ✗ SAVE ERROR: {e}")
        return

    # 2. Upload to Hugging Face
    repo_id = f"Sachin21112004/news-{category}-dataset"
    try:
        api.upload_file(
            path_or_fileobj=filename,
            path_in_repo=f"{category}.jsonl", # Always keeps one main file on HF
            repo_id=repo_id,
            repo_type="dataset",
            token=HF_TOKEN
        )
        print(f"  ✓ UPLOADED: Synced {filename} to Hugging Face")
    except Exception as e:
        print(f"  ✗ UPLOAD ERROR: {e}")

def main():
    print(f"Starting pipeline at {datetime.now()}")
    
    for category, sources in NEWS_SOURCES.items():
        print(f"\n--- Processing {category.upper()} ---")
        try:
            articles = fetch_news(category, sources)
            save_and_upload(category, articles)
        except Exception as e:
            print(f"  CRITICAL FAILURE in {category}: {e}")
            continue # Ensures we move to next category even if one fails
            
    print("\n✓ Pipeline Finished")

if __name__ == "__main__":
    main()
