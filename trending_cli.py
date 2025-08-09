#!/usr/bin/env python3
"""
🎯 TRENDING DATA COLLECTOR CLI
Command-line interface for managing the trending data collector

Usage:
  python trending_cli.py collect --regions US,GB --categories 10,24
  python trending_cli.py status
  python trending_cli.py history
  python trending_cli.py export --format json --days 7
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent))

from collect_trending import TrendingDataCollector, YOUTUBE_REGIONS, YOUTUBE_CATEGORIES


class TrendingCLI:
    """Command-line interface for trending data collector"""
    
    def __init__(self):
        self.collector = None
        self._init_collector()
    
    def _init_collector(self):
        """Initialize the collector with API keys from environment"""
        api_keys = []
        for i in range(1, 6):  # Support up to 5 API keys
            key = os.getenv(f'YOUTUBE_API_KEY_{i}') or os.getenv('YOUTUBE_API_KEY')
            if key and key not in api_keys:
                api_keys.append(key)
        
        if not api_keys:
            print("❌ No YouTube API keys found in environment variables")
            print("💡 Set YOUTUBE_API_KEY or YOUTUBE_API_KEY_1, YOUTUBE_API_KEY_2, etc.")
            sys.exit(1)
        
        self.collector = TrendingDataCollector(
            api_keys=api_keys,
            db_path="trending_data.db",
            data_dir="./data/trending"
        )
        print(f"✅ Initialized with {len(api_keys)} API key(s)")
    
    async def collect(self, regions: Optional[List[str]] = None, 
                     categories: Optional[List[str]] = None,
                     max_results: int = 50):
        """Run trending data collection"""
        print("🚀 Starting trending data collection...")
        
        # Validate inputs
        if regions:
            invalid_regions = [r for r in regions if r not in YOUTUBE_REGIONS]
            if invalid_regions:
                print(f"⚠️  Invalid regions: {invalid_regions}")
                print(f"Valid regions: {', '.join(YOUTUBE_REGIONS)}")
                return
        
        if categories:
            invalid_categories = [c for c in categories if c not in YOUTUBE_CATEGORIES]
            if invalid_categories:
                print(f"⚠️  Invalid categories: {invalid_categories}")
                print(f"Valid categories: {', '.join(YOUTUBE_CATEGORIES.keys())}")
                return
        
        # Run collection
        results = await self.collector.collect_trending_data(
            regions=regions,
            categories=categories,
            max_results_per_request=max_results
        )
        
        # Print results
        print("\n" + "="*60)
        print("📊 COLLECTION RESULTS")
        print("="*60)
        print(f"📦 Batch ID: {results['batch_id']}")
        print(f"🎥 Total Videos: {results['total_videos_collected']}")
        print(f"🌍 Regions Processed: {results['regions_processed']}")
        print(f"📈 Success Rate: {results['success_rate']:.1f}%")
        print(f"⏱️  Processing Time: {results['processing_time_seconds']:.2f}s")
        print(f"🔥 API Requests: {results['api_requests_made']}")
        print(f"💾 Quota Used: {results['quota_used']}")
        print("="*60)
        
        return results
    
    def status(self):
        """Show current status and quota usage"""
        quota_status = self.collector.get_quota_status()
        
        print("\n📊 TRENDING COLLECTOR STATUS")
        print("="*50)
        print(f"🔑 Current API Key: #{quota_status['current_api_key_index'] + 1}")
        print(f"📈 Requests Today: {quota_status['requests_today']}")
        print(f"💾 Quota Used: {quota_status['quota_used_today']}/{quota_status['quota_limit']}")
        print(f"🔋 Quota Remaining: {quota_status['quota_remaining']}")
        print(f"✅ Can Make Requests: {'Yes' if quota_status['can_make_requests'] else 'No'}")
        print("="*50)
    
    def history(self, days: int = 7):
        """Show collection history"""
        history = self.collector.get_collection_history(days=days)
        
        if not history:
            print(f"❌ No collection history found for the last {days} days")
            return
        
        print(f"\n📚 COLLECTION HISTORY (Last {days} days)")
        print("="*80)
        print(f"{'Batch ID':<18} {'Date':<20} {'Videos':<8} {'Success':<8} {'Time':<8}")
        print("-"*80)
        
        for record in history:
            date_str = datetime.fromisoformat(record['collection_date']).strftime('%Y-%m-%d %H:%M')
            print(f"{record['batch_id']:<18} {date_str:<20} {record['total_videos']:<8} "
                  f"{record['success_rate']:.1f}%{'':<3} {record['processing_time']:.1f}s{'':<3}")
        
        print("="*80)
    
    def export(self, format_type: str = 'json', days: int = 7, output_file: Optional[str] = None):
        """Export collected data"""
        try:
            import sqlite3
            import pandas as pd
            
            conn = sqlite3.connect(self.collector.db_path)
            
            # Get data from the last N days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = """
            SELECT video_id, title, channel_title, region_code, category_name,
                   view_count, like_count, comment_count, engagement_rate,
                   trending_rank, collected_at, collection_batch
            FROM trending_videos 
            WHERE collected_at >= ?
            ORDER BY collected_at DESC, trending_rank ASC
            """
            
            df = pd.read_sql_query(query, conn, params=(cutoff_date.isoformat(),))
            conn.close()
            
            if df.empty:
                print(f"❌ No data found for the last {days} days")
                return
            
            # Generate output filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"trending_export_{timestamp}.{format_type}"
            
            # Export based on format
            if format_type.lower() == 'json':
                data = df.to_dict('records')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            elif format_type.lower() == 'csv':
                df.to_csv(output_file, index=False)
            elif format_type.lower() == 'excel':
                df.to_excel(output_file, index=False, engine='openpyxl')
            else:
                print(f"❌ Unsupported format: {format_type}")
                print("Supported formats: json, csv, excel")
                return
            
            print(f"✅ Exported {len(df)} records to {output_file}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def list_regions(self):
        """List available YouTube regions"""
        print("\n🌍 AVAILABLE YOUTUBE REGIONS")
        print("="*40)
        for i, region in enumerate(YOUTUBE_REGIONS, 1):
            if i % 10 == 0:
                print(region)
            else:
                print(f"{region:<4}", end="")
        print("\n" + "="*40)
    
    def list_categories(self):
        """List available YouTube categories"""
        print("\n📂 AVAILABLE YOUTUBE CATEGORIES")
        print("="*60)
        for cat_id, cat_name in YOUTUBE_CATEGORIES.items():
            print(f"{cat_id:<3} {cat_name}")
        print("="*60)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="🔥 Trending Data Collector CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect trending data')
    collect_parser.add_argument('--regions', type=str, help='Comma-separated region codes')
    collect_parser.add_argument('--categories', type=str, help='Comma-separated category IDs')
    collect_parser.add_argument('--max-results', type=int, default=50, 
                               help='Max results per request (default: 50)')
    
    # Status command
    subparsers.add_parser('status', help='Show collector status and quota usage')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show collection history')
    history_parser.add_argument('--days', type=int, default=7, 
                               help='Number of days to show (default: 7)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export collected data')
    export_parser.add_argument('--format', choices=['json', 'csv', 'excel'], 
                              default='json', help='Export format (default: json)')
    export_parser.add_argument('--days', type=int, default=7,
                              help='Number of days to export (default: 7)')
    export_parser.add_argument('--output', type=str, help='Output filename')
    
    # List commands
    subparsers.add_parser('list-regions', help='List available regions')
    subparsers.add_parser('list-categories', help='List available categories')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = TrendingCLI()
    
    try:
        if args.command == 'collect':
            regions = None
            if args.regions:
                regions = [r.strip().upper() for r in args.regions.split(',')]
            
            categories = None
            if args.categories:
                categories = [c.strip() for c in args.categories.split(',')]
            
            asyncio.run(cli.collect(
                regions=regions,
                categories=categories,
                max_results=args.max_results
            ))
        
        elif args.command == 'status':
            cli.status()
        
        elif args.command == 'history':
            cli.history(days=args.days)
        
        elif args.command == 'export':
            cli.export(
                format_type=args.format,
                days=args.days,
                output_file=args.output
            )
        
        elif args.command == 'list-regions':
            cli.list_regions()
        
        elif args.command == 'list-categories':
            cli.list_categories()
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
