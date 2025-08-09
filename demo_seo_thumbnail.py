#!/usr/bin/env python3
"""
Demo script to test the SEO Thumbnail Generator

This script demonstrates the complete SEO metadata and thumbnail generation workflow
using existing video files and script data.
"""

import os
import json
from pathlib import Path
from seo_thumbnail_generator import SEOThumbnailGenerator

def find_video_and_script_pairs():
    """Find available video files and their corresponding script data."""
    videos_dir = Path("generated_videos")
    scripts_dir = Path("data/scripts")
    
    pairs = []
    
    if videos_dir.exists():
        video_files = list(videos_dir.glob("*.mp4"))
        script_files = list(scripts_dir.glob("*.json"))
        
        print(f"Found {len(video_files)} video files:")
        for video in video_files:
            print(f"  - {video}")
        
        print(f"Found {len(script_files)} script files:")
        for script in script_files:
            print(f"  - {script}")
        
        # For demo, we'll use the first available video with the first script
        if video_files and script_files:
            pairs.append((str(video_files[0]), str(script_files[0])))
    
    return pairs

def main():
    """Run the SEO thumbnail generation demo."""
    print("🚀 SEO Thumbnail Generator Demo")
    print("=" * 50)
    
    # Find available video and script pairs
    pairs = find_video_and_script_pairs()
    
    if not pairs:
        print("❌ No video/script pairs found for demo")
        print("💡 Make sure you have:")
        print("   - Video files in ./generated_videos/")
        print("   - Script JSON files in ./data/scripts/")
        return 1
    
    video_path, script_path = pairs[0]
    print(f"📹 Using video: {video_path}")
    print(f"📝 Using script: {script_path}")
    
    # Load script data
    with open(script_path, 'r') as f:
        script_data = json.load(f)
    
    print(f"📊 Script data loaded:")
    print(f"   Title: {script_data.get('title', 'N/A')}")
    print(f"   Description length: {len(script_data.get('description', ''))}")
    
    # Initialize generator
    print("\n🔧 Initializing SEO Thumbnail Generator...")
    generator = SEOThumbnailGenerator()
    
    # Test without OpenAI first (to show basic functionality)
    print("\n📦 Generating basic thumbnail (without GPT-3.5)...")
    
    try:
        # Generate complete package
        result = generator.generate_complete_package(
            video_path=video_path,
            script_data=script_data,
            output_dir="demo_thumbnails"
        )
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return 1
        
        # Show results
        print("\n✅ Generation completed successfully!")
        print("\n📊 Results Summary:")
        print(f"   Video source: {result['video_source']}")
        
        metadata = result['metadata']
        print(f"   Original title: {metadata.get('title', 'N/A')}")
        print(f"   Refined title: {metadata.get('refined_title', 'N/A')}")
        print(f"   Description length: {len(metadata.get('optimized_description', ''))}")
        print(f"   Tags count: {len(metadata.get('strategic_tags', []))}")
        print(f"   SEO score: {metadata.get('seo_score', 0)}/100")
        
        assets = result['assets']
        primary = assets['primary_thumbnail']
        dalle = assets['dalle_thumbnail']
        
        print(f"\n🖼️  Thumbnails generated:")
        print(f"   Primary thumbnail: {'✅' if primary['success'] else '❌'}")
        if primary['success']:
            print(f"      Path: {primary['path']}")
        
        print(f"   DALL-E thumbnail: {'✅' if dalle['success'] else '❌'}")
        if dalle['success']:
            print(f"      Path: {dalle['path']}")
        
        print(f"\n📁 All files saved in: demo_thumbnails/")
        
        # Test with OpenAI if API key is available
        if os.getenv('OPENAI_API_KEY'):
            print("\n🤖 OpenAI API key found! Testing GPT-3.5 refinement...")
            
            openai_generator = SEOThumbnailGenerator(openai_api_key=os.getenv('OPENAI_API_KEY'))
            
            # Test just the metadata refinement
            refined_metadata = openai_generator.refine_metadata_with_gpt(script_data)
            
            print("\n📈 GPT-3.5 Refinement Results:")
            print(f"   Refined title: {refined_metadata.get('refined_title', 'N/A')}")
            print(f"   Description length: {len(refined_metadata.get('optimized_description', ''))}")
            print(f"   Strategic tags: {len(refined_metadata.get('strategic_tags', []))}")
            print(f"   SEO score: {refined_metadata.get('seo_score', 0)}/100")
            
            if refined_metadata.get('strategic_tags'):
                print(f"   Tags preview: {', '.join(refined_metadata['strategic_tags'][:5])}...")
        else:
            print("\n💡 To test GPT-3.5 features, set your OPENAI_API_KEY environment variable")
        
        print("\n🎉 Demo completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
