#!/usr/bin/env python3
"""
🎬 VIDEO ASSEMBLY PIPELINE 🎬
Complete video production pipeline using FFmpeg + Python

Features:
- Sync images/video clips with voice-over timestamps
- Add kinetic text subtitles using FFmpeg drawtext
- Mix background music at -18 dB
- Output MP4 (H.264, 720p) < 100 MB for YouTube upload
- Returns path + duration

Author: AI Assistant
Date: 2024
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import re
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VideoConfig:
    """Video configuration settings"""
    width: int = 1280  # 720p width
    height: int = 720  # 720p height
    fps: int = 30
    bitrate: str = "2000k"  # Target bitrate for ~100MB output
    audio_bitrate: str = "128k"
    background_music_volume: str = "0.125"  # -18dB volume
    subtitle_fontsize: int = 48
    subtitle_color: str = "white"
    subtitle_outline_color: str = "black"
    subtitle_outline_width: int = 2
    max_file_size_mb: int = 100

@dataclass
class SubtitleSegment:
    """Individual subtitle segment with timing"""
    text: str
    start_time: float
    end_time: float
    style: Optional[Dict] = None

@dataclass
class VideoAssets:
    """Container for video assets"""
    voice_file: str
    background_video: Optional[str] = None
    background_music: Optional[str] = None
    images: Optional[List[str]] = None
    subtitles: Optional[List[SubtitleSegment]] = None

@dataclass
class VideoOutput:
    """Output metadata"""
    path: str
    duration: float
    file_size_mb: float
    resolution: Tuple[int, int]
    created_at: str

class VideoAssemblyPipeline:
    """
    Complete video assembly pipeline with all required features
    """
    
    def __init__(self, config: VideoConfig = None):
        self.config = config or VideoConfig()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="video_assembly_"))
        self.output_dir = Path("generated_videos")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("🎬 Video Assembly Pipeline initialized")
        logger.info(f"📁 Temp directory: {self.temp_dir}")
        logger.info(f"📂 Output directory: {self.output_dir}")
    
    def build_video(
        self, 
        assets: VideoAssets,
        output_filename: Optional[str] = None,
        project_title: str = "Generated Video"
    ) -> VideoOutput:
        """
        Main function to build a complete video
        
        Args:
            assets: VideoAssets containing all input files
            output_filename: Optional custom filename
            project_title: Title for the project
        
        Returns:
            VideoOutput with path and metadata
        """
        start_time = datetime.now()
        
        if not output_filename:
            timestamp = int(datetime.now().timestamp())
            output_filename = f"video_{timestamp}.mp4"
        
        output_path = self.output_dir / output_filename
        
        logger.info(f"🎬 Starting video assembly: {project_title}")
        logger.info(f"🎤 Voice file: {assets.voice_file}")
        
        try:
            # Step 1: Get audio duration
            duration = self._get_audio_duration(assets.voice_file)
            logger.info(f"⏱️ Total duration: {duration:.2f} seconds")
            
            # Step 2: Create background video
            background_video = self._create_background_video(assets, duration)
            
            # Step 3: Create subtitle file
            subtitle_file = self._create_subtitle_file(assets, duration)
            
            # Step 4: Assemble final video
            self._assemble_final_video(
                voice_file=assets.voice_file,
                background_video=background_video,
                subtitle_file=subtitle_file,
                background_music=assets.background_music,
                output_path=output_path
            )
            
            # Step 5: Optimize file size if needed
            self._optimize_file_size(output_path, duration)
            
            # Step 6: Create output metadata
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            result = VideoOutput(
                path=str(output_path),
                duration=duration,
                file_size_mb=file_size_mb,
                resolution=(self.config.width, self.config.height),
                created_at=start_time.isoformat()
            )
            
            logger.info(f"✅ Video assembly completed!")
            logger.info(f"📂 Output: {result.path}")
            logger.info(f"⏱️ Duration: {result.duration:.2f}s")
            logger.info(f"📁 Size: {result.file_size_mb:.1f} MB")
            
            # Cleanup
            self._cleanup()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in video assembly: {e}")
            self._cleanup()
            raise
    
    def _get_audio_duration(self, audio_file: str) -> float:
        """Get duration of audio file using FFprobe"""
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        cmd = [
            "ffprobe", "-v", "quiet", "-show_entries", 
            "format=duration", "-of", "csv=p=0", audio_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get audio duration: {result.stderr}")
        
        return float(result.stdout.strip())
    
    def _create_background_video(self, assets: VideoAssets, duration: float) -> str:
        """Create or prepare background video"""
        logger.info("🎥 Creating background video...")
        
        if assets.background_video and os.path.exists(assets.background_video):
            # Use provided background video
            return self._prepare_background_video(assets.background_video, duration)
        
        elif assets.images:
            # Create slideshow from images
            return self._create_image_slideshow(assets.images, duration)
        
        else:
            # Create simple gradient background
            return self._create_gradient_background(duration)
    
    def _prepare_background_video(self, video_file: str, duration: float) -> str:
        """Prepare background video with correct duration and resolution"""
        output_file = self.temp_dir / "background_prepared.mp4"
        
        cmd = [
            "ffmpeg", "-i", video_file,
            "-vf", f"scale={self.config.width}:{self.config.height}:force_original_aspect_ratio=increase,crop={self.config.width}:{self.config.height}",
            "-stream_loop", "-1",  # Loop input
            "-t", str(duration),    # Duration
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",  # No audio
            "-y", str(output_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_file)
    
    def _create_image_slideshow(self, images: List[str], duration: float) -> str:
        """Create slideshow from images"""
        logger.info(f"🖼️ Creating slideshow from {len(images)} images...")
        
        valid_images = [img for img in images if os.path.exists(img)]
        if not valid_images:
            return self._create_gradient_background(duration)
        
        output_file = self.temp_dir / "slideshow.mp4"
        time_per_image = duration / len(valid_images)
        
        # Create filter complex for slideshow with transitions
        filter_parts = []
        input_parts = []
        
        for i, img in enumerate(valid_images):
            input_parts.extend(["-loop", "1", "-t", str(time_per_image), "-i", img])
            
            # Scale each image
            filter_parts.append(
                f"[{i}:v]scale={self.config.width}:{self.config.height}:force_original_aspect_ratio=increase,"
                f"crop={self.config.width}:{self.config.height},setsar=1[img{i}]"
            )
        
        # Concatenate all images
        concat_inputs = "".join([f"[img{i}]" for i in range(len(valid_images))])
        filter_parts.append(f"{concat_inputs}concat=n={len(valid_images)}:v=1:a=0[outv]")
        
        filter_complex = ";".join(filter_parts)
        
        cmd = (
            ["ffmpeg"] + input_parts +
            ["-filter_complex", filter_complex, "-map", "[outv]",
             "-c:v", "libx264", "-preset", "fast", "-crf", "23",
             "-r", str(self.config.fps), "-y", str(output_file)]
        )
        
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_file)
    
    def _create_gradient_background(self, duration: float) -> str:
        """Create animated gradient background"""
        logger.info("🎨 Creating gradient background...")
        
        output_file = self.temp_dir / "gradient_bg.mp4"
        
        # Create animated gradient using FFmpeg color filter
        cmd = [
            "ffmpeg", "-f", "lavfi",
            "-i", f"color=c=0x1a1928:s={self.config.width}x{self.config.height}:d={duration}",
            "-vf", "fade=in:0:30,fade=out:st={}:d=30".format(max(0, duration-1)),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-r", str(self.config.fps), "-y", str(output_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_file)
    
    def _create_subtitle_file(self, assets: VideoAssets, duration: float) -> str:
        """Create subtitle file in ASS format for kinetic effects"""
        logger.info("📝 Creating subtitle file...")
        
        if assets.subtitles:
            subtitle_data = assets.subtitles
        else:
            subtitle_data = self._generate_auto_subtitles(duration)
        
        subtitle_file = self.temp_dir / "subtitles.ass"
        
        # ASS subtitle format with kinetic effects
        ass_content = self._create_ass_subtitle_content(subtitle_data)
        
        with open(subtitle_file, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        return str(subtitle_file)
    
    def _generate_auto_subtitles(self, duration: float) -> List[SubtitleSegment]:
        """Generate automatic subtitles based on duration"""
        words = [
            "Welcome to this video",
            "Today we'll explore amazing content", 
            "Get ready for incredible insights",
            "Don't forget to subscribe",
            "Thanks for watching!"
        ]
        
        segments = []
        segment_duration = duration / len(words)
        
        for i, word in enumerate(words):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration
            
            segments.append(SubtitleSegment(
                text=word,
                start_time=start_time,
                end_time=end_time
            ))
        
        return segments
    
    def _create_ass_subtitle_content(self, subtitles: List[SubtitleSegment]) -> str:
        """Create ASS subtitle content with kinetic effects"""
        ass_header = """[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{fontsize},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{outline_width},0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(
    fontsize=self.config.subtitle_fontsize,
    outline_width=self.config.subtitle_outline_width
)
        
        events = []
        for sub in subtitles:
            start_time = self._seconds_to_ass_time(sub.start_time)
            end_time = self._seconds_to_ass_time(sub.end_time)
            
            # Add kinetic effects with ASS tags
            text_with_effects = f"{{\\fad(300,300)}}{{\\t(0,300,\\fscx120\\fscy120)}}{{\\t(300,600,\\fscx100\\fscy100)}}{sub.text}"
            
            events.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text_with_effects}")
        
        return ass_header + "\n".join(events)
    
    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def _assemble_final_video(
        self,
        voice_file: str,
        background_video: str,
        subtitle_file: str,
        background_music: Optional[str],
        output_path: Path
    ):
        """Assemble final video with all components"""
        logger.info("🎬 Assembling final video...")
        
        # Build FFmpeg command
        inputs = ["-i", background_video, "-i", voice_file]
        
        # Simplify: first create video with subtitles, then add audio
        temp_video = self.temp_dir / "temp_with_subs.mp4"
        
        # Step 1: Add subtitles to video
        cmd1 = [
            "ffmpeg", "-i", background_video,
            "-vf", f"ass={subtitle_file}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",  # No audio yet
            "-y", str(temp_video)
        ]
        
        logger.info("Adding subtitles...")
        subprocess.run(cmd1, check=True, capture_output=True)
        
        # Step 2: Add audio (and background music if provided)
        if background_music and os.path.exists(background_music):
            # Mix voice and background music
            cmd = [
                "ffmpeg", "-i", str(temp_video), "-i", voice_file, "-i", background_music,
                "-filter_complex", f"[1:a][2:a]amix=inputs=2:duration=shortest:weights=1 {self.config.background_music_volume}",
                "-c:v", "copy",  # Copy video stream
                "-c:a", "aac", "-b:a", self.config.audio_bitrate,
                "-movflags", "+faststart",
                "-y", str(output_path)
            ]
        else:
            # Just add voice
            cmd = [
                "ffmpeg", "-i", str(temp_video), "-i", voice_file,
                "-c:v", "copy",  # Copy video stream
                "-c:a", "aac", "-b:a", self.config.audio_bitrate,
                "-shortest",  # Match shortest stream
                "-movflags", "+faststart",
                "-y", str(output_path)
            ]
        
        logger.info("🔄 Running FFmpeg...")
        logger.info(f"Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
    
    def _optimize_file_size(self, output_path: Path, duration: float):
        """Optimize file size if it exceeds the limit"""
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        if file_size_mb > self.config.max_file_size_mb:
            logger.warning(f"📏 File size ({file_size_mb:.1f}MB) exceeds limit, optimizing...")
            
            # Calculate target bitrate
            target_size_bits = self.config.max_file_size_mb * 8 * 1024 * 1024 * 0.9
            target_bitrate = int(target_size_bits / duration)
            
            temp_output = self.temp_dir / "optimized.mp4"
            
            cmd = [
                "ffmpeg", "-i", str(output_path),
                "-c:v", "libx264", "-preset", "medium",
                "-b:v", f"{target_bitrate}",
                "-maxrate", f"{target_bitrate}",
                "-bufsize", f"{target_bitrate * 2}",
                "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart", "-pix_fmt", "yuv420p",
                "-y", str(temp_output)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Replace original with optimized version
            temp_output.replace(output_path)
            
            new_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✅ Optimized file size: {new_size_mb:.1f} MB")
    
    def _cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info("🧹 Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up temp files: {e}")

def create_sample_assets() -> VideoAssets:
    """Create sample assets for testing"""
    # Create a sample voice file using system TTS
    voice_file = "sample_voice.mp3"
    
    if not os.path.exists(voice_file):
        sample_text = """
        Welcome to this amazing video! Today we're going to explore 
        the fascinating world of AI and technology. This is just 
        a sample demonstration of our video assembly pipeline. 
        Get ready for some incredible insights that will blow your mind!
        Make sure to subscribe for more amazing content!
        """
        
        try:
            # Use system TTS (macOS)
            subprocess.run([
                "say", "-v", "Alex", "-r", "175", 
                "-o", "sample_voice.aiff", sample_text
            ], check=True)
            
            # Convert to MP3
            subprocess.run([
                "ffmpeg", "-i", "sample_voice.aiff", 
                "-acodec", "mp3", voice_file, "-y"
            ], check=True, capture_output=True)
            
            # Clean up
            os.remove("sample_voice.aiff")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create sample voice: {e}")
            raise
    
    # Create sample subtitles with better timing
    subtitles = [
        SubtitleSegment("Welcome to this amazing video!", 0.0, 3.5),
        SubtitleSegment("Today we're exploring AI and technology", 3.5, 7.5),
        SubtitleSegment("This is a sample demonstration", 7.5, 11.0),
        SubtitleSegment("Get ready for incredible insights!", 11.0, 14.5),
        SubtitleSegment("Make sure to subscribe!", 14.5, 18.0),
    ]
    
    return VideoAssets(
        voice_file=voice_file,
        subtitles=subtitles
    )

def demo_with_background_music():
    """Demo with background music"""
    # Create a simple background music file (sine wave)
    music_file = "background_music.mp3"
    if not os.path.exists(music_file):
        cmd = [
            "ffmpeg", "-f", "lavfi", "-i", "sine=frequency=200:duration=20",
            "-ac", "1", "-ar", "22050", "-y", music_file
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    
    # Test with background music
    config = VideoConfig()
    pipeline = VideoAssemblyPipeline(config)
    
    assets = VideoAssets(
        voice_file="sample_voice.mp3",
        background_music=music_file,
        subtitles=[
            SubtitleSegment("This video has background music!", 0.0, 4.0),
            SubtitleSegment("Music is mixed at -18dB", 4.0, 8.0),
            SubtitleSegment("Perfect for YouTube uploads", 8.0, 12.0),
            SubtitleSegment("Subscribe for more!", 12.0, 17.0),
        ]
    )
    
    return pipeline.build_video(
        assets=assets,
        output_filename="demo_with_music.mp4",
        project_title="Demo with Background Music"
    )

def main():
    """Demo the video assembly pipeline"""
    print("🎬 Video Assembly Pipeline Demo")
    print("=" * 50)
    
    # Initialize pipeline
    config = VideoConfig()
    pipeline = VideoAssemblyPipeline(config)
    
    # Create sample assets
    print("📋 Creating sample assets...")
    assets = create_sample_assets()
    
    # Build video
    print("🚀 Starting video assembly...")
    result = pipeline.build_video(
        assets=assets,
        project_title="Sample Demo Video"
    )
    
    print("\n✅ Video Assembly Completed!")
    print(f"📂 Output Path: {result.path}")
    print(f"⏱️ Duration: {result.duration:.2f} seconds")
    print(f"📁 File Size: {result.file_size_mb:.1f} MB")
    print(f"🎬 Resolution: {result.resolution[0]}x{result.resolution[1]}")
    print(f"🕐 Created: {result.created_at}")
    
    # Also test with background music
    print("\n🎵 Testing with background music...")
    result_music = demo_with_background_music()
    
    print("\n✅ Music Demo Completed!")
    print(f"📂 Output Path: {result_music.path}")
    print(f"⏱️ Duration: {result_music.duration:.2f} seconds")
    print(f"📁 File Size: {result_music.file_size_mb:.1f} MB")
    
    return result, result_music

if __name__ == "__main__":
    main()
