#!/usr/bin/env python3
"""
Voice-over Generation System for OmniSphere
============================================

Converts markdown scripts to MP3 audio with multiple TTS backend support:
- ElevenLabs API (voice_id="Adam")  
- Google Cloud TTS (standard voices, 4M chars/mo free)
- Local Coqui TTS server

Features:
- Automatic TTS backend selection based on quota
- Sentence-level splitting for video editing
- Audio + timestamp storage
- Progress tracking and error handling
"""

import os
import re
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import requests
import pydub
from pydub import AudioSegment
from pydub.silence import detect_silence

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSBackend(Enum):
    ELEVENLABS = "elevenlabs"
    GOOGLE_TTS = "google_tts"
    COQUI_LOCAL = "coqui_local"

@dataclass
class SentenceAudio:
    """Container for sentence audio data with timestamps"""
    text: str
    audio_segment: AudioSegment
    start_time: float
    end_time: float
    duration: float
    sentence_index: int
    file_path: Optional[str] = None

@dataclass
class VoiceoverResult:
    """Complete voiceover generation result"""
    success: bool
    full_audio_path: str
    sentences: List[SentenceAudio]
    backend_used: TTSBackend
    total_duration: float
    character_count: int
    error_message: Optional[str] = None
    metadata: Dict = None

class TTSQuotaManager:
    """Manages TTS service quotas and usage tracking"""
    
    def __init__(self, usage_file: str = "data/tts_usage.json"):
        self.usage_file = Path(usage_file)
        self.usage_file.parent.mkdir(exist_ok=True)
        self.usage_data = self._load_usage()
    
    def _load_usage(self) -> Dict:
        """Load usage data from file"""
        if self.usage_file.exists():
            with open(self.usage_file, 'r') as f:
                return json.load(f)
        return {
            "elevenlabs": {"chars_used": 0, "last_reset": datetime.now().isoformat()},
            "google_tts": {"chars_used": 0, "last_reset": datetime.now().isoformat()},
        }
    
    def _save_usage(self):
        """Save usage data to file"""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def get_available_chars(self, backend: TTSBackend) -> int:
        """Get remaining character quota for backend"""
        if backend == TTSBackend.ELEVENLABS:
            # 10,000 chars/month free tier
            used = self.usage_data["elevenlabs"]["chars_used"]
            return max(0, 10000 - used)
        elif backend == TTSBackend.GOOGLE_TTS:
            # 4,000,000 chars/month free tier
            used = self.usage_data["google_tts"]["chars_used"]
            return max(0, 4_000_000 - used)
        elif backend == TTSBackend.COQUI_LOCAL:
            return float('inf')  # No limit for local
        return 0
    
    def update_usage(self, backend: TTSBackend, chars_used: int):
        """Update character usage for backend"""
        if backend == TTSBackend.ELEVENLABS:
            self.usage_data["elevenlabs"]["chars_used"] += chars_used
        elif backend == TTSBackend.GOOGLE_TTS:
            self.usage_data["google_tts"]["chars_used"] += chars_used
        self._save_usage()
    
    def choose_best_backend(self, text_length: int) -> TTSBackend:
        """Choose the best available TTS backend based on quota"""
        # Check ElevenLabs (highest quality)
        if self.get_available_chars(TTSBackend.ELEVENLABS) >= text_length:
            return TTSBackend.ELEVENLABS
        
        # Check Google TTS (good quality, higher quota)
        if self.get_available_chars(TTSBackend.GOOGLE_TTS) >= text_length:
            return TTSBackend.GOOGLE_TTS
        
        # Fallback to local Coqui
        return TTSBackend.COQUI_LOCAL

class ElevenLabsTTS:
    """ElevenLabs TTS implementation"""
    
    def __init__(self, api_key: str, voice_id: str = "Adam"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.base_url = "https://api.elevenlabs.io/v1"
    
    def synthesize(self, text: str, output_path: str) -> bool:
        """Synthesize text to audio using ElevenLabs API"""
        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"ElevenLabs TTS: Generated audio for {len(text)} characters")
            return True
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return False

class GoogleTTS:
    """Google Cloud Text-to-Speech implementation"""
    
    def __init__(self, project_id: str, credentials_path: str):
        self.project_id = project_id
        self.credentials_path = credentials_path
        
        # Set up authentication
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        try:
            from google.cloud import texttospeech
            self.client = texttospeech.TextToSpeechClient()
            self.voice = texttospeech.VoiceSelectionParams(
                language_code="en-US", 
                name="en-US-Standard-A"  # Standard voice for free tier
            )
            self.audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
        except ImportError:
            logger.error("Google Cloud TTS: Install with 'pip install google-cloud-texttospeech'")
            self.client = None
    
    def synthesize(self, text: str, output_path: str) -> bool:
        """Synthesize text using Google Cloud TTS"""
        if not self.client:
            return False
            
        try:
            from google.cloud import texttospeech
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )
            
            with open(output_path, "wb") as f:
                f.write(response.audio_content)
            
            logger.info(f"Google TTS: Generated audio for {len(text)} characters")
            return True
            
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return False

class CoquiLocalTTS:
    """Local Coqui TTS server implementation"""
    
    def __init__(self, server_url: str = "http://localhost:5002"):
        self.server_url = server_url
        self.is_available = self._check_server()
    
    def _check_server(self) -> bool:
        """Check if Coqui TTS server is running"""
        try:
            response = requests.get(f"{self.server_url}/api/tts", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def synthesize(self, text: str, output_path: str) -> bool:
        """Synthesize text using local Coqui TTS server"""
        if not self.is_available:
            logger.error("Coqui TTS server not available")
            return False
            
        try:
            data = {
                "text": text,
                "speaker_idx": 0,
                "style_wav": "",
                "language_idx": 0
            }
            
            response = requests.post(
                f"{self.server_url}/api/tts",
                json=data,
                timeout=120
            )
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Coqui TTS: Generated audio for {len(text)} characters")
            return True
            
        except Exception as e:
            logger.error(f"Coqui TTS error: {e}")
            return False

class MarkdownToSpeech:
    """Main class for converting markdown to speech"""
    
    def __init__(self, output_dir: str = "data/voiceovers"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.quota_manager = TTSQuotaManager()
        
        # Initialize TTS backends
        self.backends = {}
        self._init_backends()
    
    def _init_backends(self):
        """Initialize available TTS backends"""
        from dotenv import load_dotenv
        load_dotenv()
        
        # ElevenLabs
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        if elevenlabs_key and not elevenlabs_key.startswith("your-"):
            self.backends[TTSBackend.ELEVENLABS] = ElevenLabsTTS(elevenlabs_key)
            logger.info("✅ ElevenLabs TTS initialized")
        
        # Google TTS
        google_project = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        google_creds = "./credentials/google-cloud-service-account.json"
        if (google_project and os.path.exists(google_creds) and 
            not google_project.startswith("your-")):
            self.backends[TTSBackend.GOOGLE_TTS] = GoogleTTS(google_project, google_creds)
            logger.info("✅ Google Cloud TTS initialized")
        
        # Coqui Local TTS
        coqui_url = os.getenv("COQUI_TTS_URL", "http://localhost:5002")
        coqui_tts = CoquiLocalTTS(coqui_url)
        if coqui_tts.is_available:
            self.backends[TTSBackend.COQUI_LOCAL] = coqui_tts
            logger.info("✅ Coqui Local TTS initialized")
        
        if not self.backends:
            logger.warning("⚠️  No TTS backends available!")
    
    def _extract_text_from_markdown(self, markdown_content: str) -> str:
        """Extract clean text from markdown content"""
        # Remove markdown formatting
        text = re.sub(r'#{1,6}\s+', '', markdown_content)  # Headers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)       # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)           # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)             # Code
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)    # Links
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)        # Images
        text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)  # Lists
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)  # Numbered lists
        
        # Clean up whitespace
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for easier editing"""
        # Simple sentence splitting (can be improved with NLTK)
        sentences = re.split(r'[.!?]+(?:\s|$)', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _create_temp_audio(self, text: str, backend: TTSBackend) -> Optional[str]:
        """Create temporary audio file"""
        temp_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        temp_file = self.output_dir / f"temp_{temp_hash}.mp3"
        
        tts_engine = self.backends.get(backend)
        if not tts_engine:
            return None
        
        success = tts_engine.synthesize(text, str(temp_file))
        if success and temp_file.exists():
            return str(temp_file)
        return None
    
    def generate_voiceover(self, 
                          markdown_file: str,
                          output_name: Optional[str] = None) -> VoiceoverResult:
        """Generate complete voiceover from markdown file"""
        
        try:
            # Read markdown file
            markdown_path = Path(markdown_file)
            if not markdown_path.exists():
                return VoiceoverResult(
                    success=False,
                    full_audio_path="",
                    sentences=[],
                    backend_used=TTSBackend.COQUI_LOCAL,
                    total_duration=0.0,
                    character_count=0,
                    error_message=f"Markdown file not found: {markdown_file}"
                )
            
            with open(markdown_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Extract and clean text
            clean_text = self._extract_text_from_markdown(markdown_content)
            sentences = self._split_into_sentences(clean_text)
            
            if not sentences:
                return VoiceoverResult(
                    success=False,
                    full_audio_path="",
                    sentences=[],
                    backend_used=TTSBackend.COQUI_LOCAL,
                    total_duration=0.0,
                    character_count=0,
                    error_message="No text found in markdown file"
                )
            
            # Choose TTS backend
            total_chars = sum(len(s) for s in sentences)
            selected_backend = self.quota_manager.choose_best_backend(total_chars)
            
            if selected_backend not in self.backends:
                return VoiceoverResult(
                    success=False,
                    full_audio_path="",
                    sentences=[],
                    backend_used=selected_backend,
                    total_duration=0.0,
                    character_count=total_chars,
                    error_message=f"Selected backend {selected_backend.value} not available"
                )
            
            logger.info(f"Using {selected_backend.value} for {total_chars} characters")
            logger.info(f"Processing {len(sentences)} sentences...")
            
            # Generate audio for each sentence
            sentence_audios = []
            combined_audio = AudioSegment.silent(duration=0)
            current_time = 0.0
            
            for i, sentence in enumerate(sentences):
                logger.info(f"Processing sentence {i+1}/{len(sentences)}: {sentence[:50]}...")
                
                # Generate audio for sentence
                temp_audio_path = self._create_temp_audio(sentence, selected_backend)
                if not temp_audio_path:
                    logger.error(f"Failed to generate audio for sentence {i+1}")
                    continue
                
                try:
                    # Load audio segment
                    audio_segment = AudioSegment.from_mp3(temp_audio_path)
                    
                    # Add small pause between sentences
                    if i > 0:
                        pause = AudioSegment.silent(duration=500)  # 500ms pause
                        combined_audio += pause
                        current_time += 0.5
                    
                    # Calculate timing
                    start_time = current_time
                    duration = len(audio_segment) / 1000.0  # Convert to seconds
                    end_time = start_time + duration
                    
                    # Create sentence audio object
                    sentence_audio = SentenceAudio(
                        text=sentence,
                        audio_segment=audio_segment,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        sentence_index=i
                    )
                    sentence_audios.append(sentence_audio)
                    
                    # Add to combined audio
                    combined_audio += audio_segment
                    current_time = end_time
                    
                    # Clean up temp file
                    os.remove(temp_audio_path)
                    
                except Exception as e:
                    logger.error(f"Error processing sentence {i+1}: {e}")
                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                    continue
            
            if not sentence_audios:
                return VoiceoverResult(
                    success=False,
                    full_audio_path="",
                    sentences=[],
                    backend_used=selected_backend,
                    total_duration=0.0,
                    character_count=total_chars,
                    error_message="Failed to generate any sentence audio"
                )
            
            # Save combined audio
            if output_name is None:
                output_name = markdown_path.stem
            
            output_path = self.output_dir / f"{output_name}_voiceover.mp3"
            combined_audio.export(str(output_path), format="mp3")
            
            # Save individual sentence files and update paths
            sentences_dir = self.output_dir / f"{output_name}_sentences"
            sentences_dir.mkdir(exist_ok=True)
            
            for sentence_audio in sentence_audios:
                sentence_filename = f"sentence_{sentence_audio.sentence_index:03d}.mp3"
                sentence_path = sentences_dir / sentence_filename
                sentence_audio.audio_segment.export(str(sentence_path), format="mp3")
                sentence_audio.file_path = str(sentence_path)
            
            # Update quota usage
            self.quota_manager.update_usage(selected_backend, total_chars)
            
            # Create metadata
            metadata = {
                "source_file": str(markdown_path),
                "generated_at": datetime.now().isoformat(),
                "backend_used": selected_backend.value,
                "total_sentences": len(sentence_audios),
                "character_count": total_chars,
                "quota_remaining": {
                    "elevenlabs": self.quota_manager.get_available_chars(TTSBackend.ELEVENLABS),
                    "google_tts": self.quota_manager.get_available_chars(TTSBackend.GOOGLE_TTS)
                }
            }
            
            # Save metadata
            metadata_path = self.output_dir / f"{output_name}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            total_duration = len(combined_audio) / 1000.0
            
            logger.info(f"✅ Voiceover generated successfully!")
            logger.info(f"📁 Output: {output_path}")
            logger.info(f"⏱️  Duration: {total_duration:.1f}s")
            logger.info(f"📝 Sentences: {len(sentence_audios)}")
            
            return VoiceoverResult(
                success=True,
                full_audio_path=str(output_path),
                sentences=sentence_audios,
                backend_used=selected_backend,
                total_duration=total_duration,
                character_count=total_chars,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error generating voiceover: {e}")
            return VoiceoverResult(
                success=False,
                full_audio_path="",
                sentences=[],
                backend_used=TTSBackend.COQUI_LOCAL,
                total_duration=0.0,
                character_count=0,
                error_message=str(e)
            )

def main():
    """Command line interface for voice generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate voiceovers from markdown scripts")
    parser.add_argument("markdown_file", help="Path to markdown script file")
    parser.add_argument("--output", "-o", help="Output name (without extension)")
    parser.add_argument("--backend", choices=["elevenlabs", "google_tts", "coqui_local"], 
                       help="Force specific TTS backend")
    parser.add_argument("--list-quota", action="store_true", 
                       help="Show current TTS quota usage")
    
    args = parser.parse_args()
    
    # Initialize voice generator
    voice_gen = MarkdownToSpeech()
    
    if args.list_quota:
        print("📊 TTS Quota Status:")
        for backend in [TTSBackend.ELEVENLABS, TTSBackend.GOOGLE_TTS]:
            available = voice_gen.quota_manager.get_available_chars(backend)
            if backend == TTSBackend.ELEVENLABS:
                total = 10000
                used = total - available
            else:  # Google TTS
                total = 4_000_000
                used = total - available
            
            print(f"  {backend.value}: {used:,}/{total:,} chars used ({available:,} remaining)")
        return
    
    # Override backend selection if specified
    if args.backend:
        backend_map = {
            "elevenlabs": TTSBackend.ELEVENLABS,
            "google_tts": TTSBackend.GOOGLE_TTS,
            "coqui_local": TTSBackend.COQUI_LOCAL
        }
        # This would require modifying the generate_voiceover method to accept a backend parameter
        logger.info(f"Backend override not yet implemented: {args.backend}")
    
    # Generate voiceover
    result = voice_gen.generate_voiceover(args.markdown_file, args.output)
    
    if result.success:
        print(f"✅ Voiceover generated successfully!")
        print(f"📁 Audio file: {result.full_audio_path}")
        print(f"⏱️  Duration: {result.total_duration:.1f} seconds")
        print(f"📝 Sentences: {len(result.sentences)}")
        print(f"🎤 Backend used: {result.backend_used.value}")
    else:
        print(f"❌ Error: {result.error_message}")
        exit(1)

if __name__ == "__main__":
    main()
