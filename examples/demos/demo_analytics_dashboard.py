#!/usr/bin/env python3
"""
🚀 ANALYTICS DASHBOARD DEMO 🚀
Demo script to create sample analytics data and launch the dashboard

This script:
1. Creates sample YouTube analytics data
2. Populates the SQLite database
3. Launches the Streamlit dashboard
4. Shows how the system works end-to-end
"""

import os
import sqlite3
import random
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

def create_sample_data():
    """Create sample analytics data for dashboard demonstration"""
    print("📊 Creating sample analytics data...")
    
    db_path = "analytics_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables (same as in analytics_collector.py)
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
    
    # Sample channels
    channels = [
        {
            'id': 'UC_sample_tech_channel',
            'name': 'Tech Innovations Hub',
            'subscribers': 125000,
            'total_views': 15000000,
            'videos': 450
        },
        {
            'id': 'UC_sample_gaming_channel',
            'name': 'Epic Gaming Universe',
            'subscribers': 89000,
            'total_views': 8500000,
            'videos': 320
        },
        {
            'id': 'UC_sample_lifestyle_channel',
            'name': 'Daily Life Vibes',
            'subscribers': 67000,
            'total_views': 4200000,
            'videos': 180
        }
    ]
    
    # Insert channel metadata
    for channel in channels:
        cursor.execute('''
        INSERT OR REPLACE INTO channel_metadata
        (channel_id, channel_name, subscriber_count, total_views, video_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            channel['id'], channel['name'], channel['subscribers'],
            channel['total_views'], channel['videos'], '2022-01-01T00:00:00Z'
        ))
    
    # Generate 60 days of sample analytics data
    for days_ago in range(60, 0, -1):
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        for channel in channels:
            channel_id = channel['id']
            
            # Base performance with some growth trend and randomness
            base_multiplier = 1.0 + (60 - days_ago) * 0.01  # Growth over time
            
            # Channel-specific performance
            if 'tech' in channel['name'].lower():
                views = random.randint(8000, 15000) * base_multiplier
                rpm = random.uniform(2.5, 5.5)
            elif 'gaming' in channel['name'].lower():
                views = random.randint(12000, 25000) * base_multiplier
                rpm = random.uniform(1.8, 4.2)
            else:  # lifestyle
                views = random.randint(3000, 8000) * base_multiplier
                rpm = random.uniform(3.2, 6.8)
            
            views = int(views)
            watch_time = random.randint(int(views * 0.3), int(views * 0.8))
            estimated_revenue = (views / 1000) * rpm
            cpm = rpm * random.uniform(0.7, 1.3)
            
            subs_gained = random.randint(50, 200)
            subs_lost = random.randint(10, 50)
            likes = random.randint(int(views * 0.02), int(views * 0.08))
            comments = random.randint(int(views * 0.005), int(views * 0.02))
            shares = random.randint(int(views * 0.001), int(views * 0.01))
            
            # Insert analytics data
            cursor.execute('''
            INSERT OR REPLACE INTO channel_analytics
            (date, channel_id, views, watch_time_minutes, estimated_revenue, rpm, cpm,
             subscribers_gained, subscribers_lost, likes, dislikes, comments, shares,
             estimated_minutes_watched, average_view_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date, channel_id, views, watch_time, estimated_revenue, rpm, cpm,
                subs_gained, subs_lost, likes, 0, comments, shares,
                float(watch_time), random.uniform(180, 420)
            ))
            
            # Insert revenue tracking
            cursor.execute('''
            INSERT OR REPLACE INTO revenue_tracking
            (date, channel_id, total_revenue, ad_revenue, estimated_cost, profit_margin,
             cost_per_view, revenue_per_subscriber)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date, channel_id, estimated_revenue, estimated_revenue,
                0.0, 100.0, 0.0, estimated_revenue / max(1, subs_gained)
            ))
    
    conn.commit()
    conn.close()
    
    print("✅ Sample analytics data created successfully!")
    
    # Print summary
    print("\n📊 DATA SUMMARY:")
    print(f"  - {len(channels)} sample channels created")
    print(f"  - 60 days of analytics data generated")
    print(f"  - Revenue data includes zero-cost profit tracking")
    print(f"  - Database saved as: {db_path}")

def show_dashboard_commands():
    """Show commands to run the dashboard"""
    print("\n🚀 DASHBOARD LAUNCH COMMANDS:")
    print("=" * 50)
    
    print("\n1. 📊 Launch Local Dashboard:")
    print("   streamlit run dashboard.py")
    
    print("\n2. 🔧 Install Dashboard Dependencies:")
    print("   pip install -r requirements-dashboard.txt")
    
    print("\n3. 📈 Run Analytics Collector (for real data):")
    print("   python analytics_collector.py")
    
    print("\n4. ☁️ Deploy to Streamlit Cloud:")
    print("   - Push code to GitHub repository")
    print("   - Connect repository to Streamlit Cloud")
    print("   - Set main file as 'dashboard.py'")
    print("   - Deploy and share!")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['streamlit', 'pandas', 'plotly']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing_packages)}")
        print("💡 Install with: pip install -r requirements-dashboard.txt")
        return False
    
    print("✅ All required dependencies are installed!")
    return True

def launch_dashboard():
    """Launch the Streamlit dashboard"""
    try:
        print("\n🚀 Launching Streamlit dashboard...")
        print("📊 Dashboard will open in your default browser")
        print("🔄 Press Ctrl+C to stop the dashboard")
        
        # Launch streamlit
        subprocess.run(['streamlit', 'run', 'dashboard.py'], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching dashboard: {e}")
        print("💡 Make sure Streamlit is installed: pip install streamlit")
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except FileNotFoundError:
        print("❌ Streamlit not found. Install with: pip install streamlit")

def main():
    """Main demo function"""
    print("\n🚀 YOUTUBE ANALYTICS DASHBOARD DEMO")
    print("=" * 50)
    
    # Create sample data
    create_sample_data()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Show commands
    show_dashboard_commands()
    
    # Ask user if they want to launch dashboard
    print("\n" + "=" * 50)
    
    if deps_ok:
        launch_choice = input("\n🚀 Launch dashboard now? (y/n): ").lower().strip()
        
        if launch_choice in ['y', 'yes']:
            launch_dashboard()
        else:
            print("\n💡 Run 'streamlit run dashboard.py' when ready!")
    else:
        print("\n🔧 Install dependencies first, then run: streamlit run dashboard.py")
    
    print("\n✅ Demo setup complete!")

if __name__ == "__main__":
    main()
