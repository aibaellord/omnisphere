#!/usr/bin/env python3
"""
🔥 TRENDING DATA COLLECTOR AGENT 🔥
Collects trending videos from YouTube API per region & category
Handles pagination, quotas, and stores data in JSON + SQLite

Features:
- Fetches videos.list(chart="mostPopular") per region & category
- Handles API pagination and quota limits
- Stores JSON snapshots in /data/trending/DATE.json
- Upserts data to SQLite using SQLModel ORM
- Logs quota usage and rotates API keys if needed
- Supports scheduling via GitHub Actions
"""

import os
import sys
import json
import logging
import asyncio
import aiofiles
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass, asdict
import time
import random

import googleapiclient.discovery
import googleapiclient.errors
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlmodel import SQLModel, Field, create_engine as sqlmodel_create_engine, Session as SQLModelSession
import httpx
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trending_collector.log')
    ]
)
logger = logging.getLogger(__name__)

# YouTube API Constants
YOUTUBE_CATEGORIES = {
    '1': 'Film & Animation',
    '2': 'Autos & Vehicles', 
    '10': 'Music',
    '15': 'Pets & Animals',
    '17': 'Sports',
    '19': 'Travel & Events',
    '20': 'Gaming',
    '22': 'People & Blogs',
    '23': 'Comedy',
    '24': 'Entertainment',
    '25': 'News & Politics',
    '26': 'Howto & Style',
    '27': 'Education',
    '28': 'Science & Technology',
}

YOUTUBE_REGIONS = [
    'US', 'GB', 'CA', 'AU', 'DE', 'FR', 'ES', 'IT', 'JP', 'KR', 
    'BR', 'MX', 'IN', 'RU', 'NL', 'SE', 'NO', 'DK', 'FI', 'PL'
]

# SQLModel Models for ORM
class TrendingVideo(SQLModel, table=True):
    """SQLModel for trending video data"""
    __tablename__ = "trending_videos"
    
    video_id: str = Field(primary_key=True)
    title: str
    channel_id: str
    channel_title: str
    published_at: datetime
    category_id: str
    category_name: Optional[str] = None
    region_code: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    duration: Optional[str] = None
    tags: Optional[str] = None  # JSON string
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    engagement_rate: float = 0.0
    trending_rank: int = 0
    collected_at: datetime
    collection_batch: str  # Date-based batch identifier

class QuotaUsage(SQLModel, table=True):
    """Track API quota usage"""
    __tablename__ = "quota_usage"
    
    id: Optional[int] = Field(primary_key=True)
    api_key_hash: str  # Hashed API key for identification
    date: datetime
    requests_made: int = 0
    quota_used: int = 0
    quota_limit: int = 10000  # Default YouTube API quota
    region_code: Optional[str] = None
    category_id: Optional[str] = None
    created_at: datetime

class CollectionStats(SQLModel, table=True):
    """Track collection statistics"""
    __tablename__ = "collection_stats"
    
    id: Optional[int] = Field(primary_key=True)
    collection_date: datetime
    batch_id: str
    total_videos: int = 0
    regions_processed: int = 0
    categories_processed: int = 0
    api_requests_made: int = 0
    errors_encountered: int = 0
    processing_time_seconds: float = 0.0
    success_rate: float = 0.0

@dataclass
class APIQuotaTracker:
    """Track API quota usage"""
    requests_today: int = 0
    quota_used_today: int = 0
    current_api_key_index: int = 0
    quota_limit: int = 10000
    
    def can_make_request(self, cost: int = 1) -> bool:
        return (self.quota_used_today + cost) <= self.quota_limit
    
    def record_request(self, cost: int = 1):
        self.requests_today += 1
        self.quota_used_today += cost

class TrendingDataCollector:
    """
    🔥 Main Trending Data Collector Agent
    
    Collects YouTube trending videos by region and category,
    handles pagination, manages quotas, and stores data efficiently.
    """
    
    def __init__(self, 
                 api_keys: List[str],
                 db_path: str = "trending_data.db",
                 data_dir: str = "/data/trending"):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize quota tracker
        self.quota_tracker = APIQuotaTracker()
        
        # Initialize database
        self.engine = sqlmodel_create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(self.engine)
        
        # Initialize YouTube API client
        self.youtube = None
        self._init_youtube_client()
        
        logger.info(f"✅ Trending Data Collector initialized with {len(api_keys)} API keys")
    
    def _init_youtube_client(self):
        """Initialize YouTube API client with current API key"""
        try:
            current_key = self.api_keys[self.current_key_index]
            self.youtube = googleapiclient.discovery.build(
                'youtube', 'v3',
                developerKey=current_key,
                cache_discovery=False
            )
            logger.info(f"✅ YouTube API client initialized with key #{self.current_key_index + 1}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize YouTube API client: {e}")
            raise
    
    def _rotate_api_key(self):
        """Rotate to next API key if quota exceeded"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self.quota_tracker = APIQuotaTracker()  # Reset quota tracking
            self._init_youtube_client()
            logger.info(f"🔄 Rotated to API key #{self.current_key_index + 1}")
            return True
        return False
    
    async def collect_trending_data(self, 
                                  regions: List[str] = None,
                                  categories: List[str] = None,
                                  max_results_per_request: int = 50) -> Dict[str, Any]:
        """
        Main collection method - fetches trending videos for all regions/categories
        """
        start_time = time.time()
        batch_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        regions = regions or YOUTUBE_REGIONS
        categories = categories or list(YOUTUBE_CATEGORIES.keys())
        
        logger.info(f"🚀 Starting trending data collection for {len(regions)} regions, {len(categories)} categories")
        
        all_videos = []
        total_requests = 0
        total_errors = 0
        
        # Collection statistics
        stats = CollectionStats(
            collection_date=datetime.now(timezone.utc),
            batch_id=batch_id,
            regions_processed=0,
            categories_processed=0
        )
        
        for region in regions:
            region_videos = []
            
            try:
                # Collect trending videos for this region
                videos = await self._collect_region_trending(
                    region, 
                    categories,
                    max_results_per_request
                )
                region_videos.extend(videos)
                stats.regions_processed += 1
                
                # Add to overall collection
                all_videos.extend(videos)
                
                # Rate limiting between regions
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error collecting data for region {region}: {e}")
                total_errors += 1
                
                # Try rotating API key if quota exceeded
                if "quotaExceeded" in str(e) and self._rotate_api_key():
                    logger.info("🔄 Retrying after API key rotation...")
                    try:
                        videos = await self._collect_region_trending(region, categories, max_results_per_request)
                        region_videos.extend(videos)
                        all_videos.extend(videos)
                        stats.regions_processed += 1
                    except Exception as retry_error:
                        logger.error(f"❌ Retry failed for region {region}: {retry_error}")
                        total_errors += 1
        
        # Calculate final statistics
        processing_time = time.time() - start_time
        stats.total_videos = len(all_videos)
        stats.api_requests_made = self.quota_tracker.requests_today
        stats.errors_encountered = total_errors
        stats.processing_time_seconds = processing_time
        stats.success_rate = (stats.regions_processed / len(regions)) * 100 if regions else 0
        
        # Store data
        await self._store_data(all_videos, batch_id)
        self._store_stats(stats)
        
        collection_summary = {
            'batch_id': batch_id,
            'collection_time': datetime.now(timezone.utc).isoformat(),
            'total_videos_collected': len(all_videos),
            'regions_processed': stats.regions_processed,
            'categories_processed': stats.categories_processed,
            'api_requests_made': self.quota_tracker.requests_today,
            'quota_used': self.quota_tracker.quota_used_today,
            'processing_time_seconds': processing_time,
            'success_rate': stats.success_rate,
            'errors': total_errors
        }
        
        logger.info(f"✅ Collection completed: {len(all_videos)} videos in {processing_time:.2f}s")
        return collection_summary
    
    async def _collect_region_trending(self, 
                                     region: str, 
                                     categories: List[str],
                                     max_results: int) -> List[Dict[str, Any]]:
        """Collect trending videos for a specific region across all categories"""
        region_videos = []
        
        for category_id in categories:
            if not self.quota_tracker.can_make_request(cost=1):
                if not self._rotate_api_key():
                    logger.warning("⚠️  Quota exceeded and no more API keys available")
                    break
            
            try:
                # Fetch trending videos for this region/category
                videos = await self._fetch_trending_videos(
                    region_code=region,
                    category_id=category_id,
                    max_results=max_results
                )
                
                # Add metadata
                for video in videos:
                    video['region_code'] = region
                    video['category_id'] = category_id
                    video['category_name'] = YOUTUBE_CATEGORIES.get(category_id, 'Unknown')
                    video['collected_at'] = datetime.now(timezone.utc).isoformat()
                
                region_videos.extend(videos)
                
                # Track quota usage
                self.quota_tracker.record_request(cost=1)
                
                # Rate limiting between categories
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"⚠️  Error fetching {region}/{category_id}: {e}")
                continue
        
        logger.info(f"✅ Collected {len(region_videos)} videos for region {region}")
        return region_videos
    
    async def _fetch_trending_videos(self, 
                                   region_code: str,
                                   category_id: str,
                                   max_results: int) -> List[Dict[str, Any]]:
        """Fetch trending videos from YouTube API with pagination"""
        videos = []
        next_page_token = None
        collected = 0
        
        while collected < max_results:
            try:
                # Calculate results for this request
                results_needed = min(50, max_results - collected)  # YouTube API max is 50
                
                # Build request
                request = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    chart='mostPopular',
                    regionCode=region_code,
                    videoCategoryId=category_id,
                    maxResults=results_needed,
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                # Process videos
                for idx, item in enumerate(response.get('items', [])):
                    video_data = self._process_video_item(item, collected + idx + 1)
                    videos.append(video_data)
                
                collected += len(response.get('items', []))
                next_page_token = response.get('nextPageToken')
                
                # Break if no more pages or reached limit
                if not next_page_token or collected >= max_results:
                    break
                    
                # Rate limiting between paginated requests
                await asyncio.sleep(0.2)
                
            except googleapiclient.errors.HttpError as e:
                if e.resp.status == 403:
                    logger.warning(f"⚠️  Quota exceeded for {region_code}/{category_id}")
                    raise Exception("quotaExceeded")
                else:
                    logger.error(f"❌ API error for {region_code}/{category_id}: {e}")
                    break
            except Exception as e:
                logger.error(f"❌ Unexpected error for {region_code}/{category_id}: {e}")
                break
        
        return videos
    
    def _process_video_item(self, item: Dict[str, Any], rank: int) -> Dict[str, Any]:
        """Process individual video item from YouTube API response"""
        try:
            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})
            
            # Extract numeric statistics safely
            view_count = int(statistics.get('viewCount', 0))
            like_count = int(statistics.get('likeCount', 0))
            comment_count = int(statistics.get('commentCount', 0))
            
            # Calculate engagement rate
            engagement_rate = 0.0
            if view_count > 0:
                engagement_rate = ((like_count + comment_count) / view_count) * 100
            
            # Get thumbnail URL
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = None
            if 'high' in thumbnails:
                thumbnail_url = thumbnails['high']['url']
            elif 'medium' in thumbnails:
                thumbnail_url = thumbnails['medium']['url']
            elif 'default' in thumbnails:
                thumbnail_url = thumbnails['default']['url']
            
            return {
                'video_id': item['id'],
                'title': snippet.get('title', ''),
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'duration': content_details.get('duration', ''),
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'tags': json.dumps(snippet.get('tags', [])),
                'description': snippet.get('description', '')[:1000],  # Truncate for storage
                'thumbnail_url': thumbnail_url,
                'engagement_rate': engagement_rate,
                'trending_rank': rank
            }
        except Exception as e:
            logger.warning(f"⚠️  Error processing video item: {e}")
            return {}
    
    async def _store_data(self, videos: List[Dict[str, Any]], batch_id: str):
        """Store collected data in both JSON and SQLite"""
        if not videos:
            return
        
        # Store JSON snapshot
        await self._store_json_snapshot(videos, batch_id)
        
        # Upsert to SQLite database
        self._upsert_to_database(videos, batch_id)
    
    async def _store_json_snapshot(self, videos: List[Dict[str, Any]], batch_id: str):
        """Store raw JSON data snapshot"""
        try:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            filename = f"{date_str}_{batch_id}.json"
            filepath = self.data_dir / filename
            
            # Create data structure
            snapshot_data = {
                'collection_metadata': {
                    'batch_id': batch_id,
                    'collection_date': datetime.now(timezone.utc).isoformat(),
                    'total_videos': len(videos),
                    'collector_version': '1.0.0'
                },
                'videos': videos
            }
            
            # Write JSON file asynchronously
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(snapshot_data, indent=2, ensure_ascii=False))
            
            logger.info(f"✅ JSON snapshot saved: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Error saving JSON snapshot: {e}")
    
    def _upsert_to_database(self, videos: List[Dict[str, Any]], batch_id: str):
        """Upsert video data to SQLite database using SQLModel"""
        try:
            with SQLModelSession(self.engine) as session:
                for video_data in videos:
                    if not video_data:  # Skip empty video data
                        continue
                    
                    # Convert to SQLModel instance
                    video = TrendingVideo(
                        video_id=video_data['video_id'],
                        title=video_data['title'],
                        channel_id=video_data['channel_id'],
                        channel_title=video_data['channel_title'],
                        published_at=datetime.fromisoformat(video_data['published_at'].replace('Z', '+00:00')),
                        category_id=video_data.get('category_id', ''),
                        category_name=video_data.get('category_name', ''),
                        region_code=video_data.get('region_code', ''),
                        view_count=video_data['view_count'],
                        like_count=video_data['like_count'],
                        comment_count=video_data['comment_count'],
                        duration=video_data.get('duration'),
                        tags=video_data.get('tags'),
                        description=video_data.get('description'),
                        thumbnail_url=video_data.get('thumbnail_url'),
                        engagement_rate=video_data['engagement_rate'],
                        trending_rank=video_data.get('trending_rank', 0),
                        collected_at=datetime.now(timezone.utc),
                        collection_batch=batch_id
                    )
                    
                    # Upsert (merge) the record
                    session.merge(video)
                
                session.commit()
                logger.info(f"✅ Upserted {len(videos)} videos to database")
                
        except Exception as e:
            logger.error(f"❌ Error upserting to database: {e}")
            session.rollback()
    
    def _store_stats(self, stats: CollectionStats):
        """Store collection statistics"""
        try:
            with SQLModelSession(self.engine) as session:
                session.add(stats)
                session.commit()
                
                # Also store quota usage
                quota_record = QuotaUsage(
                    api_key_hash=f"key_{self.current_key_index}",
                    date=datetime.now(timezone.utc),
                    requests_made=self.quota_tracker.requests_today,
                    quota_used=self.quota_tracker.quota_used_today,
                    quota_limit=self.quota_tracker.quota_limit,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(quota_record)
                session.commit()
                
        except Exception as e:
            logger.error(f"❌ Error storing statistics: {e}")
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota usage status"""
        return {
            'current_api_key_index': self.current_key_index,
            'requests_today': self.quota_tracker.requests_today,
            'quota_used_today': self.quota_tracker.quota_used_today,
            'quota_remaining': self.quota_tracker.quota_limit - self.quota_tracker.quota_used_today,
            'quota_limit': self.quota_tracker.quota_limit,
            'can_make_requests': self.quota_tracker.can_make_request()
        }
    
    def get_collection_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent collection history"""
        try:
            with SQLModelSession(self.engine) as session:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                
                results = session.query(CollectionStats).filter(
                    CollectionStats.collection_date >= cutoff_date
                ).order_by(CollectionStats.collection_date.desc()).all()
                
                return [
                    {
                        'batch_id': stat.batch_id,
                        'collection_date': stat.collection_date.isoformat(),
                        'total_videos': stat.total_videos,
                        'success_rate': stat.success_rate,
                        'processing_time': stat.processing_time_seconds
                    }
                    for stat in results
                ]
        except Exception as e:
            logger.error(f"❌ Error getting collection history: {e}")
            return []


async def main():
    """Main execution function for testing and manual runs"""
    # Get API keys from environment
    api_keys = []
    for i in range(1, 6):  # Support up to 5 API keys
        key = os.getenv(f'YOUTUBE_API_KEY_{i}') or os.getenv('YOUTUBE_API_KEY')
        if key and key not in api_keys:
            api_keys.append(key)
    
    if not api_keys:
        logger.error("❌ No YouTube API keys found in environment variables")
        logger.info("💡 Set YOUTUBE_API_KEY or YOUTUBE_API_KEY_1, YOUTUBE_API_KEY_2, etc.")
        return
    
    logger.info(f"🔑 Found {len(api_keys)} API key(s)")
    
    # Initialize collector
    collector = TrendingDataCollector(
        api_keys=api_keys,
        db_path="trending_data.db",
        data_dir="./data/trending"
    )
    
    # Run collection
    logger.info("🚀 Starting trending data collection...")
    
    # For testing, use fewer regions/categories
    test_regions = ['US', 'GB', 'CA']
    test_categories = ['10', '24', '28']  # Music, Entertainment, Science & Technology
    
    results = await collector.collect_trending_data(
        regions=test_regions,
        categories=test_categories,
        max_results_per_request=25
    )
    
    # Print results
    print("\n" + "="*60)
    print("📊 TRENDING DATA COLLECTION RESULTS")
    print("="*60)
    print(f"📦 Batch ID: {results['batch_id']}")
    print(f"🎥 Total Videos: {results['total_videos_collected']}")
    print(f"🌍 Regions Processed: {results['regions_processed']}")
    print(f"📈 Success Rate: {results['success_rate']:.1f}%")
    print(f"⏱️  Processing Time: {results['processing_time_seconds']:.2f}s")
    print(f"🔥 API Requests: {results['api_requests_made']}")
    print(f"💾 Quota Used: {results['quota_used']}")
    print("="*60)
    
    # Show quota status
    quota_status = collector.get_quota_status()
    print(f"📊 Quota Status: {quota_status['quota_used_today']}/{quota_status['quota_limit']}")
    print(f"🔑 Current API Key: #{quota_status['current_api_key_index'] + 1}")


if __name__ == "__main__":
    asyncio.run(main())
