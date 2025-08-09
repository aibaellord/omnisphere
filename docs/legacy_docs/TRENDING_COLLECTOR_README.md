# 🔥 Trending Data Collector Agent

The Trending Data Collector is an automated system that fetches YouTube's most popular videos by region and category, handles API pagination and quota limits, and stores the data in both JSON snapshots and SQLite database for analysis.

## ✨ Features

- 📊 **Multi-region & Multi-category Collection**: Fetch trending videos from 20+ regions across 14 categories
- 🔄 **Intelligent API Management**: Automatic API key rotation and quota tracking
- 💾 **Dual Storage**: JSON snapshots for archiving + SQLite with SQLModel ORM for querying
- ⚡ **Async Processing**: Fast, non-blocking data collection
- 📈 **Comprehensive Analytics**: Track collection stats, success rates, and performance
- 🚀 **GitHub Actions Integration**: Automated hourly collection with cloud storage
- 🎯 **CLI Management**: Easy command-line interface for manual operations

## 🚀 Quick Start

### 1. Set Up API Keys

```bash
# Set your YouTube Data API key(s)
export YOUTUBE_API_KEY="your-youtube-api-key-here"

# Optional: Multiple keys for quota rotation
export YOUTUBE_API_KEY_1="your-first-key"
export YOUTUBE_API_KEY_2="your-second-key"
export YOUTUBE_API_KEY_3="your-third-key"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Your First Collection

```bash
# Collect trending videos from US, UK, and Canada
python trending_cli.py collect --regions US,GB,CA --categories 10,24,28

# Or run the full automated collection
python collect_trending.py
```

## 📋 Available Commands

### CLI Usage

```bash
# Collection Commands
python trending_cli.py collect                           # Full collection
python trending_cli.py collect --regions US,GB          # Specific regions
python trending_cli.py collect --categories 10,24       # Specific categories
python trending_cli.py collect --max-results 25         # Limit results per request

# Status & Monitoring
python trending_cli.py status                           # Show quota usage
python trending_cli.py history --days 7                # Recent collections
python trending_cli.py list-regions                    # Available regions
python trending_cli.py list-categories                 # Available categories

# Data Export
python trending_cli.py export --format json --days 7   # Export as JSON
python trending_cli.py export --format csv --days 30   # Export as CSV
python trending_cli.py export --format excel           # Export as Excel
```

## 🌍 Supported Regions

| Region | Code | Region | Code | Region | Code | Region | Code |
|--------|------|--------|------|--------|------|--------|------|
| United States | US | United Kingdom | GB | Canada | CA | Australia | AU |
| Germany | DE | France | FR | Spain | ES | Italy | IT |
| Japan | JP | South Korea | KR | Brazil | BR | Mexico | MX |
| India | IN | Russia | RU | Netherlands | NL | Sweden | SE |
| Norway | NO | Denmark | DK | Finland | FI | Poland | PL |

## 📂 Supported Categories

| ID | Category | ID | Category |
|----|----------|----|----------|
| 1 | Film & Animation | 2 | Autos & Vehicles |
| 10 | Music | 15 | Pets & Animals |
| 17 | Sports | 19 | Travel & Events |
| 20 | Gaming | 22 | People & Blogs |
| 23 | Comedy | 24 | Entertainment |
| 25 | News & Politics | 26 | Howto & Style |
| 27 | Education | 28 | Science & Technology |

## 📁 Data Storage

### JSON Snapshots
- **Location**: `/data/trending/YYYY-MM-DD_BATCH_ID.json`
- **Format**: Complete structured data with metadata
- **Use Case**: Long-term archiving, data portability

```json
{
  "collection_metadata": {
    "batch_id": "20240109_143022",
    "collection_date": "2024-01-09T14:30:22Z",
    "total_videos": 1250,
    "collector_version": "1.0.0"
  },
  "videos": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Amazing Trending Video",
      "channel_title": "Popular Channel",
      "region_code": "US",
      "category_name": "Music",
      "view_count": 1000000,
      "engagement_rate": 5.2,
      "trending_rank": 1
    }
  ]
}
```

### SQLite Database
- **Location**: `trending_data.db`
- **ORM**: SQLModel (Pydantic + SQLAlchemy)
- **Tables**: `trending_videos`, `collection_stats`, `quota_usage`
- **Use Case**: Fast queries, analytics, reporting

## 🤖 GitHub Actions Automation

The collector includes a complete GitHub Actions workflow for automated data collection:

### Setup

1. **Add Repository Secrets**:
   - `YOUTUBE_API_KEY_1`: Primary YouTube API key
   - `YOUTUBE_API_KEY_2`: Secondary API key (optional)
   - `YOUTUBE_API_KEY_3`: Tertiary API key (optional)

2. **Configure Cloudflare R2 (Optional)**:
   - Add repository variables:
     - `CLOUDFLARE_R2_ENABLED=true`
     - `CLOUDFLARE_R2_BUCKET=your-bucket-name`
     - `CLOUDFLARE_R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com`
   - Add repository secrets:
     - `CLOUDFLARE_R2_ACCESS_KEY`
     - `CLOUDFLARE_R2_SECRET_KEY`

3. **Schedule**: Runs automatically every hour at :15 minutes past the hour

### Manual Triggering

You can manually trigger collection via GitHub Actions with custom parameters:
- **Regions**: Specify which regions to collect from
- **Categories**: Specify which categories to include
- **Max Results**: Limit results per API request

## 📊 Analytics & Monitoring

### Quota Management

The system automatically tracks API quota usage and rotates between API keys:

```python
# Check current quota status
quota = collector.get_quota_status()
print(f"Quota used: {quota['quota_used_today']}/{quota['quota_limit']}")
```

### Collection Statistics

Every collection run generates comprehensive statistics:

- **Performance Metrics**: Processing time, success rate, error count
- **API Usage**: Requests made, quota consumed, key rotation events
- **Data Quality**: Videos collected per region/category
- **Historical Trends**: Compare performance over time

### Error Handling

- **API Rate Limits**: Automatic key rotation and retry logic
- **Network Issues**: Exponential backoff and retry strategies  
- **Data Validation**: Comprehensive error logging and recovery
- **Monitoring**: Integration with GitHub Actions status reporting

## 🔧 Advanced Configuration

### Custom Collection Settings

```python
collector = TrendingDataCollector(
    api_keys=["key1", "key2", "key3"],
    db_path="custom_trending.db",
    data_dir="/custom/data/path"
)

# Custom collection with specific parameters
results = await collector.collect_trending_data(
    regions=['US', 'GB'],
    categories=['10', '24'],  # Music, Entertainment
    max_results_per_request=25
)
```

### Database Queries

```python
from sqlmodel import select, Session
from collect_trending import TrendingVideo

# Query trending videos
with Session(collector.engine) as session:
    # Top videos by view count in last 7 days
    statement = select(TrendingVideo).where(
        TrendingVideo.collected_at >= cutoff_date
    ).order_by(TrendingVideo.view_count.desc()).limit(10)
    
    top_videos = session.exec(statement).all()
```

### Export & Analysis

```python
# Export data for analysis
import pandas as pd

# Load data into DataFrame
df = pd.read_sql_query("""
    SELECT video_id, title, region_code, category_name,
           view_count, engagement_rate, trending_rank
    FROM trending_videos 
    WHERE collected_at >= datetime('now', '-7 days')
""", collector.engine)

# Analyze engagement by category
category_stats = df.groupby('category_name').agg({
    'engagement_rate': ['mean', 'std'],
    'view_count': ['mean', 'median']
}).round(2)
```

## 🚦 System Requirements

- **Python**: 3.10+
- **Memory**: 1GB+ recommended for large collections
- **Storage**: ~100MB per day of JSON data
- **Network**: Stable internet for API requests
- **YouTube API Quota**: 10,000 units/day per key (recommend 2-3 keys)

## 📈 Performance Benchmarks

Typical collection performance:
- **3 regions × 5 categories × 50 videos**: ~450 videos in 2-3 minutes
- **All regions × All categories × 25 videos**: ~7,000+ videos in 15-20 minutes
- **API Requests**: ~1 request per region-category combination
- **Quota Usage**: ~1-2 quota units per request

## 🛟 Troubleshooting

### Common Issues

1. **No API Keys Found**
   ```bash
   ❌ No YouTube API keys found in environment variables
   💡 Set YOUTUBE_API_KEY or YOUTUBE_API_KEY_1, YOUTUBE_API_KEY_2, etc.
   ```
   **Solution**: Export your API key as environment variable

2. **Quota Exceeded**
   ```bash
   ⚠️ Quota exceeded for US/10
   🔄 Rotated to API key #2
   ```
   **Solution**: Add multiple API keys for automatic rotation

3. **Invalid Regions/Categories**
   ```bash
   ⚠️ Invalid regions: ['XX']
   Valid regions: US, GB, CA, AU, DE, FR, ES, IT, JP, KR, BR, MX, IN, RU, NL, SE, NO, DK, FI, PL
   ```
   **Solution**: Use `trending_cli.py list-regions` to see valid codes

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import asyncio; from collect_trending import main; asyncio.run(main())"
```

## 🔄 Integration Examples

### Data Pipeline Integration

```python
# Custom processing pipeline
async def process_trending_data():
    collector = TrendingDataCollector(api_keys=["your-key"])
    
    # Collect data
    results = await collector.collect_trending_data()
    
    # Process collected videos
    with Session(collector.engine) as session:
        recent_videos = session.exec(
            select(TrendingVideo).where(
                TrendingVideo.collection_batch == results['batch_id']
            )
        ).all()
        
        # Send to analytics system
        for video in recent_videos:
            send_to_analytics(video.dict())
```

### Webhook Integration

```python
# Notify external systems on completion
import requests

async def collect_with_webhook():
    results = await collector.collect_trending_data()
    
    # Send webhook notification
    webhook_data = {
        'event': 'collection_complete',
        'batch_id': results['batch_id'],
        'videos_collected': results['total_videos_collected'],
        'success_rate': results['success_rate']
    }
    
    requests.post('https://your-webhook.com/trending', json=webhook_data)
```

## 📜 License & Contributing

This project is part of the OmniSphere system. See the main repository for license and contribution guidelines.

---

🔥 **Ready to collect trending data?** Start with `python trending_cli.py collect` and watch the magic happen!
