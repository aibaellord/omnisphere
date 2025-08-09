# 🎬 Video Assembly Pipeline

A complete video production pipeline built with **FFmpeg** and **Python** that creates YouTube-ready videos with all the features required for modern content creation.

## ✨ Features

### Core Capabilities
- **📹 Video Creation**: Sync images/video clips with voice-over timestamps
- **📝 Kinetic Subtitles**: Add animated text subtitles using FFmpeg ASS format with kinetic effects
- **🎵 Background Music**: Mix background music at -18 dB for professional audio balance
- **🎥 YouTube Optimization**: Output MP4 (H.264, 720p) optimized for YouTube upload
- **📦 File Size Control**: Automatic optimization to keep videos under 100 MB
- **⚡ Fast Processing**: Uses FFmpeg for efficient video processing

### Technical Specifications
- **Video**: H.264 codec, 1280x720 (720p), 30fps
- **Audio**: AAC codec, configurable bitrate
- **Format**: MP4 with YouTube-optimized settings
- **Size Limit**: Automatic compression to stay under 100MB
- **Subtitles**: ASS format with fade-in/out and scale animations

## 🚀 Quick Start

### Basic Usage

```python
from build_video import VideoAssemblyPipeline, VideoAssets, SubtitleSegment

# Initialize the pipeline
pipeline = VideoAssemblyPipeline()

# Create video assets
assets = VideoAssets(
    voice_file="my_voice.mp3",
    subtitles=[
        SubtitleSegment("Hello World!", 0.0, 3.0),
        SubtitleSegment("This is amazing!", 3.0, 6.0),
    ]
)

# Build the video
result = pipeline.build_video(
    assets=assets,
    project_title="My First Video"
)

print(f"✅ Video created: {result.path}")
print(f"⏱️ Duration: {result.duration:.2f}s")
print(f"📁 Size: {result.file_size_mb:.1f} MB")
```

### Advanced Usage with Background Music and Images

```python
assets = VideoAssets(
    voice_file="voice.mp3",
    background_music="background.mp3",
    images=["image1.jpg", "image2.jpg", "image3.jpg"],
    subtitles=[
        SubtitleSegment("Welcome to my channel!", 0.0, 3.0),
        SubtitleSegment("Today we're exploring...", 3.0, 7.0),
        SubtitleSegment("Don't forget to subscribe!", 7.0, 10.0),
    ]
)

result = pipeline.build_video(assets=assets)
```

## 📋 Requirements

### System Dependencies
- **FFmpeg** (with libx264, AAC, and libass support)
- **Python 3.8+**

### Python Dependencies
```bash
pip install pillow  # For image processing (if needed)
```

### Installation Verification
```bash
# Check if FFmpeg is available
ffmpeg -version

# Check if required codecs are available
ffmpeg -codecs | grep -E "(libx264|aac|ass)"
```

## 🎛️ Configuration

### VideoConfig Options

```python
from build_video import VideoConfig

config = VideoConfig(
    width=1920,              # Video width (default: 1280)
    height=1080,             # Video height (default: 720)
    fps=30,                  # Frame rate (default: 30)
    bitrate="3000k",         # Video bitrate (default: "2000k")
    audio_bitrate="192k",    # Audio bitrate (default: "128k")
    background_music_volume="0.125",  # -18dB volume (default: "0.125")
    subtitle_fontsize=56,    # Subtitle font size (default: 48)
    max_file_size_mb=150     # Max file size (default: 100)
)

pipeline = VideoAssemblyPipeline(config)
```

## 📊 Asset Types

### 1. Voice Audio
- **Required**: Primary audio track (voice-over)
- **Formats**: MP3, WAV, M4A, AIFF
- **Recommendation**: 22050 Hz, mono for optimal file size

```python
assets = VideoAssets(voice_file="narration.mp3")
```

### 2. Background Video
- **Optional**: Custom background video
- **Formats**: MP4, MOV, AVI, MKV
- **Auto-processing**: Loops, crops, and scales to match duration and resolution

```python
assets = VideoAssets(
    voice_file="voice.mp3",
    background_video="background.mp4"
)
```

### 3. Image Slideshow
- **Optional**: Creates slideshow from images
- **Formats**: JPG, PNG, BMP, TIFF
- **Features**: Automatic transitions and scaling

```python
assets = VideoAssets(
    voice_file="voice.mp3",
    images=["slide1.jpg", "slide2.jpg", "slide3.jpg"]
)
```

### 4. Background Music
- **Optional**: Background music mixed at -18dB
- **Formats**: MP3, WAV, M4A
- **Auto-processing**: Loops to match voice duration, volume adjusted

```python
assets = VideoAssets(
    voice_file="voice.mp3",
    background_music="music.mp3"
)
```

### 5. Subtitles
- **Optional**: Kinetic text animations
- **Auto-generation**: Creates default subtitles if none provided
- **Kinetic Effects**: Fade in/out, scale animations

```python
from build_video import SubtitleSegment

subtitles = [
    SubtitleSegment("Opening line", 0.0, 3.0),
    SubtitleSegment("Main content", 3.0, 8.0),
    SubtitleSegment("Call to action", 8.0, 12.0),
]

assets = VideoAssets(
    voice_file="voice.mp3",
    subtitles=subtitles
)
```

## 🎨 Subtitle Styling

### ASS Format Features
- **Fade Effects**: Smooth fade in/out transitions
- **Scale Animations**: Text scales up on entry
- **Font Styling**: Configurable font, size, and colors
- **Positioning**: Bottom-center positioning optimized for readability

### Custom Styling
```python
# Subtitles support custom styling (advanced)
subtitle = SubtitleSegment(
    text="Custom styled text",
    start_time=0.0,
    end_time=3.0,
    style={
        "fontsize": 60,
        "color": "yellow",
        "outline_width": 3
    }
)
```

## 📈 Performance & Optimization

### Automatic Optimizations
- **File Size Management**: Automatically re-encodes if over size limit
- **Bitrate Calculation**: Dynamic bitrate adjustment based on duration
- **Two-pass Processing**: Separates subtitle rendering from audio mixing for efficiency
- **Temporary File Cleanup**: Automatic cleanup of intermediate files

### Manual Optimizations
```python
# For faster processing (lower quality)
config = VideoConfig(
    bitrate="1500k",
    audio_bitrate="96k"
)

# For higher quality (larger files)
config = VideoConfig(
    bitrate="5000k",
    audio_bitrate="256k",
    max_file_size_mb=200
)
```

## 🔍 Output Specifications

### Video Output (`VideoOutput`)
```python
result = pipeline.build_video(assets)

print(f"Path: {result.path}")              # Full path to video file
print(f"Duration: {result.duration}s")      # Video duration in seconds
print(f"Size: {result.file_size_mb} MB")    # File size in megabytes
print(f"Resolution: {result.resolution}")   # (width, height) tuple
print(f"Created: {result.created_at}")      # ISO timestamp
```

### File Structure
```
generated_videos/
├── video_1234567890.mp4      # Generated with timestamp
├── custom_name.mp4           # Custom filename
└── demo_with_music.mp4       # Named output
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

#### 2. Audio File Issues
```python
# Check audio file duration
pipeline._get_audio_duration("voice.mp3")
```

#### 3. Subtitle Timing Issues
```python
# Verify subtitle segments don't overlap
for i, sub in enumerate(subtitles[:-1]):
    if sub.end_time > subtitles[i+1].start_time:
        print(f"Overlap detected: {sub.text}")
```

#### 4. Large File Sizes
```python
# Use more aggressive compression
config = VideoConfig(
    bitrate="1000k",
    audio_bitrate="64k",
    max_file_size_mb=50
)
```

### Debugging

#### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Check FFmpeg Command
The pipeline logs the exact FFmpeg commands being executed:
```
INFO:__main__:Command: ffmpeg -i background.mp4 -i voice.mp3 ...
```

## 📚 Examples

### Example 1: Simple Video with Voice
```python
from build_video import VideoAssemblyPipeline, VideoAssets

pipeline = VideoAssemblyPipeline()
assets = VideoAssets(voice_file="podcast.mp3")
result = pipeline.build_video(assets, project_title="My Podcast")
```

### Example 2: Educational Content with Images
```python
assets = VideoAssets(
    voice_file="lecture.mp3",
    images=["slide1.jpg", "slide2.jpg", "slide3.jpg"],
    subtitles=[
        SubtitleSegment("Introduction to AI", 0.0, 5.0),
        SubtitleSegment("Machine Learning Basics", 5.0, 15.0),
        SubtitleSegment("Deep Learning Applications", 15.0, 25.0),
    ]
)
result = pipeline.build_video(assets)
```

### Example 3: YouTube Video with Music
```python
assets = VideoAssets(
    voice_file="commentary.mp3",
    background_music="upbeat_music.mp3",
    background_video="gameplay.mp4",
    subtitles=[
        SubtitleSegment("Welcome back to my channel!", 0.0, 3.0),
        SubtitleSegment("Today we're playing...", 3.0, 7.0),
        SubtitleSegment("Don't forget to like and subscribe!", 47.0, 50.0),
    ]
)

config = VideoConfig(max_file_size_mb=150)  # Larger for gaming content
result = pipeline.build_video(assets, "gaming_video.mp4")
```

### Example 4: Batch Processing
```python
voice_files = ["episode1.mp3", "episode2.mp3", "episode3.mp3"]
results = []

for i, voice_file in enumerate(voice_files, 1):
    assets = VideoAssets(voice_file=voice_file)
    result = pipeline.build_video(
        assets, 
        f"episode_{i:02d}.mp4",
        f"Podcast Episode {i}"
    )
    results.append(result)
    
print(f"✅ Created {len(results)} videos")
```

## 🎯 YouTube Upload Ready

The pipeline creates videos optimized for YouTube:

- **H.264 codec** (widely supported)
- **720p resolution** (good quality/size balance)  
- **30fps** (smooth playback)
- **AAC audio** (YouTube preferred)
- **Fast start** (web optimized)
- **Under 100MB** (fast upload on free tiers)

### Direct YouTube Integration
```python
# The output can be directly uploaded to YouTube
result = pipeline.build_video(assets)

# Use youtube-upload or similar tool
os.system(f'youtube-upload --title="My Video" "{result.path}"')
```

## 🔄 Integration with Existing Workflows

### With TTS Systems
```python
# Generate voice first
tts_output = generate_tts("My script text")
assets = VideoAssets(voice_file=tts_output)
video_result = pipeline.build_video(assets)
```

### With Content Management
```python
def process_script(script_data):
    """Process script data into video"""
    # Generate voice
    voice_file = create_voice_from_script(script_data['text'])
    
    # Create assets
    assets = VideoAssets(
        voice_file=voice_file,
        subtitles=script_data.get('subtitles', []),
        background_music=script_data.get('music')
    )
    
    # Generate video
    return pipeline.build_video(
        assets, 
        script_data['filename'],
        script_data['title']
    )
```

## 📄 License

This video assembly pipeline is designed for integration into content creation workflows and can be adapted for various use cases.

---

**Ready to create amazing videos?** 🎬 

Run `python build_video.py` to see the demo in action!
