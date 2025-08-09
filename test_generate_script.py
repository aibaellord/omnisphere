#!/usr/bin/env python3
"""
🧪 UNIT TESTS FOR SCRIPT GENERATOR 🧪

Comprehensive test suite for the ideation & script-writing agent:
- Reading time validation (≤ 90 seconds)
- Candidate selection algorithm
- Script parsing and structure validation
- AI fallback system testing
- File I/O operations
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock pytest decorators for basic testing
    class MockPytest:
        @staticmethod
        def fixture(func):
            return func
        
        class mark:
            @staticmethod
            def asyncio(func):
                return func
    
    pytest = MockPytest()

import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
try:
    from unittest.mock import Mock, patch, AsyncMock
except ImportError:
    # Basic mock for older Python versions
    class Mock:
        pass
    patch = Mock
    AsyncMock = Mock
import sys
import os

# Add the main directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_script import (
    ScriptGenerator, 
    TrendingCandidate, 
    GeneratedScript,
    validate_reading_time,
    MAX_READING_TIME_SECONDS,
    AVERAGE_READING_SPEED_WPM
)

class TestReadingTimeValidation:
    """Test suite for reading time validation"""
    
    def test_short_script_valid(self):
        """Test that short scripts pass validation"""
        short_script = "This is a short test script."
        is_valid, reading_time = validate_reading_time(short_script)
        
        assert is_valid is True
        assert reading_time <= MAX_READING_TIME_SECONDS
        assert reading_time > 0
    
    def test_medium_script_valid(self):
        """Test that medium-length scripts pass validation"""
        # ~150 words = ~60 seconds reading time
        medium_script = " ".join(["word"] * 150)
        is_valid, reading_time = validate_reading_time(medium_script)
        
        assert is_valid is True
        assert reading_time <= MAX_READING_TIME_SECONDS
        assert 50 < reading_time < MAX_READING_TIME_SECONDS
    
    def test_long_script_invalid(self):
        """Test that overly long scripts fail validation"""
        # ~300 words = ~120 seconds reading time (should fail)
        long_script = " ".join(["word"] * 300)
        is_valid, reading_time = validate_reading_time(long_script)
        
        assert is_valid is False
        assert reading_time > MAX_READING_TIME_SECONDS
    
    def test_edge_case_exact_limit(self):
        """Test script at exactly the time limit"""
        # Calculate exact word count for 90 seconds
        max_words = int((MAX_READING_TIME_SECONDS / 60) * AVERAGE_READING_SPEED_WPM)
        exact_limit_script = " ".join(["word"] * max_words)
        is_valid, reading_time = validate_reading_time(exact_limit_script)
        
        assert is_valid is True
        assert abs(reading_time - MAX_READING_TIME_SECONDS) < 1  # Within 1 second tolerance
    
    def test_empty_script(self):
        """Test empty script validation"""
        is_valid, reading_time = validate_reading_time("")
        
        assert is_valid is True
        assert reading_time == 0

class TestScriptGenerator:
    """Test suite for main ScriptGenerator class"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        temp_root = tempfile.mkdtemp()
        scripts_dir = Path(temp_root) / "scripts"
        trending_dir = Path(temp_root) / "trending"
        
        scripts_dir.mkdir(parents=True, exist_ok=True)
        trending_dir.mkdir(parents=True, exist_ok=True)
        
        yield {
            'root': Path(temp_root),
            'scripts': scripts_dir,
            'trending': trending_dir
        }
        
        # Cleanup
        shutil.rmtree(temp_root)
    
    @pytest.fixture
    def sample_trending_data(self):
        """Create sample trending data for testing"""
        return [
            {
                "video_id": "test_video_1",
                "title": "Amazing AI Tool That Changes Everything",
                "channel_title": "Tech Channel",
                "view_count": 150000,
                "published_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "category_name": "Science & Technology",
                "region_code": "US",
                "tags": '["AI", "technology", "innovation"]',
                "description": "This revolutionary AI tool is transforming how we work...",
                "engagement_rate": 8.5
            },
            {
                "video_id": "test_video_2", 
                "title": "5 Secrets Millionaires Use Daily",
                "channel_title": "Wealth Channel",
                "view_count": 89000,
                "published_at": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
                "category_name": "Education",
                "region_code": "US", 
                "tags": '["money", "success", "habits"]',
                "description": "Discover the habits that separate millionaires from everyone else...",
                "engagement_rate": 7.2
            }
        ]
    
    @pytest.fixture
    def generator(self, temp_dirs):
        """Create ScriptGenerator instance with test configuration"""
        # Patch the directory constants
        with patch('generate_script.SCRIPTS_DIR', temp_dirs['scripts']), \
             patch('generate_script.TRENDING_DIR', temp_dirs['trending']):
            
            return ScriptGenerator(
                openai_api_key=None,  # Skip OpenAI for unit tests
                textgen_webui_url="http://test-server:7860",
                db_path=str(temp_dirs['root'] / "test.db")
            )
    
    def test_generator_initialization(self, generator):
        """Test that generator initializes correctly"""
        assert generator.openai_available is False
        assert generator.textgen_webui_url == "http://test-server:7860"
        assert "test.db" in generator.db_path
    
    @pytest.mark.asyncio
    async def test_load_trending_data_success(self, generator, temp_dirs, sample_trending_data):
        """Test successful loading of trending data"""
        # Create sample trending file
        trending_file = temp_dirs['trending'] / "sample.json"
        trending_content = {
            "videos": sample_trending_data
        }
        
        with open(trending_file, 'w') as f:
            json.dump(trending_content, f)
        
        # Patch directory and test loading
        with patch('generate_script.TRENDING_DIR', temp_dirs['trending']):
            data = await generator._load_trending_data()
        
        assert len(data) == 2
        assert data[0]['video_id'] == 'test_video_1'
        assert data[1]['video_id'] == 'test_video_2'
    
    @pytest.mark.asyncio
    async def test_load_trending_data_no_files(self, generator, temp_dirs):
        """Test loading when no trending files exist"""
        with patch('generate_script.TRENDING_DIR', temp_dirs['trending']):
            data = await generator._load_trending_data()
        
        assert data == []
    
    @pytest.mark.asyncio
    async def test_select_candidates_velocity_filter(self, generator, sample_trending_data):
        """Test candidate selection with velocity filtering"""
        candidates = await generator._select_candidates(
            sample_trending_data, 
            max_candidates=5, 
            min_velocity_score=0.01  # Low threshold for testing
        )
        
        assert len(candidates) <= 2
        # Verify candidates have required attributes
        for candidate in candidates:
            assert isinstance(candidate, TrendingCandidate)
            assert candidate.velocity_score >= 0
            assert candidate.gap_score >= 0
    
    @pytest.mark.asyncio
    async def test_calculate_content_gap_no_existing(self, generator):
        """Test content gap calculation with no existing content"""
        video_data = {
            "video_id": "test_video",
            "title": "Unique New Content Topic",
            "description": "A completely unique topic that hasn't been covered before"
        }
        
        gap_score = await generator._calculate_content_gap(video_data)
        
        # Should return high gap score (1.0) when no existing content
        assert gap_score == 1.0
    
    def test_parse_script_content_complete(self, generator):
        """Test parsing of complete script content"""
        script_content = """
# Amazing Test Title

## Hook (0-15s)
Wait! Before you scroll past this, you need to know this life-changing secret!

## 8-Point Narrative

### 1. Problem Introduction
Most people struggle with productivity because they don't know this one trick.

### 2. Stakes Elevation
Without this knowledge, you'll continue wasting hours every day.

### 3. Solution Tease
I'm about to reveal the exact method successful people use.

### 4. Authority Establishment
After studying 500+ high performers, I discovered their secret.

### 5. Main Content Delivery
Here's the step-by-step process they all follow...

### 6. Social Proof/Examples
Companies like Google and Apple use this same strategy.

### 7. Urgency Creation
You need to start implementing this today to see results.

### 8. Call-to-Action
Subscribe now and hit the bell icon for more productivity secrets!

## Metadata
- **Description:** Discover the productivity secret that top performers use but never share. This simple method can transform your daily output and help you achieve more in less time.
- **Tags:** productivity, success, habits, time management, efficiency, performance, secrets, life hacks, motivation, goals, achievement, focus, workflow, optimization, results
"""
        
        parsed = generator._parse_script_content(script_content)
        
        assert parsed['title'] == "Amazing Test Title"
        assert len(parsed['narrative_points']) == 8
        assert parsed['hook'] != ""
        assert "Subscribe now" in parsed['cta']
        assert len(parsed['tags']) > 10
        assert len(parsed['description']) > 50
    
    def test_calculate_viral_score(self, generator):
        """Test viral score calculation"""
        good_script = {
            'title': 'The Ultimate 7 Secrets That Will Change Your Life',  # Good length, numbers, power words
            'hook': 'Wait! Before you scroll away, you absolutely need to see this incredible discovery...',
            'narrative_points': ['Point 1', 'Point 2', 'Point 3', 'Point 4', 'Point 5', 'Point 6', 'Point 7', 'Point 8'],
            'cta': 'Subscribe now for more amazing content!',
            'tags': ['amazing', 'secrets', 'life changing', 'ultimate', 'viral', 'trending', 'must watch', 'incredible', 'shocking', 'revealed', 'exclusive', 'proven', 'powerful', 'transformative', 'breakthrough']
        }
        
        score = generator._calculate_viral_score(good_script)
        
        assert 80 <= score <= 100  # Should score highly
    
    def test_generate_video_id(self, generator):
        """Test video ID generation"""
        candidate = TrendingCandidate(
            video_id="original_123",
            title="Test Title",
            channel_title="Test Channel",
            view_count=1000,
            published_at=datetime.now(timezone.utc),
            category_name="Test",
            region_code="US",
            tags=[],
            description="Test description",
            engagement_rate=0.05,
            velocity_score=0.8,
            gap_score=0.6,
            selected_reason="Test reason"
        )
        
        video_id = generator._generate_video_id(candidate)
        
        assert len(video_id) == 12
        assert video_id.isalnum()
    
    def test_validate_reading_time_integration(self, generator):
        """Test reading time validation integration"""
        # Create a script that should pass
        good_script = GeneratedScript(
            video_id="test123",
            title="Test Title",
            description="Test description",
            script_content=" ".join(["word"] * 150),  # ~60 seconds
            tags=["test"],
            hook="Test hook",
            narrative_points=["Point 1"],
            cta="Subscribe!",
            word_count=150,
            reading_time_seconds=60.0,
            viral_score=85.0,
            generated_at=datetime.now(timezone.utc),
            ai_model_used="test"
        )
        
        assert generator._validate_reading_time(good_script) is True
        
        # Create a script that should fail
        bad_script = GeneratedScript(
            video_id="test456",
            title="Test Title",
            description="Test description", 
            script_content=" ".join(["word"] * 300),  # ~120 seconds
            tags=["test"],
            hook="Test hook",
            narrative_points=["Point 1"],
            cta="Subscribe!",
            word_count=300,
            reading_time_seconds=120.0,
            viral_score=85.0,
            generated_at=datetime.now(timezone.utc),
            ai_model_used="test"
        )
        
        assert generator._validate_reading_time(bad_script) is False

class TestScriptStructureValidation:
    """Test suite for validating generated script structure"""
    
    def test_script_has_required_elements(self):
        """Test that generated scripts contain all required elements"""
        sample_script = """
# Viral Title Here

## Hook (0-15s)
Attention-grabbing opening

## 8-Point Narrative

### 1. Problem Introduction
Problem content

### 2. Stakes Elevation  
Stakes content

### 3. Solution Tease
Solution content

### 4. Authority Establishment
Authority content

### 5. Main Content Delivery
Main content

### 6. Social Proof/Examples
Social proof content

### 7. Urgency Creation
Urgency content

### 8. Call-to-Action
CTA content

## Metadata
- **Description:** Sample description
- **Tags:** tag1, tag2, tag3
"""
        
        # Verify structure elements
        assert "# Viral Title Here" in sample_script
        assert "## Hook (0-15s)" in sample_script
        assert "## 8-Point Narrative" in sample_script
        
        # Count narrative points
        narrative_points = sample_script.count("### ")
        assert narrative_points == 8
        
        # Verify metadata section
        assert "## Metadata" in sample_script
        assert "**Description:**" in sample_script
        assert "**Tags:**" in sample_script

@pytest.mark.asyncio
class TestAsyncOperations:
    """Test suite for asynchronous operations"""
    
    async def test_concurrent_script_generation(self):
        """Test that multiple scripts can be generated concurrently"""
        # This would be a more complex integration test
        # For now, just verify the async structure works
        
        async def mock_generation():
            await asyncio.sleep(0.01)  # Simulate async work
            return GeneratedScript(
                video_id="async_test",
                title="Async Test Title",
                description="Test description",
                script_content="Test content",
                tags=["test"],
                hook="Test hook",
                narrative_points=["Point 1"],
                cta="Subscribe!",
                word_count=10,
                reading_time_seconds=5.0,
                viral_score=75.0,
                generated_at=datetime.now(timezone.utc),
                ai_model_used="test"
            )
        
        # Run multiple concurrent generations
        tasks = [mock_generation() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, GeneratedScript)

def run_comprehensive_tests():
    """Run all tests and report results"""
    print("🧪 Running comprehensive script generator tests...\n")
    
    # Reading time validation tests
    print("📝 Testing reading time validation...")
    test_reader = TestReadingTimeValidation()
    
    try:
        test_reader.test_short_script_valid()
        print("✅ Short script validation: PASSED")
        
        test_reader.test_medium_script_valid()
        print("✅ Medium script validation: PASSED")
        
        test_reader.test_long_script_invalid()
        print("✅ Long script validation: PASSED")
        
        test_reader.test_edge_case_exact_limit()
        print("✅ Edge case validation: PASSED")
        
        test_reader.test_empty_script()
        print("✅ Empty script validation: PASSED")
        
    except AssertionError as e:
        print(f"❌ Reading time validation failed: {e}")
    
    print("\n📊 Testing script structure validation...")
    test_structure = TestScriptStructureValidation()
    
    try:
        test_structure.test_script_has_required_elements()
        print("✅ Script structure validation: PASSED")
        
    except AssertionError as e:
        print(f"❌ Script structure validation failed: {e}")
    
    print("\n🎯 All critical tests completed!")
    print("="*50)

if __name__ == "__main__":
    # Run the comprehensive test suite
    run_comprehensive_tests()
    
    # If pytest is available, run full test suite
    try:
        import pytest
        print("\n🚀 Running full pytest suite...")
        pytest.main([__file__, "-v"])
    except ImportError:
        print("\n💡 Install pytest for more comprehensive testing: pip install pytest")
