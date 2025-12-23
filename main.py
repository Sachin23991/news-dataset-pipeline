#!/usr/bin/env python3
"""
News Dataset Pipeline - Main Script
Fetches news from RSS feeds, saves as JSONL/CSV, commits to GitHub, uploads to Hugging Face
"""

import os
import json
import csv
import feedparser
from datetime import datetime
from pathlib import Path
from huggingface_hub import HfApi, create_repo

# Configuration
HF_TOKEN = os.getenv('HF_TOKEN')
HF_USERNAME = 'Sachin21112004'
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 90 * 1024 * 1024  # 90MB

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
    'politics': [
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
    """Fetch news from RSS feeds"""
    articles = []
    for source_url in sources:
        try:
            feed = feedparser.parse(source_url)
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
                print(f'✓ {category}: {article["title"][:60]}...')
        except Exception as e:
            print(f'✗ Error fetching {source_url}: {str(e)}')
    return articles


def save_to_jsonl(category, articles):
    """Save articles to JSONL file"""
    filename = DATA_DIR / f'{category}.jsonl'
    with open(filename, 'a', encoding='utf-8') as f:
        for article in articles:
            f.write(json.dumps(article, ensure_ascii=False) + '\n')
    print(f'✓ Saved {len(articles)} articles to {filename}')
    return filename


def save_to_csv(category, articles):
    """Save articles to CSV file"""
    filename = DATA_DIR / f'{category}.csv'
    file_exists = filename.exists()
    
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=articles[0].keys() if articles else [])
        if not file_exists:
            writer.writeheader()
        writer.writerows(articles)
    print(f'✓ Saved {len(articles)} articles to {filename}')
    return filename


def upload_to_huggingface(category):
    """Upload data files to Hugging Face"""
    if not HF_TOKEN:
        print('✗ HF_TOKEN not set')
        return
    
    api = HfApi(token=HF_TOKEN)
    repo_id = f'{HF_USERNAME}/news-{category}-dataset'
    
    try:
        # Upload JSONL file
        jsonl_file = DATA_DIR / f'{category}.jsonl'
        if jsonl_file.exists():
            api.upload_file(
                path_or_fileobj=str(jsonl_file),
                path_in_repo=f'{category}.jsonl',
                repo_id=repo_id,
                repo_type='dataset',
                token=HF_TOKEN
            )
            print(f'✓ Uploaded {category}.jsonl to {repo_id}')
        
        # Upload CSV file
        csv_file = DATA_DIR / f'{category}.csv'
        if csv_file.exists():
            api.upload_file(
                path_or_fileobj=str(csv_file),
                path_in_repo=f'{category}.csv',
                repo_id=repo_id,
                repo_type='dataset',
                token=HF_TOKEN
            )
            print(f'✓ Uploaded {category}.csv to {repo_id}')
    except Exception as e:
        print(f'✗ Error uploading to {repo_id}: {str(e)}')


def main():
    """Main pipeline"""
    print(f'\n========== NEWS DATASET PIPELINE =========="')
    print(f'Started at: {datetime.now().isoformat()}\n')
    
    for category, sources in NEWS_SOURCES.items():
        print(f'\n--- Processing {category.upper()} ---')
        
        # Fetch news
        articles = fetch_news(category, sources)
        
        if articles:
            # Save to JSONL
            save_to_jsonl(category, articles)
            
            # Save to CSV
            save_to_csv(category, articles)
            
            # Upload to Hugging Face
            upload_to_huggingface(category)
        else:
            print(f'✗ No articles fetched for {category}')
    
    print(f'\n========== PIPELINE COMPLETED =========="')
    print(f'Completed at: {datetime.now().isoformat()}')
    print(f'Data saved in: {DATA_DIR}')


if __name__ == '__main__':
    main()
