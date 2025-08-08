#!/usr/bin/env python3
"""
🧠 YOUTUBE INTELLIGENCE MATRIX 🧠
Advanced YouTube Data Collection & Analysis System

This system collects, analyzes, and predicts YouTube trends with
military-grade intelligence gathering capabilities.
"""

import asyncio
import aiohttp
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import googleapiclient.discovery
import googleapiclient.errors
from textblob import TextBlob
import re
import logging
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import hashlib
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VideoMetrics:
    """Complete video performance metrics"""
    video_id: str
    title: str
    channel_id: str
    channel_name: str
    published_at: datetime
    view_count: int
    like_count: int
    comment_count: int
    duration: str
    tags: List[str]
    category_id: str
    thumbnail_url: str
    description: str
    language: str
    
    # Advanced analytics
    engagement_rate: float
    viral_score: float
    retention_estimate: float
    clickbait_score: float
    emotion_score: Dict[str, float]
    trend_alignment: float
    competitor_threat_level: float

@dataclass
class ChannelIntelligence:
    """Complete channel intelligence profile"""
    channel_id: str
    channel_name: str
    subscriber_count: int
    total_views: int
    video_count: int
    created_at: datetime
    
    # Advanced metrics
    growth_rate: float
    engagement_pattern: Dict[str, float]
    content_strategy: Dict[str, Any]
    upload_frequency: float
    audience_demographics: Dict[str, float]
    revenue_estimate: float
    vulnerability_score: float
    competitive_threats: List[str]

class YouTubeIntelligenceMatrix:
    """
    🕷️ ADVANCED YOUTUBE INTELLIGENCE SYSTEM 🕷️
    
    Military-grade intelligence gathering and analysis for YouTube dominance.
    Collects data on competitors, trends, and opportunities.
    """
    
    def __init__(self, api_key: str, db_path: str = "youtube_intelligence.db"):
        self.api_key = api_key
        self.db_path = db_path
        self.youtube = googleapiclient.discovery.build(
            'youtube', 'v3', developerKey=api_key
        )
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Initialize database
        self._initialize_database()
        
        # Trend analysis models
        self.trend_keywords = []
        self.viral_patterns = {}
        self.competitor_profiles = {}
        
        logger.info("🧠 YouTube Intelligence Matrix initialized")
    
    def _initialize_database(self):
        """Initialize SQLite database for intelligence storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Videos table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            channel_id TEXT,
            channel_name TEXT,
            published_at TEXT,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            duration TEXT,
            tags TEXT,
            category_id TEXT,
            description TEXT,
            engagement_rate REAL,
            viral_score REAL,
            collected_at TEXT
        )
        ''')
        
        # Channels table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT,
            subscriber_count INTEGER,
            total_views INTEGER,
            video_count INTEGER,
            created_at TEXT,
            growth_rate REAL,
            revenue_estimate REAL,
            vulnerability_score REAL,
            last_analyzed TEXT
        )
        ''')
        
        # Trends table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            trend_score REAL,
            momentum REAL,
            category TEXT,
            detected_at TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Intelligence database initialized")
    
    async def start_intelligence_gathering(self):
        """Start the complete intelligence gathering operation"""
        logger.info("🚀 Starting intelligence gathering operation...")
        
        self.session = aiohttp.ClientSession()
        
        # Parallel intelligence gathering
        tasks = [
            self.collect_trending_videos(),
            self.analyze_competitor_landscape(),
            self.detect_emerging_trends(),
            self.map_audience_patterns(),
            self.identify_content_gaps(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        await self.session.close()
        
        logger.info("✅ Intelligence gathering operation complete")
        return results
    
    async def collect_trending_videos(self) -> List[VideoMetrics]:
        """Collect and analyze trending videos across all categories"""
        logger.info("📊 Collecting trending videos...")
        
        trending_videos = []
        
        # Get trending videos for each category
        categories = ['1', '10', '15', '17', '19', '20', '22', '23', '24', '25', '26', '27', '28']
        
        for category_id in categories:
            try:
                # Get trending videos
                request = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    chart='mostPopular',
                    regionCode='US',
                    maxResults=50,
                    videoCategoryId=category_id
                )
                
                response = request.execute()
                
                for item in response['items']:
                    video_metrics = await self._analyze_video_deep(item)
                    trending_videos.append(video_metrics)
                    
                    # Store in database
                    self._store_video_intelligence(video_metrics)
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error collecting trending videos for category {category_id}: {e}")
        
        logger.info(f"✅ Collected {len(trending_videos)} trending videos")
        return trending_videos
    
    async def _analyze_video_deep(self, video_data: Dict) -> VideoMetrics:
        """Perform deep analysis of individual videos"""
        snippet = video_data['snippet']
        statistics = video_data['statistics']
        content_details = video_data['contentDetails']
        
        # Basic metrics
        video_id = video_data['id']
        title = snippet['title']
        channel_id = snippet['channelId']
        channel_name = snippet['channelTitle']
        published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
        
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))
        
        duration = content_details['duration']
        tags = snippet.get('tags', [])
        category_id = snippet['categoryId']
        description = snippet['description']
        
        # Advanced analytics
        engagement_rate = self._calculate_engagement_rate(view_count, like_count, comment_count)
        viral_score = await self._calculate_viral_score(video_data)
        retention_estimate = self._estimate_retention(title, description, duration)
        clickbait_score = self._analyze_clickbait_level(title, snippet.get('thumbnails', {}))
        emotion_score = self._analyze_emotional_triggers(title, description)
        trend_alignment = await self._calculate_trend_alignment(title, tags)
        
        return VideoMetrics(
            video_id=video_id,
            title=title,
            channel_id=channel_id,
            channel_name=channel_name,
            published_at=published_at,
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            duration=duration,
            tags=tags,
            category_id=category_id,
            thumbnail_url=snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
            description=description,
            language=snippet.get('defaultLanguage', 'en'),
            engagement_rate=engagement_rate,
            viral_score=viral_score,
            retention_estimate=retention_estimate,
            clickbait_score=clickbait_score,
            emotion_score=emotion_score,
            trend_alignment=trend_alignment,
            competitor_threat_level=0.0  # Will be calculated separately
        )
    
    def _calculate_engagement_rate(self, views: int, likes: int, comments: int) -> float:
        """Calculate advanced engagement rate"""
        if views == 0:
            return 0.0
        
        # Weighted engagement (likes worth more than views, comments worth most)
        engagement_score = (likes * 1.0) + (comments * 3.0)
        return min((engagement_score / views) * 100, 100.0)
    
    async def _calculate_viral_score(self, video_data: Dict) -> float:
        """Calculate viral potential score using multiple factors"""
        snippet = video_data['snippet']
        statistics = video_data['statistics']
        
        # Factors for viral score
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))
        
        # Time since published
        published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
        hours_since_published = (datetime.now(published_at.tzinfo) - published_at).total_seconds() / 3600
        
        # Viral velocity (views per hour)
        if hours_since_published > 0:
            viral_velocity = view_count / hours_since_published
        else:
            viral_velocity = view_count
        
        # Engagement velocity
        total_engagement = like_count + comment_count
        if hours_since_published > 0:
            engagement_velocity = total_engagement / hours_since_published
        else:
            engagement_velocity = total_engagement
        
        # Combine factors (normalize to 0-100 scale)
        viral_score = min(
            (viral_velocity / 1000) * 50 +  # Views per hour component
            (engagement_velocity / 10) * 30 +  # Engagement per hour component
            (self._analyze_clickbait_level(snippet['title'], snippet.get('thumbnails', {})) * 20),  # Clickbait component
            100.0
        )
        
        return viral_score
    
    def _estimate_retention(self, title: str, description: str, duration: str) -> float:
        """Estimate viewer retention based on content analysis"""
        # Convert duration to seconds
        duration_seconds = self._parse_duration(duration)
        
        # Retention factors
        title_hook_score = self._analyze_title_hooks(title)
        description_value_score = self._analyze_description_value(description)
        optimal_length_score = self._calculate_length_score(duration_seconds)
        
        # Combine factors
        retention_estimate = (
            title_hook_score * 0.4 +
            description_value_score * 0.3 +
            optimal_length_score * 0.3
        )
        
        return min(retention_estimate, 100.0)
    
    def _analyze_clickbait_level(self, title: str, thumbnails: Dict) -> float:
        """Analyze clickbait level of title and thumbnail"""
        clickbait_indicators = [
            r'\b(SHOCKING|AMAZING|INCREDIBLE|UNBELIEVABLE|INSANE)\b',
            r'\b(YOU WON\'T BELIEVE|MUST WATCH|GONE WRONG|EPIC FAIL)\b',
            r'\b(TOP \d+|BEST|WORST|ULTIMATE)\b',
            r'[!]{2,}',  # Multiple exclamation marks
            r'[?]{2,}',  # Multiple question marks
            r'\b(CLICKBAIT|VIRAL|TRENDING)\b'
        ]
        
        score = 0
        title_upper = title.upper()
        
        for indicator in clickbait_indicators:
            if re.search(indicator, title_upper):
                score += 15
        
        # Check for emotional words
        emotional_words = ['LOVE', 'HATE', 'FEAR', 'ANGRY', 'EXCITED', 'SURPRISED']
        for word in emotional_words:
            if word in title_upper:
                score += 10
        
        # Check for numbers (lists are clickbait)
        if re.search(r'\d+', title):
            score += 10
        
        return min(score, 100.0)
    
    def _analyze_emotional_triggers(self, title: str, description: str) -> Dict[str, float]:
        """Analyze emotional triggers in content"""
        text = f"{title} {description}"
        blob = TextBlob(text)
        
        # Basic sentiment
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Emotion categories
        emotions = {
            'positive': max(0, polarity * 100),
            'negative': max(0, -polarity * 100),
            'neutral': 100 - abs(polarity * 100),
            'subjective': subjectivity * 100,
            'objective': (1 - subjectivity) * 100
        }
        
        # Advanced emotion detection
        fear_words = ['scary', 'terrifying', 'frightening', 'horror', 'nightmare']
        excitement_words = ['amazing', 'incredible', 'awesome', 'fantastic', 'epic']
        
        text_lower = text.lower()
        
        emotions['fear'] = sum(10 for word in fear_words if word in text_lower)
        emotions['excitement'] = sum(10 for word in excitement_words if word in text_lower)
        
        return emotions
    
    async def _calculate_trend_alignment(self, title: str, tags: List[str]) -> float:
        """Calculate how well content aligns with current trends"""
        # This would integrate with Google Trends API or similar
        # For now, using simplified trend detection
        
        trending_keywords = [
            'ai', 'artificial intelligence', 'crypto', 'nft', 'metaverse',
            'tiktok', 'shorts', 'viral', 'trending', 'challenge',
            'react', 'review', 'unboxing', 'tutorial', 'guide'
        ]
        
        content_text = f"{title} {' '.join(tags)}".lower()
        
        alignment_score = 0
        for keyword in trending_keywords:
            if keyword in content_text:
                alignment_score += 20
        
        return min(alignment_score, 100.0)
    
    async def analyze_competitor_landscape(self) -> List[ChannelIntelligence]:
        """Perform comprehensive competitor analysis"""
        logger.info("🔍 Analyzing competitor landscape...")
        
        competitors = []
        
        # Get top channels in each category
        categories = ['Gaming', 'Entertainment', 'Music', 'Education', 'Technology']
        
        for category in categories:
            try:
                # Search for top channels in category
                search_request = self.youtube.search().list(
                    part='snippet',
                    q=category,
                    type='channel',
                    order='relevance',
                    maxResults=10
                )
                
                search_response = search_request.execute()
                
                for item in search_response['items']:
                    channel_id = item['snippet']['channelId']
                    
                    # Get detailed channel info
                    channel_intelligence = await self._analyze_channel_deep(channel_id)
                    if channel_intelligence:
                        competitors.append(channel_intelligence)
                        self._store_channel_intelligence(channel_intelligence)
                
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error analyzing competitors in {category}: {e}")
        
        logger.info(f"✅ Analyzed {len(competitors)} competitor channels")
        return competitors
    
    async def _analyze_channel_deep(self, channel_id: str) -> Optional[ChannelIntelligence]:
        """Perform deep analysis of competitor channels"""
        try:
            # Get channel details
            channel_request = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=channel_id
            )
            
            channel_response = channel_request.execute()
            
            if not channel_response['items']:
                return None
            
            channel_data = channel_response['items'][0]
            snippet = channel_data['snippet']
            statistics = channel_data['statistics']
            
            # Basic metrics
            channel_name = snippet['title']
            subscriber_count = int(statistics.get('subscriberCount', 0))
            total_views = int(statistics.get('viewCount', 0))
            video_count = int(statistics.get('videoCount', 0))
            created_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
            
            # Advanced analysis
            growth_rate = await self._calculate_growth_rate(channel_id)
            engagement_pattern = await self._analyze_engagement_pattern(channel_id)
            content_strategy = await self._analyze_content_strategy(channel_id)
            upload_frequency = await self._calculate_upload_frequency(channel_id)
            revenue_estimate = self._estimate_channel_revenue(subscriber_count, total_views)
            vulnerability_score = self._assess_channel_vulnerability(channel_data)
            
            return ChannelIntelligence(
                channel_id=channel_id,
                channel_name=channel_name,
                subscriber_count=subscriber_count,
                total_views=total_views,
                video_count=video_count,
                created_at=created_at,
                growth_rate=growth_rate,
                engagement_pattern=engagement_pattern,
                content_strategy=content_strategy,
                upload_frequency=upload_frequency,
                audience_demographics={},  # Would need additional API calls
                revenue_estimate=revenue_estimate,
                vulnerability_score=vulnerability_score,
                competitive_threats=[]
            )
            
        except Exception as e:
            logger.error(f"Error analyzing channel {channel_id}: {e}")
            return None
    
    async def _calculate_growth_rate(self, channel_id: str) -> float:
        """Calculate channel growth rate"""
        # This would require historical data
        # For now, using estimated growth based on recent videos
        
        try:
            # Get recent videos
            search_request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                type='video',
                order='date',
                maxResults=10
            )
            
            response = search_request.execute()
            
            if not response['items']:
                return 0.0
            
            # Calculate average views of recent videos vs older videos
            # This is a simplified estimation
            return 5.5  # Default growth rate percentage
            
        except:
            return 0.0
    
    async def _analyze_engagement_pattern(self, channel_id: str) -> Dict[str, float]:
        """Analyze channel's engagement patterns"""
        try:
            # Get recent videos for engagement analysis
            search_request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                type='video',
                order='date',
                maxResults=20
            )
            
            response = search_request.execute()
            video_ids = [item['id']['videoId'] for item in response['items']]
            
            if not video_ids:
                return {'average_engagement': 0.0}
            
            # Get video statistics
            videos_request = self.youtube.videos().list(
                part='statistics',
                id=','.join(video_ids)
            )
            
            videos_response = videos_request.execute()
            
            engagement_rates = []
            for video in videos_response['items']:
                stats = video['statistics']
                views = int(stats.get('viewCount', 0))
                likes = int(stats.get('likeCount', 0))
                comments = int(stats.get('commentCount', 0))
                
                if views > 0:
                    engagement_rate = ((likes + comments) / views) * 100
                    engagement_rates.append(engagement_rate)
            
            if engagement_rates:
                return {
                    'average_engagement': np.mean(engagement_rates),
                    'engagement_consistency': 100 - np.std(engagement_rates),
                    'peak_engagement': np.max(engagement_rates)
                }
            
        except Exception as e:
            logger.error(f"Error analyzing engagement for {channel_id}: {e}")
        
        return {'average_engagement': 0.0}
    
    async def _analyze_content_strategy(self, channel_id: str) -> Dict[str, Any]:
        """Analyze channel's content strategy"""
        try:
            # Get recent videos
            search_request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                type='video',
                order='date',
                maxResults=50
            )
            
            response = search_request.execute()
            
            titles = [item['snippet']['title'] for item in response['items']]
            
            # Analyze content patterns
            content_themes = self._extract_content_themes(titles)
            title_patterns = self._analyze_title_patterns(titles)
            
            return {
                'content_themes': content_themes,
                'title_patterns': title_patterns,
                'video_count_analyzed': len(titles)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content strategy for {channel_id}: {e}")
            return {}
    
    def _extract_content_themes(self, titles: List[str]) -> Dict[str, int]:
        """Extract common themes from video titles"""
        themes = {}
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were']
        
        for title in titles:
            words = re.findall(r'\b\w+\b', title.lower())
            for word in words:
                if len(word) > 3 and word not in common_words:
                    themes[word] = themes.get(word, 0) + 1
        
        # Return top themes
        return dict(sorted(themes.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _analyze_title_patterns(self, titles: List[str]) -> Dict[str, float]:
        """Analyze patterns in video titles"""
        patterns = {
            'question_titles': 0,
            'numbered_lists': 0,
            'how_to_guides': 0,
            'clickbait_words': 0,
            'emotional_words': 0
        }
        
        for title in titles:
            title_lower = title.lower()
            
            if '?' in title:
                patterns['question_titles'] += 1
            
            if re.search(r'\d+', title):
                patterns['numbered_lists'] += 1
            
            if 'how to' in title_lower:
                patterns['how_to_guides'] += 1
            
            clickbait_words = ['shocking', 'amazing', 'incredible', 'unbelievable']
            if any(word in title_lower for word in clickbait_words):
                patterns['clickbait_words'] += 1
            
            emotional_words = ['love', 'hate', 'best', 'worst', 'epic', 'fail']
            if any(word in title_lower for word in emotional_words):
                patterns['emotional_words'] += 1
        
        # Convert to percentages
        total_titles = len(titles)
        if total_titles > 0:
            for key in patterns:
                patterns[key] = (patterns[key] / total_titles) * 100
        
        return patterns
    
    async def _calculate_upload_frequency(self, channel_id: str) -> float:
        """Calculate channel upload frequency"""
        try:
            # Get videos from last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            search_request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                type='video',
                publishedAfter=thirty_days_ago.isoformat() + 'Z',
                maxResults=50
            )
            
            response = search_request.execute()
            
            # Calculate videos per week
            videos_count = len(response['items'])
            return videos_count / 4.0  # Convert to weekly frequency
            
        except:
            return 0.0
    
    def _estimate_channel_revenue(self, subscribers: int, total_views: int) -> float:
        """Estimate monthly channel revenue"""
        # Industry averages and formulas
        cpm_estimate = 3.5  # Average CPM in dollars
        views_per_month = total_views * 0.1  # Assume 10% of total views happen monthly
        
        # Ad revenue
        ad_revenue = (views_per_month / 1000) * cpm_estimate
        
        # Additional revenue streams (sponsorships, merchandise, etc.)
        if subscribers > 100000:
            additional_revenue = subscribers * 0.02  # $0.02 per subscriber
        elif subscribers > 10000:
            additional_revenue = subscribers * 0.01
        else:
            additional_revenue = 0
        
        total_revenue = ad_revenue + additional_revenue
        
        return max(total_revenue, 0)
    
    def _assess_channel_vulnerability(self, channel_data: Dict) -> float:
        """Assess how vulnerable a channel is to competition"""
        snippet = channel_data['snippet']
        statistics = channel_data['statistics']
        
        vulnerability_factors = []
        
        # Low engagement rate
        subscriber_count = int(statistics.get('subscriberCount', 0))
        total_views = int(statistics.get('viewCount', 0))
        
        if subscriber_count > 0:
            views_per_sub = total_views / subscriber_count
            if views_per_sub < 10:  # Low engagement
                vulnerability_factors.append(25)
        
        # Infrequent uploads (would need recent video analysis)
        vulnerability_factors.append(15)  # Default assumption
        
        # Generic content (would need content analysis)
        vulnerability_factors.append(10)  # Default assumption
        
        # Old channel with declining growth
        created_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
        age_years = (datetime.now(created_at.tzinfo) - created_at).days / 365
        
        if age_years > 5:  # Older channels might be more vulnerable
            vulnerability_factors.append(20)
        
        return min(sum(vulnerability_factors), 100)
    
    async def detect_emerging_trends(self) -> List[Dict[str, Any]]:
        """Detect emerging trends before they become mainstream"""
        logger.info("🔥 Detecting emerging trends...")
        
        trends = []
        
        try:
            # Analyze recent videos for emerging patterns
            search_queries = [
                'trending now', 'viral', 'new trend', 'challenge',
                'AI', 'crypto', 'tech', 'gaming', 'lifestyle'
            ]
            
            for query in search_queries:
                search_request = self.youtube.search().list(
                    part='snippet',
                    q=query,
                    type='video',
                    order='relevance',
                    publishedAfter=(datetime.now() - timedelta(days=7)).isoformat() + 'Z',
                    maxResults=25
                )
                
                response = search_request.execute()
                
                for item in response['items']:
                    trend_data = await self._analyze_trend_potential(item)
                    if trend_data['trend_score'] > 70:
                        trends.append(trend_data)
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error detecting trends: {e}")
        
        # Sort by trend score
        trends.sort(key=lambda x: x['trend_score'], reverse=True)
        
        logger.info(f"✅ Detected {len(trends)} emerging trends")
        return trends[:20]  # Return top 20 trends
    
    async def _analyze_trend_potential(self, video_item: Dict) -> Dict[str, Any]:
        """Analyze the trend potential of a video/topic"""
        snippet = video_item['snippet']
        
        # Get video statistics
        video_id = video_item['id']['videoId']
        
        try:
            video_request = self.youtube.videos().list(
                part='statistics',
                id=video_id
            )
            video_response = video_request.execute()
            
            if video_response['items']:
                statistics = video_response['items'][0]['statistics']
                view_count = int(statistics.get('viewCount', 0))
                like_count = int(statistics.get('likeCount', 0))
                comment_count = int(statistics.get('commentCount', 0))
            else:
                return {'trend_score': 0}
            
        except:
            return {'trend_score': 0}
        
        # Calculate trend potential
        published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
        hours_since_published = (datetime.now(published_at.tzinfo) - published_at).total_seconds() / 3600
        
        if hours_since_published > 0:
            velocity = view_count / hours_since_published
        else:
            velocity = view_count
        
        # Trend score factors
        velocity_score = min((velocity / 1000) * 40, 40)  # Views per hour
        engagement_score = min(((like_count + comment_count) / max(view_count, 1)) * 30 * 100, 30)  # Engagement rate
        recency_score = max(30 - (hours_since_published / 24) * 10, 0)  # Recency bonus
        
        trend_score = velocity_score + engagement_score + recency_score
        
        return {
            'keyword': snippet['title'][:50],
            'trend_score': trend_score,
            'momentum': velocity,
            'category': snippet.get('categoryId', 'Unknown'),
            'video_id': video_id,
            'detected_at': datetime.now().isoformat()
        }
    
    async def map_audience_patterns(self) -> Dict[str, Any]:
        """Map audience behavior patterns"""
        logger.info("👥 Mapping audience patterns...")
        
        # This would integrate with YouTube Analytics API
        # For now, providing structure for audience analysis
        
        patterns = {
            'peak_viewing_hours': [19, 20, 21],  # 7-9 PM
            'peak_days': ['Saturday', 'Sunday'],
            'demographic_preferences': {
                '13-17': ['Gaming', 'Entertainment', 'Music'],
                '18-24': ['Technology', 'Lifestyle', 'Education'],
                '25-34': ['Business', 'Finance', 'Health'],
                '35+': ['News', 'Documentary', 'DIY']
            },
            'engagement_triggers': [
                'Ask questions in titles',
                'Use emotional thumbnails',
                'Create cliffhangers',
                'Promise value upfront'
            ],
            'retention_factors': {
                'hook_within_15_seconds': 0.8,
                'visual_changes_every_3_seconds': 0.7,
                'story_structure': 0.9,
                'call_to_action': 0.6
            }
        }
        
        logger.info("✅ Audience patterns mapped")
        return patterns
    
    async def identify_content_gaps(self) -> List[Dict[str, Any]]:
        """Identify content gaps and opportunities"""
        logger.info("🎯 Identifying content gaps...")
        
        gaps = []
        
        # Popular search terms without enough quality content
        search_terms = [
            'AI tutorial beginner', 'crypto explained simple',
            'make money online 2024', 'productivity hacks',
            'healthy recipes quick', 'workout at home'
        ]
        
        for term in search_terms:
            try:
                search_request = self.youtube.search().list(
                    part='snippet',
                    q=term,
                    type='video',
                    order='relevance',
                    maxResults=10
                )
                
                response = search_request.execute()
                
                # Analyze competition level
                competition_score = len(response['items']) * 10
                
                # Analyze quality of existing content
                quality_scores = []
                for item in response['items']:
                    # Simple quality assessment
                    title_quality = self._assess_title_quality(item['snippet']['title'])
                    quality_scores.append(title_quality)
                
                avg_quality = np.mean(quality_scores) if quality_scores else 0
                
                # Gap opportunity score
                gap_score = max(100 - competition_score - avg_quality, 0)
                
                if gap_score > 50:
                    gaps.append({
                        'keyword': term,
                        'gap_score': gap_score,
                        'competition_level': competition_score,
                        'average_quality': avg_quality,
                        'opportunity': 'HIGH' if gap_score > 75 else 'MEDIUM'
                    })
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error analyzing gap for '{term}': {e}")
        
        logger.info(f"✅ Identified {len(gaps)} content gaps")
        return gaps
    
    def _assess_title_quality(self, title: str) -> float:
        """Assess the quality of a video title"""
        quality_score = 50  # Base score
        
        # Length optimization
        if 40 <= len(title) <= 60:
            quality_score += 20
        
        # Contains numbers (specific, actionable)
        if re.search(r'\d+', title):
            quality_score += 15
        
        # Contains power words
        power_words = ['ultimate', 'complete', 'guide', 'secret', 'proven', 'best']
        if any(word in title.lower() for word in power_words):
            quality_score += 15
        
        return min(quality_score, 100)
    
    def _store_video_intelligence(self, video: VideoMetrics):
        """Store video intelligence in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO videos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            video.video_id, video.title, video.channel_id, video.channel_name,
            video.published_at.isoformat(), video.view_count, video.like_count,
            video.comment_count, video.duration, json.dumps(video.tags),
            video.category_id, video.description, video.engagement_rate,
            video.viral_score, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _store_channel_intelligence(self, channel: ChannelIntelligence):
        """Store channel intelligence in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO channels VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            channel.channel_id, channel.channel_name, channel.subscriber_count,
            channel.total_views, channel.video_count, channel.created_at.isoformat(),
            channel.growth_rate, channel.revenue_estimate, channel.vulnerability_score,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds"""
        # Simple parser for PT#M#S format
        pattern = r'PT(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)
        
        if match:
            minutes = int(match.group(1)) if match.group(1) else 0
            seconds = int(match.group(2)) if match.group(2) else 0
            return minutes * 60 + seconds
        
        return 0
    
    def _analyze_title_hooks(self, title: str) -> float:
        """Analyze title hook strength"""
        hooks = [
            r'^(How to|Why|What|When|Where|Who)',  # Question starters
            r'\b(Secret|Hidden|Unknown|Revealed)\b',  # Mystery
            r'\b(Ultimate|Complete|Best|Top)\b',  # Authority
            r'\b(Quick|Fast|Easy|Simple)\b',  # Convenience
            r'\b(Shocking|Amazing|Incredible)\b'  # Emotion
        ]
        
        score = 30  # Base score
        
        for hook in hooks:
            if re.search(hook, title, re.IGNORECASE):
                score += 15
        
        return min(score, 100)
    
    def _analyze_description_value(self, description: str) -> float:
        """Analyze value proposition in description"""
        value_indicators = [
            'learn', 'discover', 'find out', 'tutorial', 'guide',
            'tips', 'tricks', 'secrets', 'strategy', 'method'
        ]
        
        score = 40  # Base score
        desc_lower = description.lower()
        
        for indicator in value_indicators:
            if indicator in desc_lower:
                score += 10
        
        # Length bonus (detailed descriptions)
        if len(description) > 200:
            score += 20
        
        return min(score, 100)
    
    def _calculate_length_score(self, duration_seconds: int) -> float:
        """Calculate optimal length score"""
        # Optimal lengths for different content types
        if 60 <= duration_seconds <= 300:  # 1-5 minutes (shorts)
            return 95
        elif 300 <= duration_seconds <= 600:  # 5-10 minutes (tutorials)
            return 100
        elif 600 <= duration_seconds <= 1200:  # 10-20 minutes (entertainment)
            return 85
        elif 1200 <= duration_seconds <= 1800:  # 20-30 minutes (deep content)
            return 70
        else:
            return 50  # Too short or too long
    
    async def generate_intelligence_report(self) -> Dict[str, Any]:
        """Generate comprehensive intelligence report"""
        logger.info("📊 Generating intelligence report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'trending_analysis': await self.collect_trending_videos(),
            'competitor_analysis': await self.analyze_competitor_landscape(),
            'trend_predictions': await self.detect_emerging_trends(),
            'audience_insights': await self.map_audience_patterns(),
            'content_opportunities': await self.identify_content_gaps(),
            'recommendations': self._generate_strategic_recommendations()
        }
        
        # Save report
        with open(f"intelligence_report_{int(time.time())}.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("✅ Intelligence report generated")
        return report
    
    def _generate_strategic_recommendations(self) -> List[str]:
        """Generate strategic recommendations based on intelligence"""
        return [
            "Focus on AI and technology content - high trending potential",
            "Optimize for mobile viewing - majority of traffic",
            "Use emotional thumbnails with high contrast colors",
            "Upload during 7-9 PM peak hours",
            "Create 8-12 minute videos for optimal retention",
            "Include trending keywords in first 15 seconds",
            "Ask questions to boost engagement",
            "Use clickbait titles ethically for higher CTR"
        ]

# USAGE EXAMPLE
if __name__ == "__main__":
    async def main():
        # Initialize with YouTube API key
        api_key = "YOUR_YOUTUBE_API_KEY"  # Replace with actual key
        
        intelligence = YouTubeIntelligenceMatrix(api_key)
        
        # Run complete intelligence operation
        await intelligence.start_intelligence_gathering()
        
        # Generate report
        report = await intelligence.generate_intelligence_report()
        
        print("🧠 Intelligence gathering complete!")
        print(f"📊 Report saved with {len(report)} sections")
    
    # Run the intelligence system
    asyncio.run(main())
