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

# --- NEWS SOURCES (Same as before) ---
NEWS_SOURCES = {
    'tech': [
        'https://feeds.theverge.com/theverge/index.xml',
        'https://feeds2.cnbc.com/id/100003114/feed',
        'https://feeds.arstechnica.com/arstechnica/index',
        'https://feeds.wired.com/feed/rss/wired',
        'https://feeds.bloomberg.com/technology/news.rss',
        'https://feeds.fastcompany.com/fastcompany',
        'https://feeds.techcrunch.com/',
        'https://feeds.slashdot.org/slashdot/slashdot',
        'https://feeds.9to5google.com/9to5google/feed',
        'https://feeds.engadget.com/gadgets'
    ],
    'finance': [
        'https://feeds.bloomberg.com/markets/news.rss',
        'https://feeds.cnbc.com/cnbc/world',
        'https://feeds.reuters.com/finance',
        'https://feeds.marketwatch.com/marketwatch/topstories',
        'https://feeds.bloomberg.com/energy/news.rss',
        'https://feeds.ft.com/markets',
        'https://feeds.wsj.com/xml/rss/3_7085.xml',
        'https://feeds.yahoo.com/finance',
        'https://feeds.investing.com/forex',
        'https://feeds.zerodha.com/varsity'
    ],
    'education': [
        'https://feeds.edx.org/feed',
        'https://feeds.coursera.org/feed',
        'https://feeds.medium.com/feed/learning',
        'https://feeds.springer.com/journals/rss',
        'https://feeds.nature.com/ncomms/rss/current',
        'https://feeds.sciencedaily.com/feed',
        'https://feeds.toward-data-science.com/feed',
        'https://feeds.towardsdatascience.com/feed',
        'https://feeds.udemy.com/courses/feed',
        'https://feeds.khanacademy.org/feed'
    ],
    'entertainment': [
        'https://feeds.hollywood.com/feed',
        'https://feeds.variety.com/feed',
        'https://feeds.deadline.com/feed',
        'https://feeds.ew.com/feed',
        'https://feeds.theonion.com/feed',
        'https://feeds.vulture.com/feed',
        'https://feeds.collider.com/feed',
        'https://feeds.hollywoodreporter.com/feed',
        'https://feeds.slashfilm.com/feed',
        'https://feeds.ign.com/feed'
    ],
    'political': [
        'https://feeds.bbc.com/news/world/rss.xml',
        'https://feeds.cnn.com/cnn/cnn_topstories',
        'https://feeds.reuters.com/politics',
        'https://feeds.theguardian.com/world/rss',
        'https://feeds.aljazeera.com/english/news',
        'https://feeds.npr.org/feeds/news/news.php',
        'https://feeds.apnews.com/apnews/ApNewsMainFeed',
        'https://feeds.bbc.com/news/politics/rss.xml',
        'https://feeds.washingtonpost.com/rss/politics',
        'https://feeds.huffpost.com/huffpost/politics'
    ]
}

def fetch_news(category, sources):
    """Fetch news from RSS feeds with individual error handling"""
    articles = []
    for source_url in sources:
        try:
            feed = feedparser.parse(source_url)
            if not feed.entries:
                print(f"  ⚠ No entries found for {source_url}")
                continue
                
            for entry in feed.entries[:5]:
                article = {
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'link': entry.get('link', ''),
                    'source': source_url,
                    'category': category,
                    'published': entry.get('published', datetime.now().isoformat()),
                    'fetched_at': datetime.now().isoformat()
                }
                articles.append(article)
            print(f"  ✓ Fetched {len(feed.entries[:5])} items from {source_url}")
        except Exception as e:
            print(f"  ✗ Error fetching {source_url}: {str(e)}")
        # Reduced sleep to speed up pipeline
        time.sleep(0.2)
    return articles

def manage_file_size(category):
    """Check file size and delete if > 90MB"""
    Path(DATA_DIR).mkdir(exist_ok=True)
    filename = f"{DATA_DIR}/{category}.jsonl"
    
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        if size >= MAX_FILE_SIZE:
            print(f"⚠ File {filename} is {size/1024/1024:.2f}MB. Deleting to reset...")
            os.remove(filename)
    
    return filename

def append_articles(category, articles):
    """Append articles to JSONL file"""
    filename = manage_file_size(category)
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + '\n')
        print(f"  ✓ Saved {len(articles)} articles to {filename}")
        return filename
    except Exception as e:
        print(f"  ✗ Error writing to file: {e}")
        return None

def upload_to_hf(category, filename):
    """Upload to Hugging Face"""
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
        print(f"  ✓ Uploaded to {repo_id}")
    except Exception as e:
        print(f"  ✗ HF Upload failed: {str(e)}")

def main():
    print(f"Starting news scraper at {datetime.now().isoformat()}")
    
    # We iterate nicely. If one category crashes, we catch it and move to the next.
    for category, sources in NEWS_SOURCES.items():
        print(f"\n=== Processing: {category.upper()} ===")
        try:
            articles = fetch_news(category, sources)
            if articles:
                filename = append_articles(category, articles)
                upload_to_hf(category, filename)
            else:
                print(f"  ⚠ No articles found for {category}")
        except Exception as e:
            # THIS IS KEY: We catch the crash here so the script doesn't die.
            print(f"  CRITICAL ERROR processing {category}: {e}")
            continue

    print(f"\n✓ Scraper completed at {datetime.now().isoformat()}")

if __name__ == '__main__':
    main()
