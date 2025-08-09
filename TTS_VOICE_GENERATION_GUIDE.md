# 🎤 TTS Voice-over Generation Guide

Complete guide for setting up and using the voice-over generation system in OmniSphere.

## 🎯 Overview

The voice-over system converts markdown scripts to MP3 audio with multiple TTS backend support:

- **ElevenLabs API** (`voice_id="Adam"`) - Highest quality, 10k chars/mo free
- **Google Cloud TTS** (standard voices) - Good quality, 4M chars/mo free  
- **Local Coqui TTS** server - Unlimited, free, runs locally

**Key Features:**
- ✅ Automatic backend selection based on remaining quota
- ✅ Sentence-level audio splitting for easier video editing
- ✅ Audio files + timestamp metadata storage
- ✅ Progress tracking and quota management
- ✅ Error handling and fallback systems

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Installation & Setup](#installation--setup)
3. [TTS Backend Configuration](#tts-backend-configuration)
4. [Usage Examples](#usage-examples)
5. [Audio Output Structure](#audio-output-structure)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install pydub requests python-dotenv

# 2. Configure at least one TTS backend (see sections below)

# 3. Test the system
python test_voice_generation.py

# 4. Generate voiceover from existing script
python generate_voice.py data/scripts/your_script.md

# 5. Check output
ls data/voiceovers/
```

---

## 🛠️ Installation & Setup

### Core Dependencies

```bash
# Required for all backends
pip install pydub requests python-dotenv

# For audio processing (system dependency)
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: Download from https://ffmpeg.org/
```

### Optional TTS Backend Dependencies

```bash
# For Google Cloud TTS
pip install google-cloud-texttospeech

# For Local Coqui TTS
pip install TTS
```

### Project Structure Setup

```bash
# Create necessary directories
mkdir -p data/voiceovers
mkdir -p data/tts_usage
mkdir -p credentials
```

---

## 🔧 TTS Backend Configuration

### 1. ElevenLabs API (Recommended)

**Quota:** 10,000 characters/month free  
**Quality:** Excellent, natural-sounding voices

```bash
# 1. Sign up at https://elevenlabs.io/
# 2. Get API key from Profile Settings
# 3. Add to .env file:
echo "ELEVENLABS_API_KEY=your-api-key-here" >> .env
```

**Voice Options:**
- `Adam` (default) - Professional male voice
- `Bella` - Female voice
- `Antoni` - Casual male voice
- `Elli` - Young female voice

### 2. Google Cloud TTS

**Quota:** 4,000,000 characters/month free  
**Quality:** Good, consistent voices

```bash
# 1. Enable Cloud Text-to-Speech API in Google Cloud Console
# 2. Create service account and download JSON key
# 3. Save key as ./credentials/google-cloud-service-account.json
# 4. Add to .env:
echo "GOOGLE_CLOUD_PROJECT_ID=your-project-id" >> .env
```

### 3. Local Coqui TTS (No Quota Limits)

**Quota:** Unlimited (runs locally)  
**Quality:** Good, customizable

```bash
# 1. Install TTS
pip install TTS

# 2. Start TTS server
tts-server --model_name tts_models/en/ljspeech/tacotron2-DDC --port 5002

# 3. Add to .env (optional, default values):
echo "COQUI_TTS_URL=http://localhost:5002" >> .env
```

**Alternative Coqui Models:**
```bash
# List available models
tts --list_models

# High-quality English models
tts-server --model_name tts_models/en/vctk/vits
tts-server --model_name tts_models/en/ljspeech/glow-tts
```

---

## 📖 Usage Examples

### Basic Voice Generation

```bash
# Generate voiceover from markdown script
python generate_voice.py data/scripts/ai_revolution.md

# Custom output name
python generate_voice.py data/scripts/ai_revolution.md --output "my_voiceover"

# Check quota usage
python generate_voice.py --list-quota
```

### Python API Usage

```python
from generate_voice import MarkdownToSpeech

# Initialize voice generator
voice_gen = MarkdownToSpeech(output_dir="data/voiceovers")

# Generate voiceover
result = voice_gen.generate_voiceover(
    markdown_file="data/scripts/sample.md",
    output_name="sample_voiceover"
)

if result.success:
    print(f"✅ Generated: {result.full_audio_path}")
    print(f"Duration: {result.total_duration:.1f}s")
    print(f"Sentences: {len(result.sentences)}")
    print(f"Backend: {result.backend_used.value}")
else:
    print(f"❌ Error: {result.error_message}")
```

### Batch Processing

```python
from pathlib import Path
from generate_voice import MarkdownToSpeech

voice_gen = MarkdownToSpeech()

# Process all markdown files in scripts directory
for script_file in Path("data/scripts").glob("*.md"):
    print(f"Processing {script_file.name}...")
    result = voice_gen.generate_voiceover(str(script_file))
    
    if result.success:
        print(f"✅ {script_file.name} → {result.total_duration:.1f}s")
    else:
        print(f"❌ {script_file.name} failed: {result.error_message}")
```

---

## 📁 Audio Output Structure

### Generated Files

```
data/voiceovers/
├── script_name_voiceover.mp3          # Full combined audio
├── script_name_metadata.json          # Generation metadata
└── script_name_sentences/             # Individual sentence files
    ├── sentence_000.mp3
    ├── sentence_001.mp3
    └── ...
```

### Metadata Structure

```json
{
  "source_file": "data/scripts/ai_revolution.md",
  "generated_at": "2024-01-15T10:30:00Z",
  "backend_used": "elevenlabs",
  "total_sentences": 12,
  "character_count": 1250,
  "quota_remaining": {
    "elevenlabs": 8750,
    "google_tts": 4000000
  }
}
```

### Sentence Audio Objects

```python
# Each sentence includes:
{
  "text": "Welcome to the AI revolution.",
  "start_time": 0.0,      # Seconds from start
  "end_time": 3.2,        # End timestamp
  "duration": 3.2,        # Sentence duration
  "sentence_index": 0,    # Position in script
  "file_path": "data/voiceovers/script_sentences/sentence_000.mp3"
}
```

---

## 🔥 Advanced Features

### Quota Management

The system automatically tracks usage across TTS services:

```python
from generate_voice import TTSQuotaManager

quota_mgr = TTSQuotaManager()

# Check available characters
elevenlabs_remaining = quota_mgr.get_available_chars(TTSBackend.ELEVENLABS)
google_remaining = quota_mgr.get_available_chars(TTSBackend.GOOGLE_TTS)

print(f"ElevenLabs: {elevenlabs_remaining:,} chars remaining")
print(f"Google TTS: {google_remaining:,} chars remaining")

# Backend selection for optimal usage
best_backend = quota_mgr.choose_best_backend(text_length=5000)
print(f"Recommended backend: {best_backend.value}")
```

### Custom Voice Selection

```python
# ElevenLabs with different voice
from generate_voice import ElevenLabsTTS

elevenlabs = ElevenLabsTTS(
    api_key="your-key",
    voice_id="Bella"  # Female voice
)

# Google TTS with different voice
from generate_voice import GoogleTTS
from google.cloud import texttospeech

google_tts = GoogleTTS("project-id", "credentials.json")
google_tts.voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Standard-C"  # Different voice
)
```

### Markdown Processing Customization

```python
voice_gen = MarkdownToSpeech()

# Custom text extraction (modify regex patterns)
def custom_extract_text(markdown_content):
    # Add your custom markdown processing
    return processed_text

# Override the method
voice_gen._extract_text_from_markdown = custom_extract_text
```

---

## 🐛 Troubleshooting

### Common Issues

**"No TTS backends available"**
```bash
# Check .env configuration
cat .env | grep -E "(ELEVENLABS|GOOGLE_CLOUD|COQUI)"

# Test API keys
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('ElevenLabs:', bool(os.getenv('ELEVENLABS_API_KEY')))
print('Google:', bool(os.getenv('GOOGLE_CLOUD_PROJECT_ID')))
"
```

**"ModuleNotFoundError: No module named 'pydub'"**
```bash
pip install pydub
# Also install system dependency:
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

**"Google Cloud authentication error"**
```bash
# Check credentials file
ls -la ./credentials/google-cloud-service-account.json

# Test authentication
export GOOGLE_APPLICATION_CREDENTIALS="./credentials/google-cloud-service-account.json"
python -c "from google.cloud import texttospeech; print('✅ Google TTS authenticated')"
```

**"ElevenLabs API quota exceeded"**
```bash
# Check quota usage
python generate_voice.py --list-quota

# Reset monthly quota (manual)
python -c "
from generate_voice import TTSQuotaManager
mgr = TTSQuotaManager()
mgr.usage_data['elevenlabs']['chars_used'] = 0
mgr._save_usage()
print('✅ ElevenLabs quota reset')
"
```

**"Coqui TTS server not responding"**
```bash
# Check if server is running
curl http://localhost:5002/api/tts

# Start server if not running
tts-server --model_name tts_models/en/ljspeech/tacotron2-DDC --port 5002
```

### Audio Quality Issues

**Robotic/choppy audio:**
- Try ElevenLabs for highest quality
- Adjust sentence splitting (longer sentences = more natural flow)
- Use higher-quality Coqui models

**Audio too fast/slow:**
- Modify TTS voice settings in the backend classes
- For ElevenLabs, adjust `voice_settings` parameters

**Background noise:**
- Use cloud TTS services (ElevenLabs/Google) instead of local
- Check audio processing chain for issues

---

## 📊 Performance & Quota Guidelines

### Backend Comparison

| Backend | Quality | Speed | Quota | Best For |
|---------|---------|-------|-------|----------|
| ElevenLabs | ⭐⭐⭐⭐⭐ | Medium | 10k/mo | Production, demos |
| Google TTS | ⭐⭐⭐⭐ | Fast | 4M/mo | High-volume, testing |
| Coqui Local | ⭐⭐⭐ | Slow | Unlimited | Development, privacy |

### Character Count Estimates

- Short script (1-2 min): ~500-1000 chars
- Medium script (5-10 min): ~2000-5000 chars  
- Long script (15-30 min): ~8000-15000 chars

### Optimal Usage Patterns

1. **Development phase**: Use Coqui Local for unlimited testing
2. **Final production**: Use ElevenLabs for highest quality
3. **High-volume content**: Use Google TTS for cost efficiency
4. **Batch processing**: System auto-selects optimal backend

---

## 🚀 Next Steps

After setting up voice generation:

1. **Integrate with video pipeline**: Combine with video generation tools
2. **Custom voice training**: Train Coqui models on specific voices
3. **Multi-language support**: Add support for other languages
4. **Voice cloning**: Use ElevenLabs voice cloning features
5. **Audio post-processing**: Add effects, normalization, etc.

---

## 🔗 Related Documentation

- [API_CREDENTIALS_GUIDE.md](API_CREDENTIALS_GUIDE.md) - API setup instructions
- [generate_script.py](generate_script.py) - Script generation system
- [OmniSphere Documentation](README.md) - Main project documentation

---

## 💡 Tips & Best Practices

### For Video Editors
- Use individual sentence files for precise video sync
- Sentence timestamps help with automated subtitle generation
- Pause between sentences allows for smooth cuts

### For Content Creators  
- Test different voices to match your brand
- Monitor quota usage to avoid interruptions
- Keep backup TTS configured for failover

### For Developers
- The system is modular - easy to add new TTS backends
- Quota management prevents unexpected API costs
- Error handling ensures graceful degradation

---

🎉 **Your voice-over generation system is ready!** Start creating professional audio content from your markdown scripts.
