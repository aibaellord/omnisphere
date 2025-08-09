#!/usr/bin/env python3
"""
📊 YOUTUBE ANALYTICS COLLECTOR 📊
Daily YouTube Analytics API data collection for performance & revenue tracking

This system collects real analytics data from YouTube Analytics API including:
- Views, watch time, RPM (Revenue Per Mille)
- Estimated revenue, subscriber metrics
- Channel performance data for dashboard visualization
"""

import os
import json
import logging
import sqlite3
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube Analytics API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly', 
          'https://www.googleapis.com/auth/yt-analytics.readonly']

@dataclass
class AnalyticsData:
    """YouTube Analytics data structure"""
    date: str
    channel_id: str
    views: int
    watch_time_minutes: int
    estimated_revenue: float
    rpm: float  # Revenue per mille
    cpm: float  # Cost per mille
    subscribers_gained: int
    subscribers_lost: int
    likes: int
    dislikes: int
    comments: int
    shares: int
    estimated_minutes_watched: float
    average_view_duration: float
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass 
class VideoAnalytics:
    """Individual video analytics data"""
    video_id: str
    date: str
    views: int
    watch_time_minutes: int
    estimated_revenue: float
    rpm: float
    cpm: float
    likes: int
    comments: int
    shares: int
    average_view_duration: float
    traffic_source_search: float
    traffic_source_suggested: float
    traffic_source_external: float
    
    def to_dict(self) -> Dict:
        return asdict(self)

class YouTubeAnalyticsCollector:
    """
    📈 YOUTUBE ANALYTICS API COLLECTOR
    
    Collects daily analytics data from YouTube Analytics API
    and stores it in SQLite database for dashboard visualization.
    """
    
    def __init__(self, credentials_file: str = "youtube_credentials.json", 
                 token_file: str = "youtube_token.json",
                 db_path: str = "analytics_data.db"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.db_path = db_path
        self.service = None
        self.analytics_service = None
        
        # Initialize authentication
        self._authenticate()
        
        # Initialize database
        self._setup_database()
        
        logger.info("✅ YouTube Analytics Collector initialized")
    
    def _authenticate(self):
        """Authenticate with YouTube API and Analytics API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                logger.warning(f"Error loading token: {e}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("✅ Credentials refreshed")
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file {self.credentials_file} not found. "
                        "Download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("✅ New credentials obtained")
            
            # Save credentials
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        # Build services
        try:
            self.service = googleapiclient.discovery.build(
                'youtube', 'v3', credentials=creds, cache_discovery=False
            )
            self.analytics_service = googleapiclient.discovery.build(
                'youtubeAnalytics', 'v2', credentials=creds, cache_discovery=False
            )
            logger.info("✅ YouTube API services initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize YouTube services: {e}")
            raise
    
    def _setup_database(self):
        """Set up SQLite database for analytics data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Channel analytics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            watch_time_minutes INTEGER DEFAULT 0,
            estimated_revenue REAL DEFAULT 0.0,
            rpm REAL DEFAULT 0.0,
            cpm REAL DEFAULT 0.0,
            subscribers_gained INTEGER DEFAULT 0,
            subscribers_lost INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            estimated_minutes_watched REAL DEFAULT 0.0,
            average_view_duration REAL DEFAULT 0.0,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, channel_id)
        )
        ''')
        
        # Video analytics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            date TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            watch_time_minutes INTEGER DEFAULT 0,
            estimated_revenue REAL DEFAULT 0.0,
            rpm REAL DEFAULT 0.0,
            cpm REAL DEFAULT 0.0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            average_view_duration REAL DEFAULT 0.0,
            traffic_source_search REAL DEFAULT 0.0,
            traffic_source_suggested REAL DEFAULT 0.0,
            traffic_source_external REAL DEFAULT 0.0,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(video_id, date)
        )
        ''')
        
        # Revenue tracking table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS revenue_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            total_revenue REAL DEFAULT 0.0,
            ad_revenue REAL DEFAULT 0.0,
            estimated_cost REAL DEFAULT 0.0,
            profit_margin REAL DEFAULT 0.0,
            cost_per_view REAL DEFAULT 0.0,
            revenue_per_subscriber REAL DEFAULT 0.0,
            collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, channel_id)
        )
        ''')
        
        # Channel metadata table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_metadata (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT,
            subscriber_count INTEGER,
            total_views INTEGER,
            video_count INTEGER,
            created_at TEXT,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Analytics database initialized")
    
    def get_my_channels(self) -> List[Dict[str, str]]:
        """Get list of channels owned by authenticated user"""
        try:
            request = self.service.channels().list(
                part='snippet,statistics,contentDetails',
                mine=True
            )
            response = request.execute()
            
            channels = []
            for item in response['items']:
                channels.append({
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'subscriber_count': int(item['statistics'].get('subscriberCount', 0)),
                    'total_views': int(item['statistics'].get('viewCount', 0)),
                    'video_count': int(item['statistics'].get('videoCount', 0))
                })
            
            logger.info(f"✅ Found {len(channels)} channels")
            return channels
            
        except Exception as e:
            logger.error(f"❌ Error getting channels: {e}")
            return []
    
    def collect_channel_analytics(self, channel_id: str, 
                                date_str: Optional[str] = None) -> Optional[AnalyticsData]:
        """Collect analytics data for a specific channel and date"""
        if not date_str:
            date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            # Get analytics data from YouTube Analytics API
            request = self.analytics_service.reports().query(
                ids=f'channel=={channel_id}',
                startDate=date_str,
                endDate=date_str,
                metrics='views,estimatedMinutesWatched,estimatedRevenue,cpm,adImpressions,subscribersGained,subscribersLost',
                dimensions='day'
            )
            
            response = request.execute()
            
            if not response.get('rows'):
                logger.warning(f"No analytics data found for {channel_id} on {date_str}")
                return None
            
            row = response['rows'][0]  # First (and should be only) row
            
            # Map response to our data structure
            views = int(row[1]) if len(row) > 1 else 0
            watch_time_minutes = int(row[2]) if len(row) > 2 else 0
            estimated_revenue = float(row[3]) if len(row) > 3 else 0.0
            cpm = float(row[4]) if len(row) > 4 else 0.0
            ad_impressions = int(row[5]) if len(row) > 5 else 0
            subscribers_gained = int(row[6]) if len(row) > 6 else 0
            subscribers_lost = int(row[7]) if len(row) > 7 else 0
            
            # Calculate RPM (Revenue per mille)
            rpm = (estimated_revenue / views * 1000) if views > 0 else 0.0
            
            # Get engagement metrics separately
            engagement_request = self.analytics_service.reports().query(
                ids=f'channel=={channel_id}',
                startDate=date_str,
                endDate=date_str,
                metrics='likes,dislikes,comments,shares,averageViewDuration',
                dimensions='day'
            )
            
            engagement_response = engagement_request.execute()
            engagement_row = engagement_response.get('rows', [[]])[0]
            
            likes = int(engagement_row[1]) if len(engagement_row) > 1 else 0
            dislikes = int(engagement_row[2]) if len(engagement_row) > 2 else 0
            comments = int(engagement_row[3]) if len(engagement_row) > 3 else 0
            shares = int(engagement_row[4]) if len(engagement_row) > 4 else 0
            avg_view_duration = float(engagement_row[5]) if len(engagement_row) > 5 else 0.0
            
            analytics_data = AnalyticsData(
                date=date_str,
                channel_id=channel_id,
                views=views,
                watch_time_minutes=watch_time_minutes,
                estimated_revenue=estimated_revenue,
                rpm=rpm,
                cpm=cpm,
                subscribers_gained=subscribers_gained,
                subscribers_lost=subscribers_lost,
                likes=likes,
                dislikes=dislikes,
                comments=comments,
                shares=shares,
                estimated_minutes_watched=float(watch_time_minutes),
                average_view_duration=avg_view_duration
            )
            
            # Store in database
            self._store_channel_analytics(analytics_data)
            
            logger.info(f"✅ Collected analytics for {channel_id} on {date_str}: "
                       f"{views:,} views, ${estimated_revenue:.2f} revenue")
            
            return analytics_data
            
        except googleapiclient.errors.HttpError as e:
            logger.error(f"❌ YouTube API error collecting analytics for {channel_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error collecting analytics for {channel_id}: {e}")
            return None
    
    def collect_video_analytics(self, video_id: str, 
                              date_str: Optional[str] = None) -> Optional[VideoAnalytics]:
        """Collect analytics data for a specific video"""
        if not date_str:
            date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            # Get video analytics
            request = self.analytics_service.reports().query(
                ids=f'channel==MINE',  # Will need to be updated with actual channel
                startDate=date_str,
                endDate=date_str,
                metrics='views,estimatedMinutesWatched,estimatedRevenue,cpm,likes,comments,shares,averageViewDuration',
                dimensions='video',
                filters=f'video=={video_id}'
            )
            
            response = request.execute()
            
            if not response.get('rows'):
                logger.warning(f"No analytics data found for video {video_id} on {date_str}")
                return None
            
            row = response['rows'][0]
            
            # Get traffic source data
            traffic_request = self.analytics_service.reports().query(
                ids=f'channel==MINE',
                startDate=date_str,
                endDate=date_str,
                metrics='views',
                dimensions='trafficSourceType',
                filters=f'video=={video_id}'
            )
            
            traffic_response = traffic_request.execute()
            
            # Parse traffic sources
            traffic_sources = {}
            for traffic_row in traffic_response.get('rows', []):
                source_type = traffic_row[0]
                views = int(traffic_row[1])
                traffic_sources[source_type] = views
            
            total_views = sum(traffic_sources.values())
            
            video_analytics = VideoAnalytics(
                video_id=video_id,
                date=date_str,
                views=int(row[1]) if len(row) > 1 else 0,
                watch_time_minutes=int(row[2]) if len(row) > 2 else 0,
                estimated_revenue=float(row[3]) if len(row) > 3 else 0.0,
                rpm=(float(row[3]) / int(row[1]) * 1000) if len(row) > 3 and int(row[1]) > 0 else 0.0,
                cpm=float(row[4]) if len(row) > 4 else 0.0,
                likes=int(row[5]) if len(row) > 5 else 0,
                comments=int(row[6]) if len(row) > 6 else 0,
                shares=int(row[7]) if len(row) > 7 else 0,
                average_view_duration=float(row[8]) if len(row) > 8 else 0.0,
                traffic_source_search=(traffic_sources.get('SEARCH', 0) / total_views * 100) if total_views > 0 else 0.0,
                traffic_source_suggested=(traffic_sources.get('SUGGESTED_VIDEO', 0) / total_views * 100) if total_views > 0 else 0.0,
                traffic_source_external=(traffic_sources.get('EXTERNAL', 0) / total_views * 100) if total_views > 0 else 0.0
            )
            
            # Store in database
            self._store_video_analytics(video_analytics)
            
            logger.info(f"✅ Collected video analytics for {video_id}")
            return video_analytics
            
        except Exception as e:
            logger.error(f"❌ Error collecting video analytics for {video_id}: {e}")
            return None
    
    def _store_channel_analytics(self, data: AnalyticsData):
        """Store channel analytics data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO channel_analytics 
        (date, channel_id, views, watch_time_minutes, estimated_revenue, rpm, cpm,
         subscribers_gained, subscribers_lost, likes, dislikes, comments, shares,
         estimated_minutes_watched, average_view_duration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.date, data.channel_id, data.views, data.watch_time_minutes,
            data.estimated_revenue, data.rpm, data.cpm, data.subscribers_gained,
            data.subscribers_lost, data.likes, data.dislikes, data.comments,
            data.shares, data.estimated_minutes_watched, data.average_view_duration
        ))
        
        # Also store in revenue tracking
        conn.execute('''
        INSERT OR REPLACE INTO revenue_tracking
        (date, channel_id, total_revenue, ad_revenue, estimated_cost, profit_margin,
         cost_per_view, revenue_per_subscriber)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.date, data.channel_id, data.estimated_revenue, data.estimated_revenue,
            0.0,  # Zero cost as specified
            100.0,  # 100% profit margin since cost is zero
            0.0,  # Zero cost per view
            data.estimated_revenue / max(1, data.subscribers_gained)  # Revenue per new subscriber
        ))
        
        conn.commit()
        conn.close()
    
    def _store_video_analytics(self, data: VideoAnalytics):
        """Store video analytics data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO video_analytics
        (video_id, date, views, watch_time_minutes, estimated_revenue, rpm, cpm,
         likes, comments, shares, average_view_duration, traffic_source_search,
         traffic_source_suggested, traffic_source_external)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.video_id, data.date, data.views, data.watch_time_minutes,
            data.estimated_revenue, data.rpm, data.cpm, data.likes, data.comments,
            data.shares, data.average_view_duration, data.traffic_source_search,
            data.traffic_source_suggested, data.traffic_source_external
        ))
        
        conn.commit()
        conn.close()
    
    def update_channel_metadata(self, channel_id: str):
        """Update channel metadata from YouTube API"""
        try:
            request = self.service.channels().list(
                part='snippet,statistics',
                id=channel_id
            )
            response = request.execute()
            
            if response['items']:
                item = response['items'][0]
                snippet = item['snippet']
                statistics = item['statistics']
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT OR REPLACE INTO channel_metadata
                (channel_id, channel_name, subscriber_count, total_views, video_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    channel_id,
                    snippet['title'],
                    int(statistics.get('subscriberCount', 0)),
                    int(statistics.get('viewCount', 0)),
                    int(statistics.get('videoCount', 0)),
                    snippet['publishedAt']
                ))
                
                conn.commit()
                conn.close()
                
                logger.info(f"✅ Updated metadata for {snippet['title']}")
                
        except Exception as e:
            logger.error(f"❌ Error updating channel metadata: {e}")
    
    def daily_collection_job(self):
        """Daily job to collect analytics for all channels"""
        logger.info("🚀 Starting daily analytics collection...")
        
        channels = self.get_my_channels()
        
        if not channels:
            logger.warning("No channels found for collection")
            return
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        for channel in channels:
            channel_id = channel['id']
            logger.info(f"Collecting analytics for: {channel['title']}")
            
            # Collect channel analytics
            self.collect_channel_analytics(channel_id, yesterday)
            
            # Update channel metadata
            self.update_channel_metadata(channel_id)
            
            # Rate limiting
            time.sleep(1)
        
        logger.info("✅ Daily analytics collection completed")
    
    def get_dashboard_data(self, days_back: int = 30) -> Dict[str, Any]:
        """Get data for dashboard visualization"""
        conn = sqlite3.connect(self.db_path)
        
        # Date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Channel analytics summary
        analytics_query = '''
        SELECT 
            date,
            SUM(views) as total_views,
            SUM(watch_time_minutes) as total_watch_time,
            SUM(estimated_revenue) as total_revenue,
            AVG(rpm) as avg_rpm,
            AVG(cpm) as avg_cpm,
            SUM(subscribers_gained) as total_subs_gained,
            SUM(subscribers_lost) as total_subs_lost
        FROM channel_analytics
        WHERE date >= ? AND date <= ?
        GROUP BY date
        ORDER BY date DESC
        '''
        
        analytics_df = pd.read_sql_query(
            analytics_query, conn, 
            params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        )
        
        # Revenue tracking
        revenue_query = '''
        SELECT date, total_revenue, profit_margin
        FROM revenue_tracking
        WHERE date >= ? AND date <= ?
        ORDER BY date DESC
        '''
        
        revenue_df = pd.read_sql_query(
            revenue_query, conn,
            params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        )
        
        # Channel metadata
        channels_query = '''
        SELECT channel_name, subscriber_count, total_views, video_count
        FROM channel_metadata
        ORDER BY subscriber_count DESC
        '''
        
        channels_df = pd.read_sql_query(channels_query, conn)
        
        conn.close()
        
        # Calculate KPIs
        total_revenue = analytics_df['total_revenue'].sum() if not analytics_df.empty else 0
        total_views = analytics_df['total_views'].sum() if not analytics_df.empty else 0
        total_watch_time = analytics_df['total_watch_time'].sum() if not analytics_df.empty else 0
        avg_rpm = analytics_df['avg_rpm'].mean() if not analytics_df.empty else 0
        
        dashboard_data = {
            'kpis': {
                'total_revenue': total_revenue,
                'total_views': total_views,
                'total_watch_time_hours': total_watch_time / 60,
                'average_rpm': avg_rpm,
                'profit_margin': 100.0,  # 100% since costs are zero
                'cost_vs_revenue_ratio': 0.0  # Zero cost
            },
            'analytics_data': analytics_df.to_dict('records') if not analytics_df.empty else [],
            'revenue_data': revenue_df.to_dict('records') if not revenue_df.empty else [],
            'channels_data': channels_df.to_dict('records') if not channels_df.empty else [],
            'last_updated': datetime.now().isoformat()
        }
        
        return dashboard_data
    
    def setup_scheduler(self):
        """Set up daily collection schedule"""
        # Schedule daily collection at 2 AM
        schedule.every().day.at("02:00").do(self.daily_collection_job)
        logger.info("✅ Daily collection scheduled for 2:00 AM")
        
        return schedule
    
    def run_scheduler(self):
        """Run the scheduler (blocking)"""
        logger.info("🚀 Starting analytics collection scheduler...")
        
        # Run initial collection
        self.daily_collection_job()
        
        # Run scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main function for testing and manual runs"""
    print("\n📊 YOUTUBE ANALYTICS COLLECTOR")
    print("=" * 50)
    
    collector = YouTubeAnalyticsCollector()
    
    # Get channels
    print("\n📺 Getting channels...")
    channels = collector.get_my_channels()
    
    if channels:
        print(f"✅ Found {len(channels)} channels:")
        for channel in channels:
            print(f"  - {channel['title']}: {channel['subscriber_count']:,} subscribers")
        
        # Collect analytics for yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        for channel in channels:
            print(f"\n📈 Collecting analytics for {channel['title']}...")
            analytics = collector.collect_channel_analytics(channel['id'], yesterday)
            
            if analytics:
                print(f"  Views: {analytics.views:,}")
                print(f"  Watch Time: {analytics.watch_time_minutes:,} minutes")
                print(f"  Revenue: ${analytics.estimated_revenue:.2f}")
                print(f"  RPM: ${analytics.rpm:.2f}")
    
    # Get dashboard data
    print("\n📱 Getting dashboard data...")
    dashboard_data = collector.get_dashboard_data()
    print(f"✅ Dashboard data ready: ${dashboard_data['kpis']['total_revenue']:.2f} total revenue")
    
    return collector


if __name__ == "__main__":
    main()
