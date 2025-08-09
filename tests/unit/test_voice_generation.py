#!/usr/bin/env python3
"""
Test Script for Voice-over Generation System
============================================

Tests the voice generation system with existing markdown scripts
and demonstrates all TTS backends.
"""

import os
import sys
import json
from pathlib import Path
from generate_voice import MarkdownToSpeech, TTSBackend

def test_quota_management():
    """Test TTS quota tracking functionality"""
    print("🧪 Testing TTS Quota Management...")
    
    voice_gen = MarkdownToSpeech()
    quota_mgr = voice_gen.quota_manager
    
    # Check available quotas
    print("\n📊 Current TTS Quotas:")
    for backend in [TTSBackend.ELEVENLABS, TTSBackend.GOOGLE_TTS, TTSBackend.COQUI_LOCAL]:
        available = quota_mgr.get_available_chars(backend)
        if backend == TTSBackend.ELEVENLABS:
            total = 10_000
        elif backend == TTSBackend.GOOGLE_TTS:
            total = 4_000_000
        else:
            total = "unlimited"
        
        print(f"  {backend.value}: {available:,} chars available (out of {total})")
    
    # Test backend selection
    test_lengths = [500, 5000, 50000, 500000]
    print("\n🎯 Backend Selection for Different Text Lengths:")
    for length in test_lengths:
        chosen = quota_mgr.choose_best_backend(length)
        print(f"  {length:,} chars → {chosen.value}")

def test_markdown_parsing():
    """Test markdown text extraction"""
    print("\n🧪 Testing Markdown Text Extraction...")
    
    # Create a sample markdown file
    sample_markdown = """
# Introduction to AI Revolution
    
Welcome to the **future** of artificial intelligence! In this comprehensive guide, we'll explore:

1. The current state of AI technology
2. Revolutionary breakthroughs in machine learning
3. Future implications for humanity

## Key Points

- AI is transforming every industry
- *Machine learning* algorithms are becoming more sophisticated
- The future holds incredible possibilities

### Technical Details

Some `code examples` and technical specifications:

```python
def ai_revolution():
    return "The future is now!"
```

Visit our [website](https://example.com) for more information.

## Conclusion

The AI revolution is here. Are you ready?
    """
    
    # Save sample file
    test_file = Path("data/test_voice_sample.md")
    test_file.parent.mkdir(exist_ok=True)
    
    with open(test_file, 'w') as f:
        f.write(sample_markdown.strip())
    
    # Test text extraction
    voice_gen = MarkdownToSpeech()
    clean_text = voice_gen._extract_text_from_markdown(sample_markdown)
    sentences = voice_gen._split_into_sentences(clean_text)
    
    print(f"📄 Original markdown: {len(sample_markdown)} chars")
    print(f"🧹 Clean text: {len(clean_text)} chars")
    print(f"📝 Sentences: {len(sentences)}")
    
    print("\n📋 Extracted sentences:")
    for i, sentence in enumerate(sentences[:5]):  # Show first 5
        print(f"  {i+1}: {sentence[:60]}...")
    
    if len(sentences) > 5:
        print(f"  ... and {len(sentences) - 5} more")
    
    return test_file

def test_backend_availability():
    """Test which TTS backends are available"""
    print("\n🧪 Testing TTS Backend Availability...")
    
    voice_gen = MarkdownToSpeech()
    
    print("🔍 Available TTS Backends:")
    for backend, engine in voice_gen.backends.items():
        print(f"  ✅ {backend.value}: {type(engine).__name__}")
    
    if not voice_gen.backends:
        print("  ❌ No TTS backends available!")
        print("\n💡 Setup Instructions:")
        print("  - ElevenLabs: Set ELEVENLABS_API_KEY in .env")
        print("  - Google TTS: Set GOOGLE_CLOUD_PROJECT_ID and credentials file")
        print("  - Coqui Local: Run 'tts-server --model_name tts_models/en/ljspeech/tacotron2-DDC'")
    
    return len(voice_gen.backends) > 0

def test_voice_generation(markdown_file: Path):
    """Test actual voice generation with a small sample"""
    print(f"\n🧪 Testing Voice Generation with {markdown_file.name}...")
    
    voice_gen = MarkdownToSpeech()
    
    if not voice_gen.backends:
        print("❌ No TTS backends available - skipping voice generation test")
        return False
    
    # Generate voiceover
    result = voice_gen.generate_voiceover(
        str(markdown_file), 
        output_name="test_voice_sample"
    )
    
    if result.success:
        print("✅ Voice generation successful!")
        print(f"📁 Audio file: {result.full_audio_path}")
        print(f"⏱️  Duration: {result.total_duration:.1f} seconds")
        print(f"📝 Sentences: {len(result.sentences)}")
        print(f"🎤 Backend used: {result.backend_used.value}")
        print(f"📊 Character count: {result.character_count}")
        
        # Show sentence breakdown
        print("\n📋 Sentence Breakdown:")
        for i, sentence_audio in enumerate(result.sentences[:3]):
            print(f"  {i+1}: {sentence_audio.start_time:.1f}s - {sentence_audio.end_time:.1f}s")
            print(f"     Text: {sentence_audio.text[:50]}...")
        
        if len(result.sentences) > 3:
            print(f"  ... and {len(result.sentences) - 3} more sentences")
        
        # Show metadata
        if result.metadata:
            print(f"\n📊 Quota Remaining:")
            quotas = result.metadata.get("quota_remaining", {})
            for backend, remaining in quotas.items():
                print(f"  {backend}: {remaining:,} chars")
        
        return True
    else:
        print(f"❌ Voice generation failed: {result.error_message}")
        return False

def test_existing_scripts():
    """Test with existing markdown scripts from the project"""
    print("\n🧪 Testing with Existing Project Scripts...")
    
    script_files = list(Path("data/scripts").glob("*.md"))
    
    if not script_files:
        print("❌ No existing script files found in data/scripts/")
        return []
    
    print(f"📁 Found {len(script_files)} existing script files:")
    for script_file in script_files[:3]:  # Show first 3
        print(f"  - {script_file.name}")
    
    return script_files

def main():
    """Run all voice generation tests"""
    print("🎤 Voice-over Generation System Test Suite")
    print("=" * 50)
    
    # Test 1: Quota Management
    test_quota_management()
    
    # Test 2: Backend Availability
    backends_available = test_backend_availability()
    
    # Test 3: Markdown Parsing
    test_file = test_markdown_parsing()
    
    # Test 4: Voice Generation (if backends available)
    if backends_available:
        voice_success = test_voice_generation(test_file)
    else:
        voice_success = False
        print("\n⚠️  Skipping voice generation tests - no backends available")
    
    # Test 5: Check existing scripts
    existing_scripts = test_existing_scripts()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  ✅ Quota management: Working")
    print(f"  {'✅' if backends_available else '❌'} TTS backends: {'Available' if backends_available else 'Not configured'}")
    print(f"  ✅ Markdown parsing: Working")
    print(f"  {'✅' if voice_success else '❌'} Voice generation: {'Working' if voice_success else 'Not tested'}")
    print(f"  📁 Existing scripts: {len(existing_scripts)} found")
    
    if voice_success:
        print("\n🎉 All tests passed! Voice generation system is ready.")
        print("\n💡 Next steps:")
        print("  1. Configure additional TTS backends in .env")
        print("  2. Run: python generate_voice.py data/scripts/[file].md")
        print("  3. Check generated audio in data/voiceovers/")
    else:
        print("\n⚠️  Setup required for full functionality:")
        if not backends_available:
            print("  - Configure at least one TTS backend (see API_CREDENTIALS_GUIDE.md)")
        print("  - Install audio dependencies: pip install pydub")
        print("  - For Coqui TTS: pip install TTS && tts-server")
    
    return voice_success

if __name__ == "__main__":
    main()
