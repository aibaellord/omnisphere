#!/usr/bin/env python3
"""
🧪 Test Script for Trending Data Collector
Simple test to verify the collector is working correctly
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from collect_trending import TrendingDataCollector


async def test_collector():
    """Test the trending data collector with minimal data"""
    
    # Check for API key
    api_keys = []
    for i in range(1, 6):
        key = os.getenv(f'YOUTUBE_API_KEY_{i}') or os.getenv('YOUTUBE_API_KEY')
        if key and key not in api_keys:
            api_keys.append(key)
    
    if not api_keys:
        print("❌ No YouTube API keys found")
        print("💡 Set YOUTUBE_API_KEY environment variable")
        print("Example: export YOUTUBE_API_KEY='your-api-key-here'")
        return False
    
    print(f"✅ Found {len(api_keys)} API key(s)")
    
    try:
        # Initialize collector
        collector = TrendingDataCollector(
            api_keys=api_keys,
            db_path="test_trending.db",
            data_dir="./test_data"
        )
        
        print("✅ Collector initialized successfully")
        
        # Test quota status
        quota_status = collector.get_quota_status()
        print(f"📊 Quota Status: {quota_status['quota_used_today']}/{quota_status['quota_limit']}")
        
        # Test small collection (just US, Music category, 5 videos)
        print("🚀 Testing small collection (US, Music, 5 videos)...")
        
        results = await collector.collect_trending_data(
            regions=['US'],
            categories=['10'],  # Music
            max_results_per_request=5
        )
        
        print("\n📊 TEST RESULTS:")
        print(f"✅ Batch ID: {results['batch_id']}")
        print(f"📹 Videos Collected: {results['total_videos_collected']}")
        print(f"🌍 Regions Processed: {results['regions_processed']}")
        print(f"📈 Success Rate: {results['success_rate']:.1f}%")
        print(f"⏱️  Processing Time: {results['processing_time_seconds']:.2f}s")
        print(f"🔥 API Requests: {results['api_requests_made']}")
        
        # Verify data storage
        test_data_path = Path("./test_data")
        json_files = list(test_data_path.glob("*.json"))
        
        if json_files:
            print(f"✅ JSON file created: {json_files[0].name}")
        else:
            print("⚠️  No JSON files found")
        
        # Test database queries
        history = collector.get_collection_history(days=1)
        if history:
            print(f"✅ Database working: {len(history)} collection record(s)")
        else:
            print("⚠️  No collection history found")
        
        print("\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 TRENDING DATA COLLECTOR TEST")
    print("=" * 50)
    
    # Run the test
    success = asyncio.run(test_collector())
    
    if success:
        print("\n✅ All tests passed!")
        print("💡 Try running: python trending_cli.py collect --regions US --categories 10")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        print("💡 Check your API key and internet connection")
        sys.exit(1)
