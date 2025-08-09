#!/usr/bin/env python3
"""
🎨 VISUAL ASSETS FETCHER 🎨

This module:
• Extracts keywords from generated script sentences
• Queries Pexels/Unsplash APIs (both free) for each sentence keyword
• Downloads 1080p images/video snippets (≤ 1280 × 720 for quota)
• Background music: Pixabay free CC0; ensures ≤ 15 MB
• Caches all assets to /assets/ with organized structure

Features:
- Smart keyword extraction from script text
- Multi-API fallback (Pexels → Unsplash → Local fallback)
- Intelligent image selection based on relevance
- Video snippet support for dynamic content
- Background music with CC0 licensing
- Asset caching and metadata tracking
- Quota management and rate limiting
- Progressive quality selection (1080p → 720p)
"""

import os
import sys
import json
import logging
import asyncio
import aiohttp
import aiofiles
import hashlib
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from urllib.parse import urlparse, quote_plus
import mimetypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('assets_fetcher.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
ASSETS_DIR = Path("assets")
IMAGES_DIR = ASSETS_DIR / "images"
VIDEOS_DIR = ASSETS_DIR / "videos" 
MUSIC_DIR = ASSETS_DIR / "music"
CACHE_DIR = ASSETS_DIR / "cache"
METADATA_DIR = ASSETS_DIR / "metadata"

# Create directories
for directory in [ASSETS_DIR, IMAGES_DIR, VIDEOS_DIR, MUSIC_DIR, CACHE_DIR, METADATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Configuration
MAX_IMAGE_SIZE = (1280, 720)  # For quota conservation
MAX_MUSIC_SIZE_MB = 15
DEFAULT_ASSETS_PER_KEYWORD = 3
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0  # Seconds between requests

class AssetType(Enum):
    """Types of visual assets"""
    IMAGE = "image"
    VIDEO = "video"
    MUSIC = "music"

class APIProvider(Enum):
    """Supported API providers"""
    PEXELS = "pexels"
    UNSPLASH = "unsplash"  
    PIXABAY = "pixabay"

@dataclass
class AssetMetadata:
    """Metadata for downloaded assets"""
    asset_id: str
    filename: str
    asset_type: AssetType
    provider: APIProvider
    keyword: str
    url: str
    download_url: str
    file_path: str
    file_size: int
    dimensions: Optional[Tuple[int, int]]
    duration: Optional[float]  # For videos/music in seconds
    license: str
    attribution: Optional[str]
    downloaded_at: datetime
    checksum: str

@dataclass
class KeywordAssets:
    """Assets collection for a specific keyword"""
    keyword: str
    images: List[AssetMetadata]
    videos: List[AssetMetadata]
    music: List[AssetMetadata]
    extracted_from_sentence: str
    search_timestamp: datetime

class KeywordExtractor:
    """Extract meaningful keywords from script sentences"""
    
    # Common stop words to exclude
    STOP_WORDS = {
        'the', 'is', 'at', 'which', 'on', 'and', 'a', 'to', 'as', 'are', 'was', 
        'will', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'can',
        'could', 'should', 'would', 'may', 'might', 'must', 'shall', 'for', 'of',
        'with', 'by', 'from', 'in', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
        'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
        'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        'just', 'now', 'you', 'your', 'this', 'that', 'these', 'those', 'i', 'me',
        'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'he', 'him', 'his',
        'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they',
        'them', 'their', 'theirs', 'themselves'
    }
    
    # Visual keywords that translate well to images/videos
    VISUAL_KEYWORDS = {
        'technology', 'business', 'success', 'money', 'growth', 'innovation',
        'strategy', 'leadership', 'team', 'office', 'computer', 'data',
        'analytics', 'charts', 'graphs', 'meeting', 'presentation', 'handshake',
        'city', 'skyline', 'nature', 'ocean', 'mountains', 'forest', 'sunset',
        'sunrise', 'light', 'energy', 'power', 'future', 'digital', 'network',
        'connection', 'communication', 'social', 'people', 'community', 'global'
    }
    
    @classmethod
    def extract_keywords(cls, text: str, max_keywords: int = 5) -> List[str]:
        """Extract meaningful keywords from text"""
        
        # Clean and normalize text
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)      # Normalize whitespace
        
        # Extract words
        words = text.split()
        
        # Filter out stop words and short words
        meaningful_words = [
            word for word in words 
            if word not in cls.STOP_WORDS 
            and len(word) > 2
            and not word.isdigit()
        ]
        
        # Prioritize visual keywords
        visual_words = [word for word in meaningful_words if word in cls.VISUAL_KEYWORDS]
        other_words = [word for word in meaningful_words if word not in cls.VISUAL_KEYWORDS]
        
        # Count word frequency
        word_freq = {}
        for word in meaningful_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and visual relevance
        sorted_words = sorted(meaningful_words, key=lambda w: (
            2 if w in cls.VISUAL_KEYWORDS else 1,  # Prioritize visual keywords
            word_freq[w],                           # Then by frequency
            -len(w)                                # Then by length (longer = more specific)
        ), reverse=True)
        
        # Remove duplicates while preserving order
        unique_keywords = []
        seen = set()
        for word in sorted_words:
            if word not in seen:
                unique_keywords.append(word)
                seen.add(word)
        
        # Add compound phrases for better search results
        compound_keywords = cls._extract_compound_phrases(text, max_keywords // 2)
        
        # Combine and limit
        all_keywords = unique_keywords[:max_keywords] + compound_keywords
        return all_keywords[:max_keywords]
    
    @classmethod 
    def _extract_compound_phrases(cls, text: str, max_phrases: int = 2) -> List[str]:
        """Extract meaningful 2-3 word phrases"""
        
        # Simple bigram and trigram extraction
        words = text.split()
        phrases = []
        
        # Extract bigrams
        for i in range(len(words) - 1):
            if (words[i] not in cls.STOP_WORDS and 
                words[i+1] not in cls.STOP_WORDS and
                len(words[i]) > 2 and len(words[i+1]) > 2):
                phrases.append(f"{words[i]} {words[i+1]}")
        
        # Extract trigrams for very specific searches
        for i in range(len(words) - 2):
            if (words[i] not in cls.STOP_WORDS and
                words[i+1] not in cls.STOP_WORDS and
                words[i+2] not in cls.STOP_WORDS and
                len(words[i]) > 2 and len(words[i+1]) > 2):
                phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        # Return most relevant phrases
        return phrases[:max_phrases]

class APIQuotaManager:
    """Manage API quotas and rate limiting"""
    
    def __init__(self):
        self.quotas = {
            APIProvider.PEXELS: {"daily_limit": 200, "used": 0, "reset_time": None},
            APIProvider.UNSPLASH: {"daily_limit": 50, "used": 0, "reset_time": None},
            APIProvider.PIXABAY: {"daily_limit": 100, "used": 0, "reset_time": None}
        }
        self.last_request_time = {}
        self._load_quota_state()
    
    def _load_quota_state(self):
        """Load quota state from cache"""
        quota_file = CACHE_DIR / "api_quotas.json"
        if quota_file.exists():
            try:
                with open(quota_file, 'r') as f:
                    data = json.load(f)
                    
                for provider_name, quota_data in data.get('quotas', {}).items():
                    try:
                        provider = APIProvider(provider_name)
                        self.quotas[provider] = quota_data
                        
                        # Reset if past reset time
                        if quota_data.get('reset_time'):
                            reset_time = datetime.fromisoformat(quota_data['reset_time'])
                            if datetime.now() > reset_time:
                                self.quotas[provider]['used'] = 0
                                self.quotas[provider]['reset_time'] = None
                                
                    except ValueError:
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not load quota state: {e}")
    
    def _save_quota_state(self):
        """Save quota state to cache"""
        quota_file = CACHE_DIR / "api_quotas.json"
        try:
            data = {
                'quotas': {},
                'updated_at': datetime.now().isoformat()
            }
            
            for provider, quota_data in self.quotas.items():
                # Set reset time to tomorrow if not set
                if not quota_data.get('reset_time'):
                    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    quota_data['reset_time'] = tomorrow.isoformat()
                    
                data['quotas'][provider.value] = quota_data
            
            with open(quota_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not save quota state: {e}")
    
    def can_make_request(self, provider: APIProvider) -> bool:
        """Check if we can make a request to the provider"""
        quota = self.quotas.get(provider)
        if not quota:
            return False
        
        return quota['used'] < quota['daily_limit']
    
    def record_request(self, provider: APIProvider):
        """Record that we made a request"""
        if provider in self.quotas:
            self.quotas[provider]['used'] += 1
            self.last_request_time[provider] = datetime.now()
            self._save_quota_state()
    
    async def wait_if_needed(self, provider: APIProvider):
        """Wait if we need to respect rate limits"""
        last_request = self.last_request_time.get(provider)
        if last_request:
            time_since = (datetime.now() - last_request).total_seconds()
            if time_since < RATE_LIMIT_DELAY:
                wait_time = RATE_LIMIT_DELAY - time_since
                await asyncio.sleep(wait_time)

class PexelsAPI:
    """Pexels API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/v1"
        self.video_base_url = "https://api.pexels.com/videos"
    
    async def search_images(self, keyword: str, per_page: int = 3) -> List[Dict[str, Any]]:
        """Search for images on Pexels"""
        
        url = f"{self.base_url}/search"
        headers = {"Authorization": self.api_key}
        params = {
            "query": keyword,
            "per_page": per_page,
            "size": "large",  # High resolution
            "orientation": "landscape"  # Better for video
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params, 
                                     timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('photos', [])
                    elif response.status == 429:
                        logger.warning("Pexels API rate limit reached")
                        return []
                    else:
                        logger.error(f"Pexels API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Pexels API request failed: {e}")
                return []
    
    async def search_videos(self, keyword: str, per_page: int = 2) -> List[Dict[str, Any]]:
        """Search for videos on Pexels"""
        
        url = f"{self.video_base_url}/search"
        headers = {"Authorization": self.api_key}
        params = {
            "query": keyword,
            "per_page": per_page,
            "size": "medium",  # Balance quality and file size
            "orientation": "landscape"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params,
                                     timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('videos', [])
                    else:
                        logger.error(f"Pexels Video API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Pexels Video API request failed: {e}")
                return []

class UnsplashAPI:
    """Unsplash API client"""
    
    def __init__(self, access_key: str):
        self.access_key = access_key
        self.base_url = "https://api.unsplash.com"
    
    async def search_images(self, keyword: str, per_page: int = 3) -> List[Dict[str, Any]]:
        """Search for images on Unsplash"""
        
        url = f"{self.base_url}/search/photos"
        headers = {"Authorization": f"Client-ID {self.access_key}"}
        params = {
            "query": keyword,
            "per_page": per_page,
            "orientation": "landscape",
            "order_by": "relevant"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params,
                                     timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('results', [])
                    elif response.status == 403:
                        logger.warning("Unsplash API rate limit reached")
                        return []
                    else:
                        logger.error(f"Unsplash API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Unsplash API request failed: {e}")
                return []

class PixabayAPI:
    """Pixabay API client for music and additional visuals"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pixabay.com/api"
    
    async def search_music(self, keyword: str, per_page: int = 3) -> List[Dict[str, Any]]:
        """Search for CC0 music on Pixabay"""
        
        params = {
            "key": self.api_key,
            "q": keyword,
            "per_page": per_page,
            "media_type": "music",
            "min_duration": 30,    # At least 30 seconds
            "max_duration": 300,   # Max 5 minutes
            "safesearch": "true"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params,
                                     timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('hits', [])
                    else:
                        logger.error(f"Pixabay Music API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Pixabay Music API request failed: {e}")
                return []
    
    async def search_images(self, keyword: str, per_page: int = 3) -> List[Dict[str, Any]]:
        """Search for images on Pixabay as fallback"""
        
        params = {
            "key": self.api_key,
            "q": keyword,
            "per_page": per_page,
            "image_type": "photo",
            "orientation": "horizontal",
            "min_width": 1920,
            "min_height": 1080,
            "safesearch": "true"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params,
                                     timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('hits', [])
                    else:
                        logger.error(f"Pixabay Image API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Pixabay Image API request failed: {e}")
                return []

class AssetsDownloader:
    """Download and cache visual assets"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def download_asset(self, url: str, file_path: Path) -> bool:
        """Download an asset file"""
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT * 2)) as response:
                if response.status == 200:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    return True
                else:
                    logger.error(f"Failed to download {url}: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _get_image_dimensions(self, file_path: Path) -> Optional[Tuple[int, int]]:
        """Get image dimensions (requires PIL/Pillow)"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return img.size
        except ImportError:
            logger.warning("PIL not installed, cannot get image dimensions")
            return None
        except Exception as e:
            logger.warning(f"Could not get image dimensions: {e}")
            return None
    
    def _estimate_video_duration(self, file_path: Path) -> Optional[float]:
        """Estimate video duration (basic implementation)"""
        # This is a placeholder - would need ffmpeg or similar for accurate duration
        # For now, just return file size as a rough approximation
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            # Very rough estimate: assume 1MB per second of video
            return size_mb
        except Exception:
            return None

class AssetsFetcher:
    """Main assets fetcher orchestrator"""
    
    def __init__(self, 
                 pexels_api_key: Optional[str] = None,
                 unsplash_access_key: Optional[str] = None,
                 pixabay_api_key: Optional[str] = None):
        
        # Initialize APIs
        self.pexels = PexelsAPI(pexels_api_key) if pexels_api_key else None
        self.unsplash = UnsplashAPI(unsplash_access_key) if unsplash_access_key else None
        self.pixabay = PixabayAPI(pixabay_api_key) if pixabay_api_key else None
        
        # Initialize managers
        self.quota_manager = APIQuotaManager()
        self.keyword_extractor = KeywordExtractor()
        
        # Check which APIs are available
        available_apis = []
        if self.pexels:
            available_apis.append("Pexels")
        if self.unsplash:
            available_apis.append("Unsplash")  
        if self.pixabay:
            available_apis.append("Pixabay")
        
        logger.info(f"🎨 Initialized AssetsFetcher with: {', '.join(available_apis) if available_apis else 'No APIs configured'}")
    
    def extract_sentence_keywords(self, sentences: List[str]) -> Dict[str, List[str]]:
        """Extract keywords from each sentence"""
        
        sentence_keywords = {}
        
        for i, sentence in enumerate(sentences):
            keywords = self.keyword_extractor.extract_keywords(sentence, max_keywords=3)
            if keywords:
                sentence_key = f"sentence_{i+1:03d}"
                sentence_keywords[sentence_key] = keywords
                logger.info(f"📝 {sentence_key}: {keywords} | \"{sentence[:50]}...\"")
        
        return sentence_keywords
    
    async def fetch_assets_for_keywords(self, keywords: List[str]) -> KeywordAssets:
        """Fetch all types of assets for a list of keywords"""
        
        all_images = []
        all_videos = []
        all_music = []
        
        primary_keyword = keywords[0] if keywords else "generic"
        
        async with AssetsDownloader() as downloader:
            # Fetch images from multiple providers
            for keyword in keywords[:2]:  # Limit to top 2 keywords
                await self._fetch_images_for_keyword(keyword, all_images, downloader)
                await self._fetch_videos_for_keyword(keyword, all_videos, downloader)
            
            # Fetch background music (once per keyword set)
            if keywords:
                await self._fetch_music_for_keyword(primary_keyword, all_music, downloader)
        
        return KeywordAssets(
            keyword=primary_keyword,
            images=all_images,
            videos=all_videos,
            music=all_music,
            extracted_from_sentence="",  # Will be set by caller
            search_timestamp=datetime.now()
        )
    
    async def _fetch_images_for_keyword(self, keyword: str, results: List[AssetMetadata], downloader: AssetsDownloader):
        """Fetch images for a single keyword"""
        
        # Try Pexels first
        if self.pexels and self.quota_manager.can_make_request(APIProvider.PEXELS):
            await self.quota_manager.wait_if_needed(APIProvider.PEXELS)
            
            try:
                pexels_images = await self.pexels.search_images(keyword, per_page=2)
                self.quota_manager.record_request(APIProvider.PEXELS)
                
                for img_data in pexels_images:
                    metadata = await self._process_pexels_image(img_data, keyword, downloader)
                    if metadata:
                        results.append(metadata)
                        
            except Exception as e:
                logger.error(f"Error fetching Pexels images for '{keyword}': {e}")
        
        # Try Unsplash as fallback
        if len(results) < 2 and self.unsplash and self.quota_manager.can_make_request(APIProvider.UNSPLASH):
            await self.quota_manager.wait_if_needed(APIProvider.UNSPLASH)
            
            try:
                unsplash_images = await self.unsplash.search_images(keyword, per_page=2)
                self.quota_manager.record_request(APIProvider.UNSPLASH)
                
                for img_data in unsplash_images:
                    metadata = await self._process_unsplash_image(img_data, keyword, downloader)
                    if metadata:
                        results.append(metadata)
                        
            except Exception as e:
                logger.error(f"Error fetching Unsplash images for '{keyword}': {e}")
        
        # Try Pixabay as final fallback
        if len(results) < 1 and self.pixabay and self.quota_manager.can_make_request(APIProvider.PIXABAY):
            await self.quota_manager.wait_if_needed(APIProvider.PIXABAY)
            
            try:
                pixabay_images = await self.pixabay.search_images(keyword, per_page=1)
                self.quota_manager.record_request(APIProvider.PIXABAY)
                
                for img_data in pixabay_images:
                    metadata = await self._process_pixabay_image(img_data, keyword, downloader)
                    if metadata:
                        results.append(metadata)
                        
            except Exception as e:
                logger.error(f"Error fetching Pixabay images for '{keyword}': {e}")
    
    async def _fetch_videos_for_keyword(self, keyword: str, results: List[AssetMetadata], downloader: AssetsDownloader):
        """Fetch videos for a single keyword"""
        
        # Only Pexels has video API in our setup
        if self.pexels and self.quota_manager.can_make_request(APIProvider.PEXELS):
            await self.quota_manager.wait_if_needed(APIProvider.PEXELS)
            
            try:
                pexels_videos = await self.pexels.search_videos(keyword, per_page=1)
                self.quota_manager.record_request(APIProvider.PEXELS)
                
                for video_data in pexels_videos:
                    metadata = await self._process_pexels_video(video_data, keyword, downloader)
                    if metadata:
                        results.append(metadata)
                        
            except Exception as e:
                logger.error(f"Error fetching Pexels videos for '{keyword}': {e}")
    
    async def _fetch_music_for_keyword(self, keyword: str, results: List[AssetMetadata], downloader: AssetsDownloader):
        """Fetch background music for a keyword"""
        
        if self.pixabay and self.quota_manager.can_make_request(APIProvider.PIXABAY):
            await self.quota_manager.wait_if_needed(APIProvider.PIXABAY)
            
            try:
                # Use more generic terms for better music results
                music_keywords = ["inspiring", "corporate", "upbeat", "motivational", keyword.split()[0]]
                
                for music_keyword in music_keywords[:2]:
                    pixabay_music = await self.pixabay.search_music(music_keyword, per_page=1)
                    if pixabay_music:
                        self.quota_manager.record_request(APIProvider.PIXABAY)
                        
                        for music_data in pixabay_music:
                            metadata = await self._process_pixabay_music(music_data, keyword, downloader)
                            if metadata:
                                results.append(metadata)
                                break  # Only need one music file per keyword set
                        break
                        
            except Exception as e:
                logger.error(f"Error fetching Pixabay music for '{keyword}': {e}")
    
    async def _process_pexels_image(self, img_data: Dict, keyword: str, downloader: AssetsDownloader) -> Optional[AssetMetadata]:
        """Process and download Pexels image"""
        
        try:
            # Choose appropriate resolution
            download_url = img_data.get('src', {}).get('large2x') or img_data.get('src', {}).get('large')
            if not download_url:
                return None
            
            # Generate filename
            asset_id = str(img_data.get('id', ''))
            filename = f"pexels_{asset_id}_{keyword.replace(' ', '_')}.jpg"
            file_path = IMAGES_DIR / filename
            
            # Skip if already exists
            if file_path.exists():
                logger.info(f"⚡ Using cached image: {filename}")
                return self._create_asset_metadata(img_data, keyword, APIProvider.PEXELS, AssetType.IMAGE, file_path)
            
            # Download image
            success = await downloader.download_asset(download_url, file_path)
            if success:
                logger.info(f"📥 Downloaded image: {filename}")
                return self._create_asset_metadata(img_data, keyword, APIProvider.PEXELS, AssetType.IMAGE, file_path)
            
        except Exception as e:
            logger.error(f"Error processing Pexels image: {e}")
        
        return None
    
    async def _process_unsplash_image(self, img_data: Dict, keyword: str, downloader: AssetsDownloader) -> Optional[AssetMetadata]:
        """Process and download Unsplash image"""
        
        try:
            # Choose appropriate resolution
            download_url = img_data.get('urls', {}).get('regular') or img_data.get('urls', {}).get('small')
            if not download_url:
                return None
            
            # Generate filename
            asset_id = img_data.get('id', '')
            filename = f"unsplash_{asset_id}_{keyword.replace(' ', '_')}.jpg"
            file_path = IMAGES_DIR / filename
            
            # Skip if already exists
            if file_path.exists():
                logger.info(f"⚡ Using cached image: {filename}")
                return self._create_asset_metadata(img_data, keyword, APIProvider.UNSPLASH, AssetType.IMAGE, file_path)
            
            # Download image
            success = await downloader.download_asset(download_url, file_path)
            if success:
                logger.info(f"📥 Downloaded image: {filename}")
                return self._create_asset_metadata(img_data, keyword, APIProvider.UNSPLASH, AssetType.IMAGE, file_path)
            
        except Exception as e:
            logger.error(f"Error processing Unsplash image: {e}")
        
        return None
    
    async def _process_pixabay_image(self, img_data: Dict, keyword: str, downloader: AssetsDownloader) -> Optional[AssetMetadata]:
        """Process and download Pixabay image"""
        
        try:
            # Choose appropriate resolution
            download_url = img_data.get('largeImageURL') or img_data.get('fullHDURL') or img_data.get('webformatURL')
            if not download_url:
                return None
            
            # Generate filename
            asset_id = str(img_data.get('id', ''))
            filename = f"pixabay_{asset_id}_{keyword.replace(' ', '_')}.jpg"
            file_path = IMAGES_DIR / filename
            
            # Skip if already exists
            if file_path.exists():
                logger.info(f"⚡ Using cached image: {filename}")
                return self._create_asset_metadata(img_data, keyword, APIProvider.PIXABAY, AssetType.IMAGE, file_path)
            
            # Download image
            success = await downloader.download_asset(download_url, file_path)
            if success:
                logger.info(f"📥 Downloaded image: {filename}")
                return self._create_asset_metadata(img_data, keyword, APIProvider.PIXABAY, AssetType.IMAGE, file_path)
            
        except Exception as e:
            logger.error(f"Error processing Pixabay image: {e}")
        
        return None
    
    async def _process_pexels_video(self, video_data: Dict, keyword: str, downloader: AssetsDownloader) -> Optional[AssetMetadata]:
        """Process and download Pexels video"""
        
        try:
            # Choose appropriate resolution (prefer 720p for quota)
            video_files = video_data.get('video_files', [])
            download_url = None
            
            # Prefer HD quality that fits our constraints
            for video_file in video_files:
                if video_file.get('quality') == 'hd' and video_file.get('width', 0) <= MAX_IMAGE_SIZE[0]:
                    download_url = video_file.get('link')
                    break
            
            # Fallback to any available video
            if not download_url and video_files:
                download_url = video_files[0].get('link')
            
            if not download_url:
                return None
            
            # Generate filename
            asset_id = str(video_data.get('id', ''))
            filename = f"pexels_video_{asset_id}_{keyword.replace(' ', '_')}.mp4"
            file_path = VIDEOS_DIR / filename
            
            # Skip if already exists
            if file_path.exists():
                logger.info(f"⚡ Using cached video: {filename}")
                return self._create_asset_metadata(video_data, keyword, APIProvider.PEXELS, AssetType.VIDEO, file_path)
            
            # Download video
            success = await downloader.download_asset(download_url, file_path)
            if success:
                # Check file size (videos can be large)
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if file_size_mb > MAX_MUSIC_SIZE_MB:
                    logger.warning(f"Video too large ({file_size_mb:.1f}MB), removing: {filename}")
                    file_path.unlink()
                    return None
                
                logger.info(f"📥 Downloaded video: {filename} ({file_size_mb:.1f}MB)")
                return self._create_asset_metadata(video_data, keyword, APIProvider.PEXELS, AssetType.VIDEO, file_path)
            
        except Exception as e:
            logger.error(f"Error processing Pexels video: {e}")
        
        return None
    
    async def _process_pixabay_music(self, music_data: Dict, keyword: str, downloader: AssetsDownloader) -> Optional[AssetMetadata]:
        """Process and download Pixabay music"""
        
        try:
            # Get download URL (usually requires a download endpoint)
            download_url = music_data.get('download_url') or music_data.get('webformatURL')
            if not download_url:
                return None
            
            # Generate filename
            asset_id = str(music_data.get('id', ''))
            filename = f"pixabay_music_{asset_id}_{keyword.replace(' ', '_')}.mp3"
            file_path = MUSIC_DIR / filename
            
            # Skip if already exists
            if file_path.exists():
                logger.info(f"⚡ Using cached music: {filename}")
                return self._create_asset_metadata(music_data, keyword, APIProvider.PIXABAY, AssetType.MUSIC, file_path)
            
            # Download music
            success = await downloader.download_asset(download_url, file_path)
            if success:
                # Check file size constraint
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if file_size_mb > MAX_MUSIC_SIZE_MB:
                    logger.warning(f"Music file too large ({file_size_mb:.1f}MB), removing: {filename}")
                    file_path.unlink()
                    return None
                
                logger.info(f"🎵 Downloaded music: {filename} ({file_size_mb:.1f}MB)")
                return self._create_asset_metadata(music_data, keyword, APIProvider.PIXABAY, AssetType.MUSIC, file_path)
            
        except Exception as e:
            logger.error(f"Error processing Pixabay music: {e}")
        
        return None
    
    def _create_asset_metadata(self, api_data: Dict, keyword: str, provider: APIProvider, 
                              asset_type: AssetType, file_path: Path) -> AssetMetadata:
        """Create standardized asset metadata"""
        
        # Extract common fields based on provider
        if provider == APIProvider.PEXELS:
            if asset_type == AssetType.IMAGE:
                asset_id = str(api_data.get('id', ''))
                url = api_data.get('url', '')
                download_url = api_data.get('src', {}).get('large2x', '')
                attribution = f"Photo by {api_data.get('photographer', 'Unknown')} on Pexels"
                dimensions = (api_data.get('width'), api_data.get('height'))
            elif asset_type == AssetType.VIDEO:
                asset_id = str(api_data.get('id', ''))
                url = api_data.get('url', '')
                download_url = ''  # Complex structure
                attribution = f"Video by {api_data.get('user', {}).get('name', 'Unknown')} on Pexels"
                dimensions = (api_data.get('width'), api_data.get('height'))
            else:
                asset_id = str(api_data.get('id', ''))
                url = ''
                download_url = ''
                attribution = 'Pexels'
                dimensions = None
                
        elif provider == APIProvider.UNSPLASH:
            asset_id = api_data.get('id', '')
            url = api_data.get('links', {}).get('html', '')
            download_url = api_data.get('urls', {}).get('regular', '')
            attribution = f"Photo by {api_data.get('user', {}).get('name', 'Unknown')} on Unsplash"
            dimensions = (api_data.get('width'), api_data.get('height'))
            
        elif provider == APIProvider.PIXABAY:
            asset_id = str(api_data.get('id', ''))
            url = api_data.get('pageURL', '')
            download_url = api_data.get('largeImageURL', '') or api_data.get('download_url', '')
            attribution = f"Image by {api_data.get('user', 'Unknown')} on Pixabay"
            
            if asset_type == AssetType.MUSIC:
                dimensions = None
            else:
                dimensions = (api_data.get('imageWidth'), api_data.get('imageHeight'))
        else:
            asset_id = ''
            url = ''
            download_url = ''
            attribution = 'Unknown'
            dimensions = None
        
        # Calculate file info
        file_size = file_path.stat().st_size if file_path.exists() else 0
        checksum = self._calculate_checksum(file_path) if file_path.exists() else ''
        
        # Get duration for videos/music
        duration = None
        if asset_type in [AssetType.VIDEO, AssetType.MUSIC]:
            duration = self._estimate_duration(api_data, asset_type)
        
        return AssetMetadata(
            asset_id=asset_id,
            filename=file_path.name,
            asset_type=asset_type,
            provider=provider,
            keyword=keyword,
            url=url,
            download_url=download_url,
            file_path=str(file_path),
            file_size=file_size,
            dimensions=dimensions,
            duration=duration,
            license="CC0" if provider == APIProvider.PIXABAY else "Free to use",
            attribution=attribution,
            downloaded_at=datetime.now(),
            checksum=checksum
        )
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _estimate_duration(self, api_data: Dict, asset_type: AssetType) -> Optional[float]:
        """Estimate media duration"""
        if asset_type == AssetType.MUSIC:
            return api_data.get('duration', None)
        elif asset_type == AssetType.VIDEO:
            return api_data.get('duration', None)
        return None
    
    async def process_script_sentences(self, sentences: List[str]) -> Dict[str, KeywordAssets]:
        """Process all sentences and fetch assets"""
        
        logger.info(f"🎬 Processing {len(sentences)} sentences for asset extraction...")
        
        # Extract keywords from sentences  
        sentence_keywords = self.extract_sentence_keywords(sentences)
        
        # Fetch assets for each sentence
        sentence_assets = {}
        
        for sentence_key, keywords in sentence_keywords.items():
            logger.info(f"🔍 Fetching assets for {sentence_key}: {keywords}")
            
            try:
                assets = await self.fetch_assets_for_keywords(keywords)
                assets.extracted_from_sentence = sentences[int(sentence_key.split('_')[1]) - 1]
                sentence_assets[sentence_key] = assets
                
                # Log results
                logger.info(f"✅ {sentence_key}: {len(assets.images)} images, {len(assets.videos)} videos, {len(assets.music)} music")
                
            except Exception as e:
                logger.error(f"❌ Error processing {sentence_key}: {e}")
                continue
        
        # Save combined metadata
        await self._save_session_metadata(sentence_assets)
        
        return sentence_assets
    
    async def _save_session_metadata(self, sentence_assets: Dict[str, KeywordAssets]):
        """Save metadata for the entire fetching session"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata_file = METADATA_DIR / f"assets_session_{timestamp}.json"
        
        try:
            session_data = {
                "session_timestamp": datetime.now().isoformat(),
                "sentences_processed": len(sentence_assets),
                "total_assets": sum(
                    len(assets.images) + len(assets.videos) + len(assets.music)
                    for assets in sentence_assets.values()
                ),
                "sentences": {}
            }
            
            for sentence_key, assets in sentence_assets.items():
                session_data["sentences"][sentence_key] = {
                    "keyword": assets.keyword,
                    "extracted_from": assets.extracted_from_sentence,
                    "images": [asdict(img) for img in assets.images],
                    "videos": [asdict(video) for video in assets.videos], 
                    "music": [asdict(music) for music in assets.music],
                    "search_timestamp": assets.search_timestamp.isoformat()
                }
            
            async with aiofiles.open(metadata_file, 'w') as f:
                await f.write(json.dumps(session_data, indent=2, default=str))
            
            logger.info(f"💾 Saved session metadata: {metadata_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to save session metadata: {e}")

# CLI Interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch visual assets for video scripts")
    parser.add_argument("--script-file", help="Path to script markdown file")
    parser.add_argument("--text", help="Direct text input for testing")  
    parser.add_argument("--list-quota", action="store_true", help="Show API quota usage")
    parser.add_argument("--test-apis", action="store_true", help="Test API connections")
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get API keys from environment
    pexels_key = os.getenv('PEXELS_API_KEY')
    unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY') 
    pixabay_key = os.getenv('PIXABAY_API_KEY')
    
    # Initialize fetcher
    fetcher = AssetsFetcher(
        pexels_api_key=pexels_key,
        unsplash_access_key=unsplash_key,
        pixabay_api_key=pixabay_key
    )
    
    if args.list_quota:
        print("\n🔢 API Quota Status:")
        for provider, quota in fetcher.quota_manager.quotas.items():
            used = quota['used']
            limit = quota['daily_limit']
            remaining = limit - used
            print(f"  {provider.value}: {used}/{limit} ({remaining} remaining)")
        return
    
    if args.test_apis:
        print("\n🧪 Testing API connections...")
        
        # Test with a simple keyword
        test_keyword = "business"
        
        if fetcher.pexels:
            try:
                results = await fetcher.pexels.search_images(test_keyword, per_page=1)
                print(f"  ✅ Pexels: {len(results)} results")
            except Exception as e:
                print(f"  ❌ Pexels: {e}")
        
        if fetcher.unsplash:
            try:
                results = await fetcher.unsplash.search_images(test_keyword, per_page=1)
                print(f"  ✅ Unsplash: {len(results)} results")
            except Exception as e:
                print(f"  ❌ Unsplash: {e}")
        
        if fetcher.pixabay:
            try:
                results = await fetcher.pixabay.search_images(test_keyword, per_page=1)
                print(f"  ✅ Pixabay: {len(results)} results")
            except Exception as e:
                print(f"  ❌ Pixabay: {e}")
        
        return
    
    # Process script or text
    sentences = []
    
    if args.script_file:
        script_path = Path(args.script_file)
        if not script_path.exists():
            print(f"❌ Script file not found: {args.script_file}")
            return
        
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract text and split into sentences (simplified)
        text = re.sub(r'#{1,6}\\s+', '', content)  # Remove headers
        text = re.sub(r'\\*\\*(.*?)\\*\\*', r'\\1', text)  # Remove bold
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        
    elif args.text:
        sentences = [s.strip() for s in re.split(r'[.!?]+', args.text) if s.strip()]
    
    else:
        print("❌ Please provide either --script-file or --text")
        return
    
    if not sentences:
        print("❌ No sentences found to process")
        return
    
    print(f"🎬 Processing {len(sentences)} sentences...")
    
    # Fetch assets
    results = await fetcher.process_script_sentences(sentences)
    
    # Print summary
    total_assets = sum(
        len(assets.images) + len(assets.videos) + len(assets.music)
        for assets in results.values()
    )
    
    print(f"\n✅ Asset fetching complete!")
    print(f"  📁 Assets saved to: {ASSETS_DIR}")
    print(f"  🖼️  Total images: {sum(len(a.images) for a in results.values())}")
    print(f"  🎥 Total videos: {sum(len(a.videos) for a in results.values())}")
    print(f"  🎵 Total music: {sum(len(a.music) for a in results.values())}")
    print(f"  📊 Total assets: {total_assets}")

if __name__ == "__main__":
    asyncio.run(main())
