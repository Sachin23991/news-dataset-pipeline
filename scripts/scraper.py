#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from huggingface_hub import HfApi, create_repo
import time
import feedparser

api = HfApi()
HF_TOKEN = os.getenv('HF_TOKEN')
DATA_DIR = 'data'
MAX_FILE_SIZE = 90 * 1024 * 1024  # 90MB

# --- NEWS SOURCES ---
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
    """Fetch news safely. If one source fails, it skips to the next."""
    articles = []
    for source_url in sources:
        try:
            feed = feedparser.parse(source_url)
            if not feed.entries:
                continue
                
            for entry in feed.entries[:5]:
                article = {
                    'title': entry.get('title', 'No Title'),
                    'description': entry.get('summary', 'No Description'),
                    'link': entry.get('link', source_url),
                    'source': source_url,
                    'category': category,
                    'published': entry.get('published', datetime.now().isoformat()),
                    'fetched_at': datetime.now().isoformat()
                }
                articles.append(article)
        except Exception as e:
            print(f"  ⚠ Skipped {source_url}: {e}")
    return articles

def manage_file_size(category):
    """
    1. Checks if file exists (restored from Git).
    2. If > 90MB, deletes it (Rotates).
    3. Returns the filename to write to.
    """
    Path(DATA_DIR).mkdir(exist_ok=True)
    filename = f"{DATA_DIR}/{category}.jsonl"
    
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        # If file is too big, delete it to start fresh
        if size >= MAX_FILE_SIZE:
            print(f"♻ Rotating file: {filename} (Size: {size/1024/1024:.2f} MB)")
            os.remove(filename)
    
    return filename

def append_articles(category, articles):
    """Opens file in APPEND mode ('a') so we don't overwrite history."""
    filename = manage_file_size(category)
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + '\n')
        print(f"  ✓ Appended {len(articles)} articles to {filename}")
        return filename
    except Exception as e:
        print(f"  ✗ Error writing file: {e}")
        return None

def upload_to_hf(category, filename):
    """Uploads the updated file to Hugging Face."""
    if not filename or not os.path.exists(filename):
        return
    
    repo_id = f"Sachin21112004/news-{category}-dataset"
    try:
        api.upload_file(
            path_or_fileobj=filename,
            path_in_repo=os.path.basename(filename),
            repo_id=repo_id,
            repo_type="dataset",
            token=HF_TOKEN
        )
        print(f"  ✓ Synced {category} to Hugging Face")
    except Exception as e:
        print(f"  ✗ HF Upload Error: {e}")

def main():
    print(f"Starting pipeline at {datetime.now().isoformat()}")
    
    # Iterate through all categories properly
    for category, sources in NEWS_SOURCES.items():
        print(f"\n--- Processing {category.upper()} ---")
        try:
            articles = fetch_news(category, sources)
            if articles:
                filename = append_articles(category, articles)
                upload_to_hf(category, filename)
            else:
                print(f"  ⚠ No new articles for {category}")
        except Exception as e:
            # THIS IS THE FIX: Catches crashes so Politics still runs!
            print(f"  CRITICAL ERROR in {category}: {e}")
            continue

if __name__ == '__main__':
    main()
