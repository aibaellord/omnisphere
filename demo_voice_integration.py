#!/usr/bin/env python3
"""
Voice Integration Demo - Complete Workflow
==========================================

Demonstrates the complete workflow from:
1. Script generation (existing system)
2. Voice-over generation (new TTS system)
3. Combined output for video production

This shows how the voice generation integrates with the existing OmniSphere system.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime

# Import existing OmniSphere components
try:
    from generate_script import ScriptGenerator
    script_gen_available = True
except ImportError as e:
    print(f"⚠️  Script generation not available: {e}")
    script_gen_available = False

# Import voice generation (always needed for demo)
from generate_voice import MarkdownToSpeech, TTSBackend

def demo_complete_workflow():
    """Demonstrate complete workflow with script + voice generation"""
    print("🎬 Complete Content Creation Workflow Demo")
    print("=" * 55)
    
    # Step 1: Check existing scripts
    print("\n📋 Step 1: Available Scripts")
    scripts_dir = Path("data/scripts")
    existing_scripts = list(scripts_dir.glob("*.md")) if scripts_dir.exists() else []
    
    if existing_scripts:
        print(f"Found {len(existing_scripts)} existing scripts:")
        for script in existing_scripts[:3]:
            print(f"  - {script.name}")
        
        # Use first existing script for demo
        demo_script = existing_scripts[0]
        print(f"\n✅ Using existing script: {demo_script.name}")
        
        # Read script content for analysis
        with open(demo_script, 'r') as f:
            content = f.read()
            word_count = len(content.split())
            char_count = len(content)
            
        print(f"   📊 Content: {word_count} words, {char_count} characters")
        
    else:
        print("❌ No existing scripts found in data/scripts/")
        print("   💡 Run script generation first: python generate_script.py")
        return False
    
    # Step 2: Voice-over generation
    print(f"\n🎤 Step 2: Voice-over Generation")
    voice_gen = MarkdownToSpeech()
    
    # Check available TTS backends
    if not voice_gen.backends:
        print("❌ No TTS backends configured")
        print("   💡 See TTS_VOICE_GENERATION_GUIDE.md for setup")
        print("   💡 Quick test: Set ELEVENLABS_API_KEY in .env")
        return False
    
    print("✅ TTS backends available:")
    for backend in voice_gen.backends.keys():
        print(f"   - {backend.value}")
    
    # Show quota status
    print(f"\n📊 Current TTS Quotas:")
    quota_mgr = voice_gen.quota_manager
    for backend in [TTSBackend.ELEVENLABS, TTSBackend.GOOGLE_TTS]:
        available = quota_mgr.get_available_chars(backend)
        if backend == TTSBackend.ELEVENLABS:
            total = 10_000
        else:
            total = 4_000_000
        used = total - available
        print(f"   {backend.value}: {used:,}/{total:,} used ({available:,} remaining)")
    
    # Generate voice-over
    print(f"\n🎙️  Generating voice-over...")
    start_time = time.time()
    
    result = voice_gen.generate_voiceover(
        str(demo_script),
        output_name=f"demo_{demo_script.stem}"
    )
    
    generation_time = time.time() - start_time
    
    if result.success:
        print(f"✅ Voice-over generated in {generation_time:.1f}s")
        print(f"   📁 Audio file: {result.full_audio_path}")
        print(f"   ⏱️  Duration: {result.total_duration:.1f} seconds") 
        print(f"   📝 Sentences: {len(result.sentences)}")
        print(f"   🎤 Backend used: {result.backend_used.value}")
        print(f"   📊 Characters: {result.character_count:,}")
        
        # Show sentence breakdown for video editing
        print(f"\n🎬 Video Editing Information:")
        print(f"   Individual sentence files in: {Path(result.full_audio_path).parent}/{Path(result.full_audio_path).stem.replace('_voiceover', '')}_sentences/")
        
        # Show first few sentence timings
        print(f"   Sentence timings for sync:")
        for i, sentence in enumerate(result.sentences[:3]):
            print(f"     {i+1:2d}: {sentence.start_time:5.1f}s - {sentence.end_time:5.1f}s | {sentence.text[:40]}...")
        
        if len(result.sentences) > 3:
            print(f"     ... and {len(result.sentences) - 3} more sentences")
            
        return result
    else:
        print(f"❌ Voice generation failed: {result.error_message}")
        return False

def demo_production_ready_workflow():
    """Show production-ready workflow with all metadata"""
    print("\n" + "=" * 55)
    print("🏭 Production-Ready Workflow")
    print("=" * 55)
    
    # Get all scripts
    scripts_dir = Path("data/scripts")
    if not scripts_dir.exists():
        print("❌ No scripts directory found")
        return
    
    script_files = list(scripts_dir.glob("*.md"))
    if not script_files:
        print("❌ No script files found")
        return
    
    voice_gen = MarkdownToSpeech()
    if not voice_gen.backends:
        print("❌ No TTS backends available")
        return
    
    print(f"📦 Processing {len(script_files)} scripts for production...")
    
    production_summary = {
        "processed_at": datetime.now().isoformat(),
        "scripts_processed": [],
        "total_duration": 0.0,
        "total_characters": 0,
        "backends_used": set(),
        "success_count": 0,
        "error_count": 0
    }
    
    for i, script_file in enumerate(script_files):
        print(f"\n📄 Processing {i+1}/{len(script_files)}: {script_file.name}")
        
        # Generate voice-over
        result = voice_gen.generate_voiceover(
            str(script_file),
            output_name=f"prod_{script_file.stem}"
        )
        
        script_info = {
            "script_file": script_file.name,
            "success": result.success
        }
        
        if result.success:
            script_info.update({
                "audio_file": result.full_audio_path,
                "duration": result.total_duration,
                "sentences": len(result.sentences),
                "characters": result.character_count,
                "backend_used": result.backend_used.value
            })
            
            production_summary["total_duration"] += result.total_duration
            production_summary["total_characters"] += result.character_count
            production_summary["backends_used"].add(result.backend_used.value)
            production_summary["success_count"] += 1
            
            print(f"   ✅ Generated: {result.total_duration:.1f}s, {result.character_count} chars")
        else:
            script_info["error"] = result.error_message
            production_summary["error_count"] += 1
            print(f"   ❌ Failed: {result.error_message}")
        
        production_summary["scripts_processed"].append(script_info)
    
    # Convert set to list for JSON serialization
    production_summary["backends_used"] = list(production_summary["backends_used"])
    
    # Save production summary
    summary_file = Path("data/voiceovers/production_summary.json")
    summary_file.parent.mkdir(exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump(production_summary, f, indent=2)
    
    # Display summary
    print(f"\n📊 Production Summary:")
    print(f"   ✅ Success: {production_summary['success_count']}/{len(script_files)}")
    print(f"   ⏱️  Total duration: {production_summary['total_duration']:.1f} seconds")
    print(f"   📝 Total characters: {production_summary['total_characters']:,}")
    print(f"   🎤 Backends used: {', '.join(production_summary['backends_used'])}")
    print(f"   📁 Summary saved: {summary_file}")
    
    return production_summary

def demo_quota_optimization():
    """Demonstrate intelligent quota usage across backends"""
    print("\n" + "=" * 55)
    print("🧮 Smart Quota Management Demo")
    print("=" * 55)
    
    voice_gen = MarkdownToSpeech()
    quota_mgr = voice_gen.quota_manager
    
    # Simulate different text lengths and show optimal backend selection
    test_scenarios = [
        ("Short social media clip", 300),
        ("Medium blog post", 2500),
        ("Long tutorial script", 8000),
        ("Very long documentary", 25000),
        ("Massive training content", 100000)
    ]
    
    print("💡 Optimal backend selection for different content types:")
    
    for scenario_name, char_count in test_scenarios:
        optimal_backend = quota_mgr.choose_best_backend(char_count)
        
        # Show what would happen with each backend
        elevenlabs_remaining = quota_mgr.get_available_chars(TTSBackend.ELEVENLABS)
        google_remaining = quota_mgr.get_available_chars(TTSBackend.GOOGLE_TTS)
        
        print(f"\n   📝 {scenario_name} ({char_count:,} chars):")
        print(f"      🎯 Optimal: {optimal_backend.value}")
        
        # Show feasibility for each backend
        if char_count <= elevenlabs_remaining:
            print(f"      ✅ ElevenLabs: Available ({elevenlabs_remaining:,} remaining)")
        else:
            print(f"      ❌ ElevenLabs: Exceeds quota (need {char_count - elevenlabs_remaining:,} more)")
        
        if char_count <= google_remaining:
            print(f"      ✅ Google TTS: Available ({google_remaining:,} remaining)")
        else:
            print(f"      ❌ Google TTS: Exceeds quota (need {char_count - google_remaining:,} more)")
        
        print(f"      ♾️  Coqui Local: Always available (unlimited)")

def main():
    """Main demo function"""
    print("🎤 OmniSphere Voice Generation Integration Demo")
    print("This demo shows the complete content creation workflow")
    print("from script generation to voice-over production.\n")
    
    # Demo 1: Complete workflow
    result = demo_complete_workflow()
    
    if result:
        # Demo 2: Production workflow (only if voice generation works)
        demo_production_ready_workflow()
        
        # Demo 3: Quota optimization
        demo_quota_optimization()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"\n🚀 Next Steps:")
        print(f"   1. Configure more TTS backends for redundancy")
        print(f"   2. Integrate with video generation pipeline")
        print(f"   3. Set up automated batch processing")
        print(f"   4. Add custom voice training (Coqui)")
        print(f"   5. Implement audio post-processing effects")
        
    else:
        print(f"\n⚠️  Demo limited due to missing configuration")
        print(f"   See TTS_VOICE_GENERATION_GUIDE.md for setup instructions")
    
    print(f"\n📚 Documentation:")
    print(f"   - TTS_VOICE_GENERATION_GUIDE.md - Complete setup guide")
    print(f"   - API_CREDENTIALS_GUIDE.md - API configuration")
    print(f"   - generate_voice.py - Main voice generation system")

if __name__ == "__main__":
    main()
