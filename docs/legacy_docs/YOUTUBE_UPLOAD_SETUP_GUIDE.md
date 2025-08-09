# 🚀 YouTube Upload Automation Setup Guide

This guide covers the complete setup and usage of the automated YouTube upload system integrated with Omnisphere.

## 📋 Overview

The YouTube upload automation system provides:

- **Automated uploads** with retry logic and exponential backoff
- **Scheduled publishing** with precise timing control  
- **Database tracking** of all uploads with returned videoId
- **Error handling** for 403/500 errors with intelligent retry delays
- **Playlist management** for organizing uploaded content
- **Revenue tracking integration** with the existing Omnisphere system
- **GitHub Actions integration** for CI/CD workflows

## 🔧 Prerequisites

### Required Tools & APIs

1. **YouTube Data API v3** - For uploading videos
2. **Google OAuth 2.0 Credentials** - For authentication
3. **youtube-upload CLI** - Open-source upload tool
4. **Python 3.10+** - Runtime environment
5. **GitHub Repository** - For Actions automation

### Required Python Packages

```bash
pip install youtube-upload google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests retrying sqlalchemy python-dateutil moviepy
```

## 🗝️ Authentication Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **YouTube Data API v3**
4. Go to **APIs & Services > Credentials**

### Step 2: Create OAuth 2.0 Credentials  

1. Click **Create Credentials > OAuth 2.0 Client IDs**
2. Choose **Desktop application** 
3. Download the credentials JSON file
4. Rename to `oauth_credentials.json`

### Step 3: Obtain Refresh Token

Run the OAuth flow once to get a refresh token:

```bash
# Install youtube-upload if not already installed
pip install youtube-upload

# Run initial OAuth flow (interactive)
youtube-upload --client-secrets oauth_credentials.json --privacy private test_video.mp4

# This will open a browser for OAuth consent
# After completion, credentials are saved automatically
```

### Step 4: Setup GitHub Secrets

Add these secrets to your GitHub repository:

- **`GOOGLE_OAUTH_CREDENTIALS`** - Contents of `oauth_credentials.json`
- **`GOOGLE_REFRESH_TOKEN`** - Contents of generated refresh token file
- **`SLACK_WEBHOOK_URL`** (optional) - For error notifications

```bash
# Get the contents for GitHub secrets
cat oauth_credentials.json | base64  # Use raw JSON, not base64
cat ~/.youtube-upload-credentials.json  # This is your refresh token
```

## 💾 Database Schema

The system creates comprehensive tracking tables:

### youtube_uploads (Main table)
- **video_id** - YouTube video ID (primary output)
- **video_url** - Full YouTube URL  
- **local_video_path** - Original video file
- **title, description, tags** - Video metadata
- **privacy_status** - public, private, unlisted
- **scheduled_publish_time** - When to publish
- **upload_status** - pending, processing, completed, failed
- **view_count, like_count** - Performance metrics
- **estimated_revenue** - Revenue tracking
- **upload_attempts** - Retry tracking

### upload_sessions (Retry tracking)
- **session_start/end** - Timing data
- **error_type** - quota_exceeded, rate_limited, etc.
- **retry_delay_seconds** - Calculated backoff time

### video_analytics (Historical performance)
- **metrics_date** - Date of measurement
- **views, likes, comments** - Performance data
- **estimated_revenue** - Revenue over time

## 🎬 Usage Examples

### Manual Upload via GitHub Actions

Trigger the workflow manually with parameters:

```yaml
# Via GitHub web interface or API
POST /repos/{owner}/{repo}/actions/workflows/youtube-upload.yml/dispatches
{
  "ref": "main",
  "inputs": {
    "video_file": "generated_videos/my_video.mp4",
    "thumbnail_file": "thumbnails/my_thumbnail.jpg", 
    "title": "My Awesome Video Title",
    "description": "Detailed video description with keywords",
    "tags": "tag1,tag2,tag3",
    "privacy": "public",
    "scheduled_time": "2024-01-15 14:00",
    "playlist_id": "PLxxxxxxxxxxxxxxx",
    "retry_count": 3
  }
}
```

### Programmatic Usage

```python
from core.youtube_upload_manager import YouTubeUploadManager, UploadRequest

# Initialize manager
upload_manager = YouTubeUploadManager(
    oauth_credentials_path="oauth_credentials.json",
    refresh_token_path="refresh_token.json",
    max_retries=3
)

# Create upload request
request = UploadRequest(
    video_file="path/to/video.mp4",
    thumbnail_file="path/to/thumbnail.jpg",
    title="My Video Title", 
    description="Video description with keywords",
    tags=["youtube", "automation", "ai"],
    privacy="public",
    scheduled_time=datetime(2024, 1, 15, 14, 0),  # Optional
    playlist_id="PLxxxxxxxxxxxxxxx"  # Optional
)

# Schedule upload
upload_id = upload_manager.schedule_upload(request)

# Upload immediately  
result = upload_manager.upload_video(upload_id)

if result.success:
    print(f"✅ Uploaded! Video ID: {result.video_id}")
    print(f"URL: {result.video_url}")
else:
    print(f"❌ Failed: {result.error_message}")
```

### Integration with Video Pipeline

```python
from core.video_automation_pipeline import VideoAutomationPipeline
from core.youtube_upload_manager import YouTubeUploadManager, UploadRequest

# Create video
pipeline = VideoAutomationPipeline()
project = pipeline.create_video_from_script({
    "title": "AI Revolution 2024",
    "script": "Your engaging script here...",
    "niche": "technology"
})

# Upload to YouTube
upload_manager = YouTubeUploadManager()
request = UploadRequest(
    video_file=f"generated_videos/{project.project_id}_final.mp4",
    thumbnail_file=project.thumbnail,
    title=project.title,
    description=project.description,
    tags=project.tags,
    privacy="public"
)

upload_id = upload_manager.schedule_upload(request)
result = upload_manager.upload_video(upload_id)

print(f"Video created and uploaded: {result.video_url}")
```

## 🔄 Retry Logic & Error Handling

### Automatic Retry Strategy

The system uses intelligent retry logic with exponential backoff:

```python
@retry(
    stop_max_attempt_number=3,
    wait_exponential_multiplier=2000,     # Start with 2 seconds
    wait_exponential_max=300000,          # Max 5 minutes between retries  
    retry_on_exception=lambda ex: isinstance(ex, (subprocess.CalledProcessError, requests.RequestException))
)
```

### Error Classification & Delays

| Error Type | Delay | Retry? | Description |
|------------|-------|--------|-------------|
| quota_exceeded | 1 hour | ✅ | API quota limit hit |
| rate_limited | 5 minutes | ✅ | Rate limit exceeded |
| server_error | 2 minutes | ✅ | YouTube server issues |
| service_unavailable | 3 minutes | ✅ | Service temporarily down |
| network_error | 1 minute | ✅ | Connection problems |
| authentication_failed | No retry | ❌ | OAuth issues |
| file_error | No retry | ❌ | Missing/corrupt files |

### Manual Error Recovery

Check failed uploads:

```python
# Get upload statistics
stats = upload_manager.get_upload_statistics(days=7)
print(f"Failed uploads: {stats['status_breakdown']}")

# Retry specific upload
result = upload_manager.upload_video(upload_id=123)
```

## 📊 Monitoring & Analytics

### Upload Statistics

```python
# Get comprehensive stats
stats = upload_manager.get_upload_statistics(days=30)

print(f"Success rate: {stats['performance']['success_rate']:.1%}")
print(f"Total views: {stats['performance']['total_views']:,}")
print(f"Estimated revenue: ${stats['performance']['total_estimated_revenue']:,.2f}")
```

### Database Queries

```sql
-- Recent uploads
SELECT title, video_id, upload_status, created_at 
FROM youtube_uploads 
WHERE created_at >= datetime('now', '-7 days')
ORDER BY created_at DESC;

-- Failed uploads needing attention  
SELECT title, error_message, upload_attempts, last_attempt_time
FROM youtube_uploads 
WHERE upload_status = 'failed' 
AND upload_attempts >= 3;

-- Performance analytics
SELECT 
    DATE(created_at) as upload_date,
    COUNT(*) as videos_uploaded,
    SUM(view_count) as total_views,
    AVG(engagement_rate) as avg_engagement
FROM youtube_uploads 
WHERE upload_status = 'completed'
GROUP BY DATE(created_at)
ORDER BY upload_date DESC;
```

### GitHub Actions Monitoring

The workflow provides detailed reporting:

- **Step summaries** with upload results
- **Artifact uploads** of database and logs  
- **Slack notifications** on failures
- **Database commits** for tracking persistence

## ⏰ Scheduling System

### Automated Batch Processing

The system runs every hour to check for scheduled uploads:

```yaml
schedule:
  - cron: '0 * * * *'  # Every hour
```

### Scheduling Videos

```python
# Schedule for future publication
request = UploadRequest(
    video_file="video.mp4",
    title="Scheduled Video",
    scheduled_time=datetime(2024, 1, 15, 14, 0)  # Jan 15, 2PM
)

upload_id = upload_manager.schedule_upload(request)
# Video will be uploaded automatically at scheduled time
```

### Batch Upload Processing

```python
# Process up to 5 pending uploads
results = upload_manager.batch_upload(max_uploads=5)

print(f"Processed: {results['total']}")
print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")
```

## 🎯 Best Practices

### File Organization

```
project/
├── generated_videos/          # Video outputs
│   ├── video_123_final.mp4
│   └── video_124_final.mp4
├── thumbnails/               # Thumbnail images  
│   ├── thumb_123.jpg
│   └── thumb_124.jpg
├── oauth_credentials.json    # OAuth config
├── refresh_token.json       # Refresh token
└── youtube_uploads.db       # Upload database
```

### Title & Description Optimization

```python
# Optimized title (under 60 characters)
title = "AI Revolution 2024: 5 Changes That Will Shock You"

# SEO-optimized description
description = """
🤖 The AI revolution is happening faster than expected! 

In this video, I reveal 5 groundbreaking changes coming in 2024 that will transform everything from work to daily life.

⏰ TIMESTAMPS:
00:00 - Introduction
01:30 - Change #1: AI Assistants
03:45 - Change #2: Automation
06:20 - Change #3: Creative AI
08:15 - Change #4: Job Market
10:30 - Change #5: Education

🔗 RESOURCES:
- AI Tools List: https://example.com/ai-tools
- Newsletter: https://example.com/newsletter

#AI #Technology #Future #2024 #Automation
"""

# Strategic tags (max 500 characters total)
tags = [
    "artificial intelligence", "AI 2024", "future technology",
    "automation", "machine learning", "tech trends",
    "digital transformation", "innovation"
]
```

### Upload Timing Strategy

```python
from datetime import datetime, timedelta

# Optimal upload times (research-based)
optimal_times = {
    "monday": datetime(2024, 1, 15, 14, 0),    # 2 PM EST
    "tuesday": datetime(2024, 1, 16, 15, 0),   # 3 PM EST  
    "wednesday": datetime(2024, 1, 17, 14, 0), # 2 PM EST
    "thursday": datetime(2024, 1, 18, 15, 0),  # 3 PM EST
    "friday": datetime(2024, 1, 19, 12, 0),    # 12 PM EST
}

# Schedule uploads strategically
for day, time in optimal_times.items():
    request = UploadRequest(
        video_file=f"videos/{day}_video.mp4",
        title=f"Weekly {day.title()} Content",
        scheduled_time=time
    )
    upload_manager.schedule_upload(request)
```

## 🚨 Troubleshooting

### Common Issues

#### 1. OAuth Authentication Failed

```bash
# Error: 401 Unauthorized
# Solution: Regenerate refresh token
youtube-upload --client-secrets oauth_credentials.json --privacy private test.mp4
```

#### 2. Quota Exceeded (403 Error)

```python
# Check current quota usage
stats = upload_manager.get_upload_statistics(days=1)
failed_quotas = [s for s in stats['status_breakdown'] if 'quota' in s['status']]

# Wait for quota reset (midnight Pacific Time)
# Or use multiple API keys with rotation
```

#### 3. File Not Found Errors

```python
# Verify file exists before upload
import os

video_file = "path/to/video.mp4"
if not os.path.exists(video_file):
    print(f"❌ Video file not found: {video_file}")
else:
    print(f"✅ File exists: {os.path.getsize(video_file)} bytes")
```

#### 4. Upload Timeouts

```python
# Check file size (YouTube limit: 256 GB)
file_size_gb = os.path.getsize(video_file) / (1024**3)
if file_size_gb > 128:  # Conservative limit
    print(f"⚠️ Large file ({file_size_gb:.1f} GB) may timeout")
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed command execution
upload_manager = YouTubeUploadManager()
result = upload_manager.upload_video(upload_id)
```

### Testing Uploads

Use private uploads for testing:

```python
# Test upload (private, won't affect channel)
test_request = UploadRequest(
    video_file="test_video.mp4",
    title="Test Upload - Please Ignore",
    description="This is a test upload for system validation",
    tags=["test"],
    privacy="private"  # Won't be public
)
```

## 📈 Revenue Integration

The system automatically integrates with revenue tracking:

```python
# Revenue tracking is initialized automatically
# Check revenue for uploaded videos
video = upload_manager.get_video_by_id("dQw4w9WgXcQ")
print(f"Estimated revenue: ${video['estimated_revenue']:.2f}")

# Update analytics from YouTube API
analytics_data = {
    "view_count": 50000,
    "like_count": 1200,
    "comment_count": 89,
    "engagement_rate": 2.4,
    "estimated_revenue": 125.50
}
upload_manager.update_video_analytics("dQw4w9WgXcQ", analytics_data)
```

## 🔗 API Integration

### Webhook Notifications

Set up webhooks for upload completion:

```python
# Add webhook after successful upload
if result.success:
    webhook_url = "https://your-site.com/api/video-uploaded"
    requests.post(webhook_url, json={
        "video_id": result.video_id,
        "video_url": result.video_url,
        "title": request.title,
        "upload_time": datetime.now().isoformat()
    })
```

### External System Integration

```python
# Integration with CRM/Analytics
class AnalyticsIntegration:
    def on_upload_success(self, result: UploadResult):
        # Send to Google Analytics
        self.track_event("video_uploaded", {
            "video_id": result.video_id,
            "upload_duration": result.upload_duration
        })
        
        # Update CRM
        self.update_crm_record(result.video_id)
        
        # Trigger email sequence
        self.start_email_sequence(result.video_url)
```

## 💡 Advanced Features

### Multi-Channel Support

```python
# Different credentials for different channels
channel_configs = {
    "main_channel": {
        "oauth_path": "main_oauth.json",
        "refresh_path": "main_refresh.json"
    },
    "secondary_channel": {
        "oauth_path": "secondary_oauth.json", 
        "refresh_path": "secondary_refresh.json"
    }
}

# Upload to specific channel
main_manager = YouTubeUploadManager(**channel_configs["main_channel"])
secondary_manager = YouTubeUploadManager(**channel_configs["secondary_channel"])
```

### Playlist Automation

```python
# Automatically organize uploads into playlists
playlist_rules = {
    "ai_content": "PLxxxxxxxxxxxxxxx",
    "tutorials": "PLyyyyyyyyyyyyyyy",
    "reviews": "PLzzzzzzzzzzzzzzz"
}

def get_playlist_for_content(title, tags):
    if "AI" in title or "artificial intelligence" in tags:
        return playlist_rules["ai_content"]
    elif "tutorial" in title.lower() or "how to" in title.lower():
        return playlist_rules["tutorials"]
    elif "review" in title.lower():
        return playlist_rules["reviews"]
    return None

# Use in upload request
playlist_id = get_playlist_for_content(request.title, request.tags)
request.playlist_id = playlist_id
```

## 📚 Additional Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [YouTube Upload Policies](https://support.google.com/youtube/answer/71673)
- [YouTube-Upload CLI GitHub](https://github.com/tokland/youtube-upload)
- [Google OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)

## 🎯 Success Metrics

Track these KPIs for upload automation:

- **Upload Success Rate** - Target: >95%
- **Average Upload Time** - Target: <10 minutes
- **Error Recovery Rate** - Target: >90% after retries
- **Scheduled Accuracy** - Target: Within 5 minutes of scheduled time
- **Revenue Per Upload** - Track growth over time

---

This system provides enterprise-grade YouTube upload automation with comprehensive tracking, intelligent retry logic, and seamless integration with the Omnisphere video creation pipeline. The returned `videoId` from each upload is stored in the database for complete tracking and revenue attribution.
