#!/usr/bin/env python3
"""
🎬 YOUTUBE UPLOAD MANAGER 🎬
Complete integration of YouTube upload functionality into Omnisphere pipeline

This module provides:
1. Direct integration with video automation pipeline
2. Database tracking of uploaded videos with videoId
3. Retry logic with exponential backoff
4. Batch upload scheduling and management
5. Integration with existing revenue tracking system
"""

import os
import json
import time
import sqlite3
import subprocess
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import requests
from retrying import retry

# Try to import existing components
try:
    from .real_revenue_tracker import RealRevenueTracker
except ImportError:
    RealRevenueTracker = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UploadRequest:
    """Represents a YouTube upload request"""
    video_file: str
    thumbnail_file: Optional[str]
    title: str
    description: str
    tags: List[str]
    privacy: str = "public"  # public, private, unlisted
    scheduled_time: Optional[datetime] = None
    playlist_id: Optional[str] = None
    category_id: str = "28"  # Science & Technology by default

@dataclass
class UploadResult:
    """Result of a YouTube upload operation"""
    success: bool
    video_id: Optional[str]
    video_url: Optional[str]
    error_message: Optional[str]
    attempt_count: int
    upload_duration: float

class YouTubeUploadManager:
    """
    Manages YouTube video uploads with comprehensive tracking and retry logic
    Integrates with Omnisphere's video automation pipeline
    """
    
    def __init__(self, 
                 oauth_credentials_path: str = "oauth_credentials.json",
                 refresh_token_path: str = "refresh_token.json",
                 db_path: str = "youtube_uploads.db",
                 max_retries: int = 3):
        
        self.oauth_credentials_path = oauth_credentials_path
        self.refresh_token_path = refresh_token_path
        self.db_path = db_path
        self.max_retries = max_retries
        
        # Initialize database
        self.setup_database()
        
        # Initialize revenue tracker if available
        self.revenue_tracker = None
        if RealRevenueTracker:
            try:
                self.revenue_tracker = RealRevenueTracker()
            except Exception as e:
                logger.warning(f"Could not initialize revenue tracker: {e}")
        
        logger.info("✅ YouTube Upload Manager initialized")
    
    def setup_database(self):
        """Setup comprehensive database schema for upload tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main uploads table with all video metadata
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS youtube_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- YouTube identifiers
            video_id TEXT UNIQUE,                    -- YouTube video ID (the key output)
            video_url TEXT,                         -- Full YouTube URL
            
            -- Local file information
            local_video_path TEXT NOT NULL,         -- Path to original video file
            local_thumbnail_path TEXT,              -- Path to thumbnail file
            file_size_bytes INTEGER,                -- Video file size
            duration_seconds REAL,                  -- Video duration
            
            -- Video metadata
            title TEXT NOT NULL,
            description TEXT,
            tags TEXT,                              -- JSON array of tags
            category_id TEXT DEFAULT '28',          -- YouTube category ID
            privacy_status TEXT DEFAULT 'public',   -- public, private, unlisted
            
            -- Scheduling and playlist
            scheduled_publish_time DATETIME,        -- When to publish (NULL = immediate)
            playlist_id TEXT,                      -- Playlist to add video to
            
            -- Upload tracking
            upload_status TEXT DEFAULT 'pending',   -- pending, processing, completed, failed, scheduled
            upload_attempts INTEGER DEFAULT 0,
            last_attempt_time DATETIME,
            upload_start_time DATETIME,
            upload_complete_time DATETIME,
            upload_duration_seconds REAL,
            
            -- Error tracking
            error_code TEXT,
            error_message TEXT,
            retry_after_seconds INTEGER,
            
            -- Performance tracking (updated later via API)
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            watch_time_minutes REAL DEFAULT 0.0,
            engagement_rate REAL DEFAULT 0.0,
            
            -- Revenue tracking integration
            estimated_revenue REAL DEFAULT 0.0,
            actual_revenue REAL DEFAULT 0.0,
            revenue_last_updated DATETIME,
            
            -- Timestamps
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Upload sessions table for detailed retry tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS upload_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_end DATETIME,
            attempt_number INTEGER,
            session_status TEXT,               -- started, completed, failed, timeout, cancelled
            error_type TEXT,                   -- quota_exceeded, rate_limited, server_error, etc.
            error_details TEXT,
            retry_delay_seconds INTEGER,
            upload_progress_percent REAL,     -- Progress when session ended
            bandwidth_mbps REAL,              -- Upload speed achieved
            
            FOREIGN KEY (upload_id) REFERENCES youtube_uploads (id)
        )
        ''')
        
        # Video analytics tracking (separate table for historical data)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            video_id TEXT,
            
            -- Performance metrics
            views INTEGER,
            likes INTEGER,
            comments INTEGER,
            shares INTEGER,
            watch_time_minutes REAL,
            average_view_duration_seconds REAL,
            click_through_rate REAL,
            
            -- Revenue data
            estimated_revenue REAL,
            ad_revenue REAL,
            channel_revenue REAL,
            
            -- Date of metrics
            metrics_date DATE,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (upload_id) REFERENCES youtube_uploads (id)
        )
        ''')
        
        # Playlist management
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlist_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            playlist_id TEXT,
            playlist_title TEXT,
            position_in_playlist INTEGER,
            assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            assignment_status TEXT DEFAULT 'pending',  -- pending, completed, failed
            
            FOREIGN KEY (upload_id) REFERENCES youtube_uploads (id)
        )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_id ON youtube_uploads (video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_upload_status ON youtube_uploads (upload_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scheduled_time ON youtube_uploads (scheduled_publish_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON youtube_uploads (created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_upload_attempts ON youtube_uploads (upload_attempts)')
        
        # Create analytics indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_video_id ON video_analytics (video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_date ON video_analytics (metrics_date)')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database schema setup complete")
    
    def schedule_upload(self, request: UploadRequest) -> int:
        """
        Schedule a video for upload (adds to database, doesn't upload immediately)
        Returns the upload record ID for tracking
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get file information
        file_size = 0
        duration = 0.0
        if os.path.exists(request.video_file):
            file_size = os.path.getsize(request.video_file)
            duration = self._get_video_duration(request.video_file)
        
        # Insert upload request
        cursor.execute('''
        INSERT INTO youtube_uploads (
            local_video_path, local_thumbnail_path, file_size_bytes, duration_seconds,
            title, description, tags, category_id, privacy_status,
            scheduled_publish_time, playlist_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.video_file,
            request.thumbnail_file,
            file_size,
            duration,
            request.title,
            request.description,
            json.dumps(request.tags),
            request.category_id,
            request.privacy,
            request.scheduled_time,
            request.playlist_id
        ))
        
        upload_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Upload scheduled with ID: {upload_id}")
        logger.info(f"   Title: {request.title}")
        logger.info(f"   File: {request.video_file}")
        logger.info(f"   Scheduled: {request.scheduled_time or 'Immediate'}")
        
        return upload_id
    
    @retry(
        stop_max_attempt_number=3,
        wait_exponential_multiplier=2000,     # Start with 2 seconds
        wait_exponential_max=300000,          # Max 5 minutes between retries
        retry_on_exception=lambda ex: isinstance(ex, (subprocess.CalledProcessError, requests.RequestException))
    )
    def upload_video(self, upload_id: int) -> UploadResult:
        """
        Upload a video to YouTube with comprehensive retry logic and error handling
        """
        start_time = time.time()
        
        # Get upload record
        upload_data = self._get_upload_record(upload_id)
        if not upload_data:
            return UploadResult(False, None, None, f"Upload record {upload_id} not found", 0, 0.0)
        
        logger.info(f"🚀 Starting upload for: {upload_data['title']}")
        
        # Check if already completed
        if upload_data['upload_status'] == 'completed':
            logger.info(f"✅ Upload already completed: {upload_data['video_id']}")
            return UploadResult(
                True, 
                upload_data['video_id'], 
                upload_data['video_url'], 
                None, 
                upload_data['upload_attempts'], 
                0.0
            )
        
        # Check if scheduled time has arrived
        if upload_data['scheduled_publish_time']:
            scheduled = datetime.fromisoformat(upload_data['scheduled_publish_time'])
            if datetime.now() < scheduled:
                logger.info(f"⏰ Upload scheduled for {scheduled}, not yet time")
                return UploadResult(False, None, None, "Upload time not yet reached", 0, 0.0)
        
        # Create upload session
        session_id = self._create_upload_session(upload_id, upload_data['upload_attempts'] + 1)
        
        try:
            # Update status to processing
            self._update_upload_status(upload_id, 'processing')
            
            # Build upload command
            upload_cmd = self._build_upload_command(upload_data)
            
            logger.info("🎬 Executing YouTube upload...")
            logger.debug(f"Command (truncated): {' '.join(upload_cmd[:5])}...")
            
            # Execute upload with timeout
            result = subprocess.run(
                upload_cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
                check=True
            )
            
            # Extract video ID from output
            video_id = self._extract_video_id(result.stdout)
            
            if video_id:
                # Calculate upload duration
                upload_duration = time.time() - start_time
                
                # Update database with success
                self._update_upload_success(upload_id, video_id, session_id, upload_duration)
                
                # Add to playlist if specified
                if upload_data['playlist_id']:
                    self._add_to_playlist(upload_id, video_id, upload_data['playlist_id'])
                
                # Initialize revenue tracking
                if self.revenue_tracker:
                    self._initialize_revenue_tracking(upload_id, video_id, upload_data)
                
                video_url = f"https://youtube.com/watch?v={video_id}"
                logger.info(f"✅ Upload successful! Video ID: {video_id}")
                logger.info(f"   URL: {video_url}")
                logger.info(f"   Duration: {upload_duration:.1f}s")
                
                return UploadResult(True, video_id, video_url, None, upload_data['upload_attempts'] + 1, upload_duration)
            
            else:
                raise Exception("Failed to extract video ID from upload response")
        
        except subprocess.TimeoutExpired:
            error_msg = "Upload timeout after 30 minutes"
            upload_duration = time.time() - start_time
            logger.error(f"❌ {error_msg}")
            
            self._update_upload_failure(upload_id, session_id, "TIMEOUT", error_msg, 3600)  # 1 hour retry delay
            return UploadResult(False, None, None, error_msg, upload_data['upload_attempts'] + 1, upload_duration)
        
        except subprocess.CalledProcessError as e:
            error_msg = f"Upload failed: {e.stderr or e.stdout or str(e)}"
            upload_duration = time.time() - start_time
            
            # Parse error for appropriate retry delay
            retry_delay = self._parse_error_for_retry_delay(e.stderr or e.stdout or str(e))
            error_type = self._classify_error_type(e.stderr or e.stdout or str(e))
            
            logger.error(f"❌ {error_msg}")
            logger.info(f"   Error type: {error_type}")
            logger.info(f"   Retry delay: {retry_delay}s")
            
            self._update_upload_failure(upload_id, session_id, str(e.returncode), error_msg, retry_delay, error_type)
            
            # Don't retry immediately on certain errors
            if error_type in ['quota_exceeded', 'authentication_failed']:
                logger.info(f"   Not retrying due to error type: {error_type}")
            
            return UploadResult(False, None, None, error_msg, upload_data['upload_attempts'] + 1, upload_duration)
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            upload_duration = time.time() - start_time
            logger.error(f"❌ {error_msg}")
            
            self._update_upload_failure(upload_id, session_id, "UNKNOWN", error_msg, 300)  # 5 minute retry delay
            return UploadResult(False, None, None, error_msg, upload_data['upload_attempts'] + 1, upload_duration)
    
    def batch_upload(self, max_uploads: int = 5) -> Dict[str, Any]:
        """
        Process a batch of pending uploads
        Returns summary of upload results
        """
        logger.info(f"📊 Starting batch upload (max {max_uploads} videos)")
        
        # Get pending uploads
        pending_uploads = self._get_pending_uploads(max_uploads)
        
        if not pending_uploads:
            logger.info("📭 No pending uploads found")
            return {"total": 0, "successful": 0, "failed": 0, "results": []}
        
        logger.info(f"📋 Found {len(pending_uploads)} pending uploads")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for upload_data in pending_uploads:
            upload_id = upload_data['id']
            title = upload_data['title']
            
            try:
                logger.info(f"🎬 Processing: {title}")
                result = self.upload_video(upload_id)
                
                if result.success:
                    successful_count += 1
                    logger.info(f"✅ Success: {title} -> {result.video_id}")
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed: {title} - {result.error_message}")
                
                results.append({
                    "upload_id": upload_id,
                    "title": title,
                    "success": result.success,
                    "video_id": result.video_id,
                    "video_url": result.video_url,
                    "error_message": result.error_message,
                    "upload_duration": result.upload_duration
                })
                
                # Rate limiting between uploads to avoid hitting limits
                if failed_count == 0 and len(pending_uploads) > 1:
                    time.sleep(10)  # 10 second delay between successful uploads
                elif failed_count > 0:
                    time.sleep(30)  # 30 second delay after failures
                    
            except Exception as e:
                failed_count += 1
                error_msg = f"Batch upload error: {str(e)}"
                logger.error(f"❌ {error_msg}")
                
                results.append({
                    "upload_id": upload_id,
                    "title": title,
                    "success": False,
                    "video_id": None,
                    "video_url": None,
                    "error_message": error_msg,
                    "upload_duration": 0.0
                })
        
        summary = {
            "total": len(pending_uploads),
            "successful": successful_count,
            "failed": failed_count,
            "results": results
        }
        
        logger.info(f"📊 Batch upload complete:")
        logger.info(f"   Total processed: {summary['total']}")
        logger.info(f"   Successful: {summary['successful']}")
        logger.info(f"   Failed: {summary['failed']}")
        logger.info(f"   Success rate: {(successful_count/len(pending_uploads)*100):.1f}%")
        
        return summary
    
    def get_upload_status(self, upload_id: int) -> Optional[Dict]:
        """Get detailed status of an upload"""
        return self._get_upload_record(upload_id)
    
    def get_video_by_id(self, video_id: str) -> Optional[Dict]:
        """Get upload record by YouTube video ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM youtube_uploads WHERE video_id = ?', (video_id,))
        result = cursor.fetchone()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        
        conn.close()
        return None
    
    def update_video_analytics(self, video_id: str, analytics_data: Dict):
        """Update video analytics from YouTube API data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update main video record
        cursor.execute('''
        UPDATE youtube_uploads 
        SET view_count = ?, like_count = ?, comment_count = ?, 
            engagement_rate = ?, updated_at = CURRENT_TIMESTAMP
        WHERE video_id = ?
        ''', (
            analytics_data.get('view_count', 0),
            analytics_data.get('like_count', 0),
            analytics_data.get('comment_count', 0),
            analytics_data.get('engagement_rate', 0.0),
            video_id
        ))
        
        # Insert historical analytics record
        cursor.execute('''
        INSERT INTO video_analytics (
            upload_id, video_id, views, likes, comments, shares,
            watch_time_minutes, average_view_duration_seconds, click_through_rate,
            estimated_revenue, ad_revenue, metrics_date
        ) VALUES (
            (SELECT id FROM youtube_uploads WHERE video_id = ?),
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATE('now')
        )
        ''', (
            video_id, video_id,
            analytics_data.get('view_count', 0),
            analytics_data.get('like_count', 0),
            analytics_data.get('comment_count', 0),
            analytics_data.get('share_count', 0),
            analytics_data.get('watch_time_minutes', 0.0),
            analytics_data.get('average_view_duration', 0.0),
            analytics_data.get('click_through_rate', 0.0),
            analytics_data.get('estimated_revenue', 0.0),
            analytics_data.get('ad_revenue', 0.0)
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Analytics updated for video: {video_id}")
    
    def get_upload_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive upload statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get basic upload stats
        cursor.execute('''
        SELECT 
            upload_status,
            COUNT(*) as count,
            AVG(upload_attempts) as avg_attempts,
            AVG(upload_duration_seconds) as avg_duration
        FROM youtube_uploads 
        WHERE created_at >= datetime('now', '-{} days')
        GROUP BY upload_status
        '''.format(days))
        
        status_stats = cursor.fetchall()
        
        # Get performance stats
        cursor.execute('''
        SELECT 
            COUNT(*) as total_videos,
            SUM(view_count) as total_views,
            SUM(like_count) as total_likes,
            SUM(comment_count) as total_comments,
            AVG(engagement_rate) as avg_engagement_rate,
            SUM(estimated_revenue) as total_estimated_revenue
        FROM youtube_uploads 
        WHERE upload_status = 'completed'
        AND created_at >= datetime('now', '-{} days')
        '''.format(days))
        
        perf_stats = cursor.fetchone()
        
        # Get most successful videos
        cursor.execute('''
        SELECT title, video_id, view_count, like_count, engagement_rate, estimated_revenue
        FROM youtube_uploads 
        WHERE upload_status = 'completed'
        AND created_at >= datetime('now', '-{} days')
        ORDER BY view_count DESC 
        LIMIT 10
        '''.format(days))
        
        top_videos = cursor.fetchall()
        
        conn.close()
        
        return {
            "period_days": days,
            "status_breakdown": [
                {
                    "status": row[0],
                    "count": row[1],
                    "avg_attempts": row[2],
                    "avg_duration_seconds": row[3]
                } for row in status_stats
            ],
            "performance": {
                "total_videos": perf_stats[0] or 0,
                "total_views": perf_stats[1] or 0,
                "total_likes": perf_stats[2] or 0,
                "total_comments": perf_stats[3] or 0,
                "avg_engagement_rate": perf_stats[4] or 0.0,
                "total_estimated_revenue": perf_stats[5] or 0.0
            },
            "top_performers": [
                {
                    "title": row[0],
                    "video_id": row[1],
                    "views": row[2],
                    "likes": row[3],
                    "engagement_rate": row[4],
                    "estimated_revenue": row[5]
                } for row in top_videos
            ]
        }
    
    # Internal helper methods
    
    def _get_upload_record(self, upload_id: int) -> Optional[Dict]:
        """Get upload record by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM youtube_uploads WHERE id = ?', (upload_id,))
        result = cursor.fetchone()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        
        conn.close()
        return None
    
    def _get_pending_uploads(self, limit: int = 10) -> List[Dict]:
        """Get pending uploads ready for processing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM youtube_uploads 
        WHERE upload_status = 'pending'
        AND (scheduled_publish_time IS NULL OR scheduled_publish_time <= CURRENT_TIMESTAMP)
        AND upload_attempts < ?
        ORDER BY created_at ASC
        LIMIT ?
        ''', (self.max_retries, limit))
        
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        uploads = []
        for row in results:
            uploads.append(dict(zip(columns, row)))
        
        conn.close()
        return uploads
    
    def _build_upload_command(self, upload_data: Dict) -> List[str]:
        """Build the youtube-upload command with all parameters"""
        cmd = ['youtube-upload']
        
        # OAuth credentials
        if os.path.exists(self.oauth_credentials_path):
            cmd.extend(['--client-secrets', self.oauth_credentials_path])
        
        # Refresh token if available
        if os.path.exists(self.refresh_token_path):
            cmd.extend(['--credentials-file', self.refresh_token_path])
        
        # Video file (must be the first positional argument)
        cmd.append(upload_data['local_video_path'])
        
        # Title and description
        cmd.extend(['--title', upload_data['title']])
        if upload_data['description']:
            cmd.extend(['--description', upload_data['description']])
        
        # Tags
        if upload_data['tags']:
            try:
                tags = json.loads(upload_data['tags'])
                if tags and len(tags) > 0:
                    cmd.extend(['--tags', ','.join(tags)])
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Category
        if upload_data['category_id']:
            cmd.extend(['--category', upload_data['category_id']])
        
        # Privacy
        cmd.extend(['--privacy', upload_data['privacy_status']])
        
        # Thumbnail
        if upload_data['local_thumbnail_path'] and os.path.exists(upload_data['local_thumbnail_path']):
            cmd.extend(['--thumbnail', upload_data['local_thumbnail_path']])
        
        # Scheduled publishing
        if upload_data['scheduled_publish_time'] and upload_data['privacy_status'] != 'private':
            scheduled = datetime.fromisoformat(upload_data['scheduled_publish_time'])
            iso_time = scheduled.isoformat() + 'Z'
            cmd.extend(['--publish-at', iso_time])
        
        return cmd
    
    def _extract_video_id(self, output: str) -> Optional[str]:
        """Extract YouTube video ID from upload command output"""
        import re
        
        patterns = [
            r'Video ID:\s*([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
            r'ID:\s*([a-zA-Z0-9_-]{11})',
            r'([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                video_id = match.group(1)
                if len(video_id) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', video_id):
                    return video_id
        
        logger.warning(f"Could not extract video ID from output: {output[:500]}")
        return None
    
    def _classify_error_type(self, error_output: str) -> str:
        """Classify error type for better handling"""
        error_lower = error_output.lower()
        
        if '403' in error_output or 'quota' in error_lower or 'exceeded' in error_lower:
            return 'quota_exceeded'
        elif '429' in error_output or 'rate limit' in error_lower:
            return 'rate_limited'
        elif '401' in error_output or 'authentication' in error_lower or 'unauthorized' in error_lower:
            return 'authentication_failed'
        elif '500' in error_output or 'internal server error' in error_lower:
            return 'server_error'
        elif '502' in error_output or '503' in error_output or '504' in error_output:
            return 'service_unavailable'
        elif 'timeout' in error_lower or 'connection' in error_lower:
            return 'network_error'
        elif 'file' in error_lower and ('not found' in error_lower or 'missing' in error_lower):
            return 'file_error'
        else:
            return 'unknown_error'
    
    def _parse_error_for_retry_delay(self, error_output: str) -> int:
        """Determine appropriate retry delay based on error type"""
        error_type = self._classify_error_type(error_output)
        
        delay_map = {
            'quota_exceeded': 3600,      # 1 hour
            'rate_limited': 300,         # 5 minutes
            'server_error': 120,         # 2 minutes
            'service_unavailable': 180,  # 3 minutes
            'network_error': 60,         # 1 minute
            'authentication_failed': 0,  # Don't retry
            'file_error': 0,             # Don't retry
            'unknown_error': 60          # 1 minute
        }
        
        return delay_map.get(error_type, 60)
    
    def _create_upload_session(self, upload_id: int, attempt_number: int) -> int:
        """Create upload session record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO upload_sessions (upload_id, attempt_number, session_status)
        VALUES (?, ?, 'started')
        ''', (upload_id, attempt_number))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def _update_upload_status(self, upload_id: int, status: str):
        """Update upload status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE youtube_uploads 
        SET upload_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (status, upload_id))
        
        conn.commit()
        conn.close()
    
    def _update_upload_success(self, upload_id: int, video_id: str, session_id: int, duration: float):
        """Update records for successful upload"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        video_url = f"https://youtube.com/watch?v={video_id}"
        
        # Update main upload record
        cursor.execute('''
        UPDATE youtube_uploads 
        SET video_id = ?, video_url = ?, upload_status = 'completed',
            upload_complete_time = CURRENT_TIMESTAMP, upload_duration_seconds = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (video_id, video_url, duration, upload_id))
        
        # Update session record
        cursor.execute('''
        UPDATE upload_sessions 
        SET session_status = 'completed', session_end = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def _update_upload_failure(self, upload_id: int, session_id: int, error_code: str, 
                              error_msg: str, retry_delay: int = 60, error_type: str = 'unknown'):
        """Update records for failed upload"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update main upload record
        cursor.execute('''
        UPDATE youtube_uploads 
        SET upload_status = 'failed', upload_attempts = upload_attempts + 1,
            last_attempt_time = CURRENT_TIMESTAMP, error_code = ?, error_message = ?,
            retry_after_seconds = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (error_code, error_msg, retry_delay, upload_id))
        
        # Update session record
        cursor.execute('''
        UPDATE upload_sessions 
        SET session_status = 'failed', session_end = CURRENT_TIMESTAMP,
            error_type = ?, error_details = ?, retry_delay_seconds = ?
        WHERE id = ?
        ''', (error_type, error_msg, retry_delay, session_id))
        
        conn.commit()
        conn.close()
    
    def _add_to_playlist(self, upload_id: int, video_id: str, playlist_id: str):
        """Add video to playlist and track the assignment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Record playlist assignment
        cursor.execute('''
        INSERT INTO playlist_assignments (upload_id, playlist_id, assignment_status)
        VALUES (?, ?, 'pending')
        ''', (upload_id, playlist_id))
        
        assignment_id = cursor.lastrowid
        conn.commit()
        
        try:
            # Use youtube-upload to add to playlist
            cmd = [
                'youtube-upload',
                '--client-secrets', self.oauth_credentials_path,
                '--add-to-playlist', playlist_id,
                video_id
            ]
            
            if os.path.exists(self.refresh_token_path):
                cmd.extend(['--credentials-file', self.refresh_token_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Update assignment status
            cursor.execute('''
            UPDATE playlist_assignments 
            SET assignment_status = 'completed'
            WHERE id = ?
            ''', (assignment_id,))
            
            conn.commit()
            logger.info(f"✅ Video {video_id} added to playlist: {playlist_id}")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e.stdout or str(e)
            logger.warning(f"Failed to add video to playlist: {error_msg}")
            
            cursor.execute('''
            UPDATE playlist_assignments 
            SET assignment_status = 'failed'
            WHERE id = ?
            ''', (assignment_id,))
            
            conn.commit()
        
        conn.close()
    
    def _initialize_revenue_tracking(self, upload_id: int, video_id: str, upload_data: Dict):
        """Initialize revenue tracking for newly uploaded video"""
        if not self.revenue_tracker:
            return
        
        try:
            # Add revenue source for this video
            source_name = f"YouTube Video: {upload_data['title'][:50]}..."
            self.revenue_tracker.add_revenue_source(
                source_name, 
                "youtube_video", 
                0.0,  # Start with 0 revenue
                metadata={
                    "video_id": video_id,
                    "upload_id": upload_id,
                    "upload_date": datetime.now().isoformat()
                }
            )
            
            logger.info(f"✅ Revenue tracking initialized for video: {video_id}")
            
        except Exception as e:
            logger.warning(f"Could not initialize revenue tracking: {e}")
    
    def _get_video_duration(self, video_file: str) -> float:
        """Get video duration in seconds"""
        try:
            import moviepy.editor as mp
            clip = mp.VideoFileClip(video_file)
            duration = clip.duration
            clip.close()
            return duration or 0.0
        except Exception:
            return 0.0

# Convenience function for integration with existing video pipeline
def integrate_youtube_upload_with_pipeline():
    """
    Example of how to integrate YouTube upload with existing video automation pipeline
    """
    logger.info("🔗 Integrating YouTube upload with video automation pipeline")
    
    # This would be called from video_automation_pipeline.py after video creation
    upload_manager = YouTubeUploadManager()
    
    def upload_completed_video(video_project, privacy="public", scheduled_time=None):
        """Upload a completed video project to YouTube"""
        
        # Create upload request from video project
        request = UploadRequest(
            video_file=f"generated_videos/{video_project.project_id}_final.mp4",
            thumbnail_file=video_project.thumbnail,
            title=video_project.title,
            description=video_project.description,
            tags=video_project.tags,
            privacy=privacy,
            scheduled_time=scheduled_time
        )
        
        # Schedule upload
        upload_id = upload_manager.schedule_upload(request)
        
        # Upload immediately or let scheduled process handle it
        if not scheduled_time:
            result = upload_manager.upload_video(upload_id)
            if result.success:
                logger.info(f"✅ Video uploaded: {result.video_url}")
                return result.video_id
            else:
                logger.error(f"❌ Upload failed: {result.error_message}")
                return None
        else:
            logger.info(f"⏰ Upload scheduled for: {scheduled_time}")
            return upload_id
    
    return upload_completed_video

if __name__ == "__main__":
    # Example usage and testing
    manager = YouTubeUploadManager()
    
    # Example: Schedule an upload
    request = UploadRequest(
        video_file="example_video.mp4",
        thumbnail_file="example_thumbnail.jpg",
        title="Test Video Upload",
        description="This is a test video uploaded via the automation system",
        tags=["test", "automation", "youtube"],
        privacy="private"  # Start with private for testing
    )
    
    upload_id = manager.schedule_upload(request)
    print(f"Upload scheduled with ID: {upload_id}")
    
    # Get statistics
    stats = manager.get_upload_statistics(30)
    print(f"Upload statistics: {json.dumps(stats, indent=2)}")
