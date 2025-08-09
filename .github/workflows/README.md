# 🚀 CI/CD Workflows Overview

This directory contains the complete CI/CD pipeline for the automated video generation system.

## 📋 Workflow Matrix

### 🔄 Main Orchestration
- **`video-pipeline-matrix.yml`** - Main matrix workflow orchestrating all components
  - Triggers: Schedule, manual, push, workflow completion
  - Features: Job dependency management, matrix strategies, conditional execution

### 📊 Data Collection  
- **`collect-trending-data.yml`** - YouTube trending data collection (hourly)
- **`collect-analytics.yml`** - YouTube Analytics data collection (daily)

### 🎬 Content Generation
- **`youtube-upload.yml`** - Video upload and scheduling system

### 🔧 Reusable Components
- **`reusable-setup.yml`** - Python environment setup with dependency caching
- **`reusable-notify.yml`** - Slack/Discord webhook notifications

## 🎯 Key Features

### ✅ Dependency Caching
- Automatic pip dependency caching using `actions/cache`
- Cache keys based on requirements file hashes
- Significant speed improvements for subsequent runs

### 📢 Webhook Notifications  
- Rich Slack notifications with workflow status
- Discord embed support with color-coded status
- Fallback GitHub step summaries when webhooks unavailable

### 🔀 Matrix Strategies
- Parallel video content generation (trending_analysis, tech_news, market_insights)
- Configurable max-parallel execution (default: 2)
- Fail-fast disabled for robustness

### ⚡ Smart Triggers
- **Hourly**: Trending data collection (15 minutes past each hour)
- **Daily**: Analytics collection (2:00 AM UTC)  
- **Push**: Video uploads on new content in `data/scripts/**` or `generated_videos/**`
- **Workflow completion**: Video creation after successful trending collection

### 🛡️ Error Handling & Retry
- Exponential backoff retry logic for API calls
- Quota management with automatic API key rotation
- Comprehensive error logging and reporting

## 📈 Monitoring Dashboard

Each workflow provides:
- **Real-time logs** in GitHub Actions interface
- **Step summaries** with key metrics and results
- **Artifact uploads** (databases, logs, reports) with 30-day retention
- **Database commits** automatically pushed to repository
- **Rich notifications** to Slack/Discord channels

## 🔐 Security & Secrets

Required repository secrets:
```
YOUTUBE_API_KEY_1, YOUTUBE_API_KEY_2, YOUTUBE_API_KEY_3
GOOGLE_OAUTH_CREDENTIALS, GOOGLE_REFRESH_TOKEN  
OPENAI_API_KEY
SLACK_WEBHOOK_URL, DISCORD_WEBHOOK_URL (optional)
```

## 🎮 Usage

### Manual Triggers
Access via GitHub Actions tab → Select workflow → "Run workflow" button

### Bulk Operations
```yaml
# Full pipeline execution
operation: "full_pipeline"

# Individual components  
operation: "collect_trending"
operation: "create_video"  
operation: "upload_video"
operation: "collect_analytics"
```

### Dry Run Mode
```yaml
# Test without actual uploads
dry_run: true
```

## 📚 Documentation

See [`docs/CI-CD-SETUP.md`](../../docs/CI-CD-SETUP.md) for complete setup instructions and troubleshooting guide.

---

*This workflow system provides enterprise-grade automation for the video generation pipeline with comprehensive monitoring, error handling, and notification capabilities.*
