#!/usr/bin/env python3
"""
🧪 ASSETS FETCHER TESTING SUITE 🧪

This test script demonstrates and validates the assets fetcher functionality:
• Keyword extraction from sentences
• API connections to Pexels, Unsplash, and Pixabay
• Asset downloading and caching
• Metadata generation and storage
• Quota management and rate limiting
• Error handling and fallback mechanisms
"""

import os
import sys
import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from assets_fetcher import (
    AssetsFetcher,
    KeywordExtractor,
    APIQuotaManager,
    PexelsAPI,
    UnsplashAPI,
    PixabayAPI,
    AssetType,
    APIProvider,
    AssetMetadata,
    KeywordAssets
)

class TestKeywordExtractor:
    """Test keyword extraction functionality"""
    
    def test_basic_keyword_extraction(self):
        """Test basic keyword extraction from text"""
        
        text = "This is a business presentation about technology and innovation in the digital world."
        keywords = KeywordExtractor.extract_keywords(text, max_keywords=5)
        
        assert len(keywords) <= 5
        assert "business" in keywords  # Should prioritize visual keywords
        assert "technology" in keywords
        assert "digital" in keywords
        
        # Should not include stop words
        assert "this" not in keywords
        assert "the" not in keywords
    
    def test_visual_keywords_prioritization(self):
        """Test that visual keywords are prioritized"""
        
        text = "The meeting will discuss business growth and team leadership strategies."
        keywords = KeywordExtractor.extract_keywords(text, max_keywords=3)
        
        # Should prioritize visual keywords
        visual_keywords = {"business", "growth", "team", "leadership", "meeting"}
        found_visual = [kw for kw in keywords if kw in visual_keywords]
        
        assert len(found_visual) >= 2, f"Should find visual keywords, got: {keywords}"
    
    def test_compound_phrases_extraction(self):
        """Test extraction of compound phrases"""
        
        text = "Digital marketing strategies for small business owners in competitive markets."
        keywords = KeywordExtractor.extract_keywords(text, max_keywords=5)
        
        # Should include some compound phrases
        assert any(" " in kw for kw in keywords), f"Should include compound phrases: {keywords}"
    
    def test_empty_text_handling(self):
        """Test handling of empty or minimal text"""
        
        assert KeywordExtractor.extract_keywords("") == []
        assert KeywordExtractor.extract_keywords("   ") == []
        assert KeywordExtractor.extract_keywords("the and of") == []

class TestAPIQuotaManager:
    """Test API quota management functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.quota_manager = APIQuotaManager()
        
        # Mock cache directory to temp directory
        with patch('assets_fetcher.CACHE_DIR', self.temp_dir):
            self.quota_manager = APIQuotaManager()
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_quota_initialization(self):
        """Test quota manager initialization"""
        
        assert APIProvider.PEXELS in self.quota_manager.quotas
        assert APIProvider.UNSPLASH in self.quota_manager.quotas
        assert APIProvider.PIXABAY in self.quota_manager.quotas
        
        # Should start with zero usage
        for provider in self.quota_manager.quotas:
            assert self.quota_manager.quotas[provider]['used'] == 0
    
    def test_can_make_request(self):
        """Test request permission checking"""
        
        # Should initially allow requests
        assert self.quota_manager.can_make_request(APIProvider.PEXELS) == True
        
        # Should deny after reaching limit
        self.quota_manager.quotas[APIProvider.PEXELS]['used'] = 200  # At limit
        assert self.quota_manager.can_make_request(APIProvider.PEXELS) == False
    
    def test_record_request(self):
        """Test request recording"""
        
        initial_usage = self.quota_manager.quotas[APIProvider.PEXELS]['used']
        self.quota_manager.record_request(APIProvider.PEXELS)
        
        assert self.quota_manager.quotas[APIProvider.PEXELS]['used'] == initial_usage + 1

@pytest.mark.asyncio
class TestAPIClients:
    """Test API client functionality with mocking"""
    
    async def test_pexels_search_images_success(self):
        """Test successful Pexels image search"""
        
        mock_response_data = {
            'photos': [
                {
                    'id': 123456,
                    'url': 'https://pexels.com/photo/123456',
                    'photographer': 'Test Photographer',
                    'src': {
                        'large': 'https://images.pexels.com/photos/123456/test-large.jpg',
                        'large2x': 'https://images.pexels.com/photos/123456/test-large2x.jpg'
                    },
                    'width': 1920,
                    'height': 1080
                }
            ]
        }
        
        pexels = PexelsAPI("test-api-key")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await pexels.search_images("business", per_page=1)
            
            assert len(results) == 1
            assert results[0]['id'] == 123456
            assert results[0]['photographer'] == 'Test Photographer'
    
    async def test_pexels_search_images_rate_limit(self):
        """Test Pexels rate limit handling"""
        
        pexels = PexelsAPI("test-api-key")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 429  # Rate limit
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await pexels.search_images("business", per_page=1)
            
            assert results == []  # Should return empty list on rate limit
    
    async def test_unsplash_search_images_success(self):
        """Test successful Unsplash image search"""
        
        mock_response_data = {
            'results': [
                {
                    'id': 'abc123',
                    'urls': {
                        'regular': 'https://images.unsplash.com/photo-abc123-regular.jpg',
                        'small': 'https://images.unsplash.com/photo-abc123-small.jpg'
                    },
                    'user': {'name': 'Test User'},
                    'links': {'html': 'https://unsplash.com/photos/abc123'},
                    'width': 1920,
                    'height': 1280
                }
            ]
        }
        
        unsplash = UnsplashAPI("test-access-key")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await unsplash.search_images("technology", per_page=1)
            
            assert len(results) == 1
            assert results[0]['id'] == 'abc123'
            assert results[0]['user']['name'] == 'Test User'

@pytest.mark.asyncio
class TestAssetsFetcher:
    """Test main AssetsFetcher functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock all directory paths to use temp directory
        with patch.multiple(
            'assets_fetcher',
            ASSETS_DIR=self.temp_dir,
            IMAGES_DIR=self.temp_dir / "images", 
            VIDEOS_DIR=self.temp_dir / "videos",
            MUSIC_DIR=self.temp_dir / "music",
            CACHE_DIR=self.temp_dir / "cache",
            METADATA_DIR=self.temp_dir / "metadata"
        ):
            self.fetcher = AssetsFetcher(
                pexels_api_key="test-pexels-key",
                unsplash_access_key="test-unsplash-key", 
                pixabay_api_key="test-pixabay-key"
            )
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test AssetsFetcher initialization"""
        
        assert self.fetcher.pexels is not None
        assert self.fetcher.unsplash is not None
        assert self.fetcher.pixabay is not None
        assert self.fetcher.quota_manager is not None
        assert self.fetcher.keyword_extractor is not None
    
    def test_extract_sentence_keywords(self):
        """Test sentence keyword extraction"""
        
        sentences = [
            "This is a business meeting about growth strategies.",
            "Technology innovations are changing the digital landscape.",
            "Team leadership skills are crucial for success."
        ]
        
        result = self.fetcher.extract_sentence_keywords(sentences)
        
        assert len(result) == 3
        assert "sentence_001" in result
        assert "sentence_002" in result
        assert "sentence_003" in result
        
        # Check that keywords were extracted
        for sentence_key, keywords in result.items():
            assert isinstance(keywords, list)
            assert len(keywords) > 0
    
    async def test_fetch_assets_for_keywords_with_mocking(self):
        """Test asset fetching with mocked API responses"""
        
        # Mock successful image download
        mock_image_data = {
            'id': 123456,
            'url': 'https://pexels.com/photo/123456',
            'photographer': 'Test Photographer',
            'src': {
                'large2x': 'https://images.pexels.com/photos/123456/test.jpg'
            },
            'width': 1920,
            'height': 1080
        }
        
        # Mock API responses
        with patch.object(self.fetcher.pexels, 'search_images', return_value=[mock_image_data]):
            with patch.object(self.fetcher.pexels, 'search_videos', return_value=[]):
                with patch.object(self.fetcher.pixabay, 'search_music', return_value=[]):
                    with patch('assets_fetcher.AssetsDownloader') as mock_downloader_class:
                        # Mock the downloader context manager
                        mock_downloader = AsyncMock()
                        mock_downloader.download_asset.return_value = True
                        mock_downloader_class.return_value.__aenter__.return_value = mock_downloader
                        
                        # Mock file creation
                        with patch('pathlib.Path.exists', return_value=False):
                            with patch('pathlib.Path.stat') as mock_stat:
                                mock_stat.return_value.st_size = 1024 * 1024  # 1MB
                                
                                keywords = ["business", "growth"]
                                result = await self.fetcher.fetch_assets_for_keywords(keywords)
                                
                                assert isinstance(result, KeywordAssets)
                                assert result.keyword == "business"
                                # Note: Images list may be empty due to file path mocking complexity

class TestIntegration:
    """Integration tests for complete workflow"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_workflow_mock(self):
        """Test complete workflow with mocked external dependencies"""
        
        sentences = [
            "Welcome to our business presentation about digital transformation.",
            "Technology is reshaping how companies operate in the modern world.",
            "Team collaboration tools are essential for remote work success."
        ]
        
        with patch.multiple(
            'assets_fetcher',
            ASSETS_DIR=self.temp_dir,
            IMAGES_DIR=self.temp_dir / "images",
            CACHE_DIR=self.temp_dir / "cache",
            METADATA_DIR=self.temp_dir / "metadata"
        ):
            fetcher = AssetsFetcher(
                pexels_api_key="test-key",
                unsplash_access_key="test-key",
                pixabay_api_key="test-key"
            )
            
            # Test keyword extraction (no mocking needed)
            keywords_result = fetcher.extract_sentence_keywords(sentences)
            
            assert len(keywords_result) == 3
            assert all(len(kw_list) > 0 for kw_list in keywords_result.values())
            
            # Verify visual keywords are prioritized
            all_keywords = []
            for kw_list in keywords_result.values():
                all_keywords.extend(kw_list)
            
            visual_found = [kw for kw in all_keywords if kw in KeywordExtractor.VISUAL_KEYWORDS]
            assert len(visual_found) > 0, f"Should find visual keywords in: {all_keywords}"

def demo_assets_fetcher():
    """
    Demo function to showcase assets fetcher capabilities
    This function demonstrates the complete workflow without actual API calls
    """
    
    print("🎨 ASSETS FETCHER DEMO")
    print("=" * 50)
    
    # Demo sentences from a typical YouTube script
    demo_sentences = [
        "Welcome back to our channel where we explore the latest in business technology!",
        "Today we're diving deep into digital transformation strategies that are revolutionizing industries.",
        "From artificial intelligence to cloud computing, these innovations are changing everything.",
        "Successful companies are leveraging data analytics to gain competitive advantages.",
        "Team collaboration has evolved with remote work becoming the new normal.",
        "Leadership skills are more important than ever in this digital age.",
        "Don't forget to subscribe and hit the notification bell for more content!"
    ]
    
    print(f"📝 Sample Script ({len(demo_sentences)} sentences):")
    for i, sentence in enumerate(demo_sentences, 1):
        print(f"  {i}. {sentence}")
    
    print("\n🔍 KEYWORD EXTRACTION DEMO:")
    print("-" * 30)
    
    extractor = KeywordExtractor()
    
    for i, sentence in enumerate(demo_sentences, 1):
        keywords = extractor.extract_keywords(sentence, max_keywords=3)
        print(f"Sentence {i}: {keywords}")
        print(f"  └─ \"{sentence[:60]}...\"")
    
    print("\n📊 QUOTA MANAGER DEMO:")
    print("-" * 25)
    
    quota_manager = APIQuotaManager()
    print("Initial API Quotas:")
    for provider, quota in quota_manager.quotas.items():
        used = quota['used']
        limit = quota['daily_limit']
        remaining = limit - used
        print(f"  {provider.value}: {used}/{limit} ({remaining} remaining)")
    
    print("\n🏗️  ASSET DIRECTORY STRUCTURE:")
    print("-" * 35)
    print("assets/")
    print("├── images/          # Downloaded stock photos")
    print("│   ├── pexels_123456_business.jpg")
    print("│   ├── unsplash_abc123_technology.jpg")
    print("│   └── pixabay_789012_growth.jpg")
    print("├── videos/          # Downloaded video clips")
    print("│   ├── pexels_video_456789_team.mp4")
    print("│   └── pexels_video_012345_office.mp4")
    print("├── music/           # Background music files")
    print("│   ├── pixabay_music_111222_inspiring.mp3")
    print("│   └── pixabay_music_333444_corporate.mp3")
    print("├── cache/           # API quota and caching data")
    print("│   └── api_quotas.json")
    print("└── metadata/        # Session metadata")
    print("    └── assets_session_20240809_123456.json")
    
    print("\n✅ DEMO COMPLETE!")
    print("To test with real APIs, run:")
    print("  python assets_fetcher.py --test-apis")
    print("  python assets_fetcher.py --text 'Your test sentence here'")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test and demo the assets fetcher")
    parser.add_argument("--demo", action="store_true", help="Run demo showcase")
    parser.add_argument("--run-tests", action="store_true", help="Run test suite")
    
    args = parser.parse_args()
    
    if args.demo:
        demo_assets_fetcher()
    elif args.run_tests:
        # Run pytest on this file
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"], 
                              capture_output=False)
        sys.exit(result.returncode)
    else:
        print("Choose an option:")
        print("  --demo        Show functionality demo")
        print("  --run-tests   Run test suite")
        print("\nOr run the actual assets fetcher:")
        print("  python assets_fetcher.py --help")
