#!/usr/bin/env python3
"""
🎬 SCRIPT GENERATION DEMO 🎬

Demonstrates the ideation & script-writing agent with sample data and mock AI responses.
This showcases the full system functionality including:
- Trending data analysis and candidate selection
- Script generation with proper structure
- Reading time validation
- File saving in both JSON and Markdown formats
"""

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from generate_script import (
    ScriptGenerator, 
    TrendingCandidate, 
    GeneratedScript,
    validate_reading_time
)

class MockScriptGenerator(ScriptGenerator):
    """Mock version of ScriptGenerator that doesn't require external APIs"""
    
    def __init__(self):
        # Initialize without API keys - will use mock generation
        super().__init__(
            openai_api_key=None,
            textgen_webui_url="http://mock-server:7860",
            db_path="demo_script_generator.db"
        )
    
    async def _generate_with_openai(self, candidate, gap_analysis):
        """Mock OpenAI generation with pre-made viral script"""
        await asyncio.sleep(0.5)  # Simulate API call
        
        mock_script = f"""
# The Ultimate AI Revolution Secret That Will 10X Your Success

## Hook (0-15s)
Wait! Before you scroll past this, you NEED to see this game-changing discovery. The results will shock you!

## 8-Point Narrative

### 1. Problem Introduction
95% of people use outdated methods while the top 1% leverage this powerful approach.

### 2. Stakes Elevation
Every day you delay costs you opportunities and progress.

### 3. Solution Tease
I'll reveal the exact system that transformed my results overnight.

### 4. Authority Establishment
After analyzing {candidate.view_count:,} data points, I discovered this winning pattern.

### 5. Main Content Delivery
Three key steps: understand the principle, implement strategies, optimize technique.

### 6. Social Proof/Examples
Google, Apple, and Tesla use this. Beginners see 300% improvements in 30 days.

### 7. Urgency Creation
This window won't stay open forever. Early adopters are pulling ahead.

### 8. Call-to-Action
LIKE if this opened your eyes, SUBSCRIBE for secrets, COMMENT your takeaway!

## Metadata
- **Description:** Discover the secret helping people achieve incredible results. This proven system has been tested by thousands. Learn the exact steps to get ahead of 95% of people.
- **Tags:** viral secret, ultimate guide, game changer, proven system, success method, life hack, breakthrough, transformation, results, opportunity, insider knowledge, expert tips, winning strategy, competitive advantage, success mindset
"""
        return mock_script.strip()
    
    async def _generate_with_textgen_webui(self, candidate, gap_analysis):
        """Mock textgen-webui generation with fallback script"""
        await asyncio.sleep(1.0)  # Simulate slower local generation
        
        fallback_script = f"""
# The Complete Guide to {candidate.category_name} Success

## Hook (0-15s)
Stop! This will change how you think about {candidate.category_name.lower()}.

## 8-Point Narrative

### 1. Problem Introduction
Most struggle with this challenge, costing time and opportunities.

### 2. Stakes Elevation
Waiting means falling further behind. This problem worsens daily.

### 3. Solution Tease
I discovered a simple method that solves this. Easier than you think.

### 4. Authority Establishment
Extensive research and testing prove this approach works.

### 5. Main Content Delivery
Key steps to implement this solution effectively.

### 6. Social Proof/Examples
Thousands used this method with amazing success.

### 7. Urgency Creation
Start right now. Don't let another day pass.

### 8. Call-to-Action
Like, subscribe, and comment what you learned!

## Metadata
- **Description:** Learn the proven method thousands use to solve this problem. Complete guide with everything you need.
- **Tags:** solution, method, guide, proven, effective, results, strategy, tips, advice, help, tutorial, system, approach, technique, success
"""
        return fallback_script.strip()

async def demo_script_generation():
    """Demonstrate the complete script generation process"""
    
    print("🎬 SCRIPT GENERATION DEMO")
    print("="*60)
    
    # Initialize mock generator
    generator = MockScriptGenerator()
    
    print("✅ Initialized Script Generator (Mock Mode)")
    
    # Create sample trending candidates manually (since real data would be filtered)
    candidates = [
        TrendingCandidate(
            video_id="demo_ai_tool",
            title="This AI Tool Will Change Everything in 2024",
            channel_title="TechVision",
            view_count=125000,
            published_at=datetime.now(timezone.utc) - timedelta(hours=2),
            category_name="Science & Technology",
            region_code="US",
            tags=["AI", "artificial intelligence", "technology", "2024", "future"],
            description="Revolutionary AI tool transforming industries worldwide...",
            engagement_rate=7.76,
            velocity_score=0.85,  # High velocity score
            gap_score=0.75,       # Good gap opportunity
            selected_reason="High viral potential and trending topic"
        ),
        TrendingCandidate(
            video_id="demo_youtube_secret",
            title="The Secret Every YouTuber Uses (But Won't Tell You)",
            channel_title="Creator Secrets",
            view_count=156000,
            published_at=datetime.now(timezone.utc) - timedelta(hours=1),
            category_name="People & Blogs",
            region_code="US",
            tags=["YouTube secrets", "content creation", "viral videos", "algorithm"],
            description="Hidden pattern that successful YouTubers use but never share...",
            engagement_rate=9.29,
            velocity_score=0.92,
            gap_score=0.68,
            selected_reason="Extremely high engagement and viral potential"
        )
    ]
    
    print(f"📋 Selected {len(candidates)} high-potential candidates")
    
    # Generate scripts
    generated_scripts = []
    
    for i, candidate in enumerate(candidates, 1):
        print(f"\n🎯 Generating Script {i}/{len(candidates)}")
        print(f"   Title: {candidate.title[:50]}...")
        print(f"   Views: {candidate.view_count:,}")
        print(f"   Velocity Score: {candidate.velocity_score:.2f}")
        print(f"   Gap Score: {candidate.gap_score:.2f}")
        
        # Generate script
        script = await generator._generate_script_for_candidate(candidate)
        
        if script:
            # Validate reading time
            is_valid, reading_time = validate_reading_time(script.script_content)
            
            print(f"   📝 Word Count: {script.word_count}")
            print(f"   ⏱️  Reading Time: {reading_time:.1f}s")
            print(f"   📊 Viral Score: {script.viral_score:.1f}/100")
            print(f"   🤖 AI Model: {script.ai_model_used}")
            
            if is_valid:
                print(f"   ✅ Reading time validation: PASSED")
                generated_scripts.append(script)
                
                # Save the script
                await generator._save_script(script)
                print(f"   💾 Script saved: {script.video_id}.json/.md")
            else:
                print(f"   ❌ Reading time validation: FAILED ({reading_time:.1f}s > 90s)")
        else:
            print(f"   ❌ Script generation failed")
    
    # Summary
    print("\n" + "="*60)
    print("📊 GENERATION SUMMARY")
    print("="*60)
    
    print(f"🎯 Scripts Generated: {len(generated_scripts)}")
    print(f"📁 Files Created: {len(generated_scripts) * 2} (JSON + MD)")
    
    if generated_scripts:
        avg_viral_score = sum(s.viral_score for s in generated_scripts) / len(generated_scripts)
        avg_reading_time = sum(s.reading_time_seconds for s in generated_scripts) / len(generated_scripts)
        
        print(f"📊 Average Viral Score: {avg_viral_score:.1f}/100")
        print(f"⏱️  Average Reading Time: {avg_reading_time:.1f}s")
        
        print(f"\n🎬 Sample Generated Scripts:")
        for script in generated_scripts:
            print(f"\n📄 {script.title}")
            print(f"   ID: {script.video_id}")
            print(f"   Viral Score: {script.viral_score:.1f}")
            print(f"   Tags: {', '.join(script.tags[:5])}...")
            
        # Show one complete script example
        print(f"\n📜 SAMPLE SCRIPT PREVIEW:")
        print("-" * 50)
        sample_lines = generated_scripts[0].script_content.split('\n')[:15]
        for line in sample_lines:
            print(line)
        print("... (truncated)")
        print("-" * 50)
    
    print("\n✅ Demo completed successfully!")
    print(f"🗂️  Check 'data/scripts/' directory for generated files")

if __name__ == "__main__":
    asyncio.run(demo_script_generation())
