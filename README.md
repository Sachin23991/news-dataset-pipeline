# News Dataset Pipeline 📰

An automated news scraper that fetches articles from trusted sources, categorizes them into **5 categories**, and uploads them to **Hugging Face datasets** using GitHub Actions.

## 📋 Features

✅ **Automated Scraping**: Runs every 6 hours via GitHub Actions  
✅ **5 News Categories**: Tech, Finance, Education, Entertainment, Political  
✅ **10 Trusted Sources per Category**: Diverse, reliable news feeds  
✅ **Hugging Face Integration**: Auto-uploads to HF datasets  
✅ **Smart File Rotation**: Creates new files at 90MB limit  
✅ **Auto-Commits**: Commits with author as Sachin23991  
✅ **5 Separate Dataset Repos**: One per category for organization  

## 📊 Categories & Sources

### 🔧 **Tech** (10 sources)
- The Verge, CNBC Tech, Ars Technica, Wired, Bloomberg Tech
- FastCompany, TechCrunch, Slashdot, 9to5Google, Engadget

### 💰 **Finance** (10 sources)
- Bloomberg Markets, CNBC, Reuters Finance, MarketWatch, Bloomberg Energy
- Financial Times, WSJ, Yahoo Finance, Investing.com, Zerodha Varsity

### 📚 **Education** (10 sources)
- edX, Coursera, Medium Learning, Springer, Nature Communications
- ScienceDaily, Towards Data Science, Udemy, Khan Academy, + more

### 🎬 **Entertainment** (10 sources)
- Hollywood, Variety, Deadline, EW, The Onion
- Vulture, Collider, Hollywood Reporter, SlashFilm, IGN

### 🏛️ **Political** (10 sources)
- BBC News, CNN, Reuters Politics, The Guardian, Al Jazeera
- NPR, AP News, Washington Post, Huffington Post

## 🏗️ Project Structure

```
news-dataset-pipeline/
├── .github/
│   └── workflows/
│       └── news-scraper.yml          # GitHub Actions workflow
├── scripts/
│   └── scraper.py                    # Main scraper script
├── .gitignore                         # Ignore data files & cache
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## 🚀 Getting Started

### Local Setup

```bash
# Clone the repository
git clone https://github.com/Sachin23991/news-dataset-pipeline.git
cd news-dataset-pipeline

# Install dependencies
pip install -r requirements.txt

# Set HF_TOKEN environment variable
export HF_TOKEN="your_huggingface_token"

# Run the scraper
python scripts/scraper.py
```

### GitHub Actions Setup

The workflow automatically runs **every 6 hours**. To manually trigger:

1. Go to **Actions** tab
2. Select **News Dataset Pipeline**
3. Click **Run workflow**

### Required Secrets

Add this secret in **Settings → Secrets and variables → Actions**:

- `HF_TOKEN`: Your Hugging Face API token

## 📦 Generated Datasets

All datasets are created automatically in Hugging Face:

```
https://huggingface.co/datasets/Sachin23991/news-tech-dataset
https://huggingface.co/datasets/Sachin23991/news-finance-dataset
https://huggingface.co/datasets/Sachin23991/news-education-dataset
https://huggingface.co/datasets/Sachin23991/news-entertainment-dataset
https://huggingface.co/datasets/Sachin23991/news-politics-dataset
```

## 📄 Data Format

Each article is stored as JSONL with the following structure:

```json
{
  "title": "Article Title",
  "description": "Article summary or content",
  "link": "https://example.com/article",
  "source": "https://feeds.example.com/feed",
  "category": "tech",
  "published": "2025-01-01T12:00:00",
  "fetched_at": "2025-01-01T14:30:00"
}
```

## 🔄 Workflow Details

1. **Fetch**: Scrapes 5 articles from each source (50 per category)
2. **Categorize**: Articles are auto-categorized by source
3. **Append**: Adds to category JSONL files
4. **Rotate**: Creates new file when current reaches 90MB
5. **Upload**: Uploads to corresponding HF dataset repo
6. **Commit**: Commits changes with author: Sachin23991
7. **Push**: Pushes to main branch

## 🛠️ Dependencies

- **requests** (2.31.0+): HTTP requests
- **beautifulsoup4** (4.12.0+): HTML parsing
- **feedparser** (6.0.10+): RSS/Atom parsing
- **huggingface-hub** (0.19.0+): HF API integration
- **python-dateutil** (2.8.2+): Date parsing

## 📊 File Rotation Logic

- Each category can grow up to **~90MB** per file
- When a file reaches 90MB, a new file is created
- Files are named: `{category}_{counter:03d}.jsonl`
- Example: `tech_001.jsonl`, `tech_002.jsonl`, etc.

## 🔐 Security Notes

- HF_TOKEN is stored as a GitHub secret (encrypted)
- Token is never exposed in logs or commits
- Only used by GitHub Actions workflow

## 📝 Commit Messages

All commits follow this format:
```
[AUTO] News dataset update - 2025-01-01_14:30:00
```

Commit author: **Sachin23991** (Sachin Rao)  
Commit email: **sachinraosahab7@gmail.com**

## 🤝 Contributing

To add new news sources:

1. Edit `scripts/scraper.py`
2. Add URLs to `NEWS_SOURCES` dictionary
3. Commit and push
4. Workflow will automatically use new sources

## 📈 Monitoring

Check the **Actions** tab for:
- Workflow execution history
- Logs for each run
- Success/failure status
- Dataset upload confirmations

## 🚨 Troubleshooting

**Error: API rate limits**
- Solution: Increased delay between requests (0.5s)

**Error: File upload fails**
- Check HF_TOKEN is valid and has write permissions
- Verify dataset repo exists

**Error: No articles fetched**
- RSS feed might be down
- Check feed URL is accessible
- Increase timeout in requests

## 📄 License

MIT License - Feel free to use and modify

## 👨‍💻 Author

**Sachin Rao** (@Sachin23991)  
Data Scientist & Full Stack Developer  
Building the future with Code, Cloud & AI

---

**Last Updated**: January 2025  
**Status**: ✅ Active & Automated
