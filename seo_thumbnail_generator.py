#!/usr/bin/env python3
"""
SEO Metadata & Thumbnail Generator

This module provides functionality to:
1. Use GPT-3.5 to refine video titles (≤70 chars), descriptions (1-2k chars), and generate 15 keyword tags
2. Create professional thumbnails using Pillow with bold text overlays on high-contrast video frames
3. Save thumbnails as 1280x720 JPEG files under 2MB
4. Optional DALL-E integration for enhanced thumbnails

Requirements:
- OpenAI API key for GPT-3.5 and DALL-E
- Pillow for image processing
- OpenCV for video frame extraction
- Video files to extract frames from

Usage:
    python seo_thumbnail_generator.py --video-path path/to/video.mp4 --script-data path/to/script.json
"""

import os
import json
import argparse
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import hashlib
import time

# Core libraries
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
from openai import OpenAI

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SEOThumbnailGenerator:
    """
    Advanced SEO metadata and thumbnail generator with AI-powered optimization.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the generator with OpenAI client.
        
        Args:
            openai_api_key: OpenAI API key. If None, will try to get from environment.
        """
        self.openai_client = None
        
        # Initialize OpenAI client
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        else:
            logger.warning("OpenAI API key not found. GPT-3.5 features will be disabled.")
        
        # Thumbnail specifications
        self.thumbnail_size = (1280, 720)  # YouTube standard
        self.max_file_size = 2 * 1024 * 1024  # 2MB
        self.output_format = "JPEG"
        
        # Font settings for different text sizes
        self.font_configs = {
            'title': {
                'size_range': (48, 96),
                'weight': 'bold',
                'color': '#FFFFFF',
                'stroke_color': '#000000',
                'stroke_width': 3
            },
            'subtitle': {
                'size_range': (24, 48),
                'weight': 'regular',
                'color': '#FFFF00',
                'stroke_color': '#000000',
                'stroke_width': 2
            }
        }
    
    def refine_metadata_with_gpt(self, existing_data: Dict) -> Dict:
        """
        Use GPT-3.5 to refine video metadata including title, description, and tags.
        
        Args:
            existing_data: Dictionary containing existing video metadata
            
        Returns:
            Dictionary with refined metadata
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available. Returning existing metadata.")
            return existing_data
        
        try:
            # Extract key information from existing data
            current_title = existing_data.get('title', 'Video Content')
            current_description = existing_data.get('description', '')
            script_content = existing_data.get('script_content', '')
            hook = existing_data.get('hook', '')
            
            # Create the GPT prompt for metadata refinement
            prompt = f"""
            You are an expert YouTube SEO specialist. Please refine the following video metadata to maximize engagement and searchability:

            CURRENT TITLE: {current_title}
            HOOK: {hook}
            SCRIPT PREVIEW: {script_content[:500]}...
            
            Please provide:
            1. REFINED TITLE (max 70 characters, highly clickable, includes emotional triggers)
            2. OPTIMIZED DESCRIPTION (1000-2000 characters, includes keywords, value proposition, and call-to-action)
            3. 15 STRATEGIC TAGS (mix of broad and specific keywords, trending terms)
            
            Focus on:
            - Emotional triggers and curiosity gaps
            - SEO optimization with relevant keywords  
            - Click-through rate optimization
            - YouTube algorithm signals
            - Clear value proposition
            
            Format your response as JSON:
            {{
                "refined_title": "Your refined title here",
                "optimized_description": "Your detailed description here", 
                "strategic_tags": ["tag1", "tag2", "tag3", ...]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert YouTube SEO and marketing specialist focused on maximizing video performance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                # Find JSON block in response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_text = response_text[start_idx:end_idx]
                    refined_data = json.loads(json_text)
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse GPT response as JSON: {e}")
                # Fallback: try to extract manually
                lines = response_text.split('\n')
                refined_data = {
                    "refined_title": existing_data.get('title', 'Engaging Content'),
                    "optimized_description": existing_data.get('description', 'High-value content.'),
                    "strategic_tags": ["content", "tutorial", "guide", "tips", "strategy"]
                }
            
            # Validate and clean the refined data
            refined_title = refined_data.get('refined_title', existing_data.get('title', ''))[:70]
            optimized_description = refined_data.get('optimized_description', existing_data.get('description', ''))
            strategic_tags = refined_data.get('strategic_tags', [])[:15]  # Limit to 15 tags
            
            # Ensure description is within range (1000-2000 chars)
            if len(optimized_description) < 1000:
                optimized_description += "\n\n🎯 Key Benefits:\n✅ Proven strategies that work\n✅ Step-by-step implementation\n✅ Real-world examples\n✅ Immediate actionable insights\n\n💡 Don't forget to LIKE this video if it helped you and SUBSCRIBE for more valuable content!\n\n#ContentStrategy #Tutorial #Success"
            elif len(optimized_description) > 2000:
                optimized_description = optimized_description[:1997] + "..."
            
            refined_metadata = {
                **existing_data,
                'refined_title': refined_title,
                'optimized_description': optimized_description,
                'strategic_tags': strategic_tags,
                'seo_score': self._calculate_seo_score(refined_title, optimized_description, strategic_tags),
                'refinement_timestamp': time.time()
            }
            
            logger.info(f"Successfully refined metadata with GPT-3.5")
            logger.info(f"Refined title: {refined_title}")
            logger.info(f"Description length: {len(optimized_description)}")
            logger.info(f"Tags count: {len(strategic_tags)}")
            
            return refined_metadata
            
        except Exception as e:
            logger.error(f"Error refining metadata with GPT-3.5: {e}")
            return existing_data
    
    def _calculate_seo_score(self, title: str, description: str, tags: List[str]) -> float:
        """Calculate a basic SEO optimization score."""
        score = 0.0
        
        # Title scoring
        if len(title) <= 70:
            score += 20
        if any(word in title.lower() for word in ['secret', 'ultimate', 'complete', 'guide', 'hack', 'trick']):
            score += 15
        if title[0].isupper():
            score += 5
        
        # Description scoring
        if 1000 <= len(description) <= 2000:
            score += 25
        if 'subscribe' in description.lower() or 'like' in description.lower():
            score += 10
        if description.count('\n') >= 3:  # Good formatting
            score += 5
        
        # Tags scoring
        if len(tags) >= 10:
            score += 20
        if len(tags) == 15:
            score += 10
        
        return min(score, 100.0)
    
    def extract_high_contrast_frame(self, video_path: str, target_frame: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Extract a high-contrast frame from the video for thumbnail background.
        
        Args:
            video_path: Path to the video file
            target_frame: Specific frame number to extract (optional)
            
        Returns:
            Numpy array representing the extracted frame, or None if failed
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Cannot open video file: {video_path}")
                return None
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"Video: {total_frames} frames, {fps:.2f} FPS, {duration:.2f}s duration")
            
            # If no specific frame is requested, sample multiple frames to find highest contrast
            if target_frame is None:
                # Sample frames at different positions
                sample_positions = [0.1, 0.25, 0.4, 0.6, 0.75, 0.9]  # 10%, 25%, 40%, 60%, 75%, 90%
                best_frame = None
                best_contrast = 0
                
                for position in sample_positions:
                    frame_num = int(total_frames * position)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                    ret, frame = cap.read()
                    
                    if ret:
                        # Calculate contrast using standard deviation
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        contrast = gray.std()
                        
                        if contrast > best_contrast:
                            best_contrast = contrast
                            best_frame = frame.copy()
                
                cap.release()
                return best_frame
            else:
                # Extract specific frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    return frame
                else:
                    logger.error(f"Failed to extract frame {target_frame}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error extracting frame from video: {e}")
            return None
    
    def enhance_frame_for_thumbnail(self, frame: Optional[np.ndarray]) -> Image.Image:
        """
        Enhance a video frame to create an optimal thumbnail background.
        
        Args:
            frame: OpenCV frame (numpy array) or None for solid background
            
        Returns:
            PIL Image optimized for thumbnail use
        """
        try:
            # Handle None frame (use solid background)
            if frame is None:
                img = Image.new('RGB', self.thumbnail_size, (30, 40, 60))
            else:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                img = Image.fromarray(frame_rgb)
                
                # Resize to thumbnail dimensions
                img = img.resize(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # Enhance the image for better thumbnail appeal
            # 1. Increase saturation slightly
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.3)  # 30% more saturated
            
            # 2. Increase contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)  # 20% more contrast
            
            # 3. Apply subtle sharpening
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            # 4. Add a subtle dark overlay to make text more readable
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 40))  # Semi-transparent black
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay)
            img = img.convert('RGB')
            
            logger.info("Frame enhanced successfully for thumbnail background")
            return img
            
        except Exception as e:
            logger.error(f"Error enhancing frame: {e}")
            # Return a solid color background as fallback
            return Image.new('RGB', self.thumbnail_size, (20, 20, 40))
    
    def get_font_path(self, weight: str = 'bold') -> Optional[str]:
        """
        Try to find a suitable font file for the thumbnail text.
        
        Args:
            weight: Font weight ('bold', 'regular')
            
        Returns:
            Path to font file or None if not found
        """
        # Common font locations and names
        font_paths = []
        
        if os.name == 'nt':  # Windows
            font_paths = [
                r"C:\Windows\Fonts\arialbd.ttf",  # Arial Bold
                r"C:\Windows\Fonts\arial.ttf",    # Arial Regular
                r"C:\Windows\Fonts\calibrib.ttf", # Calibri Bold
                r"C:\Windows\Fonts\calibri.ttf",  # Calibri Regular
            ]
        else:  # Linux/Mac
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",  # Mac
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/TTF/arial.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
        
        # Return the first available font
        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
        
        logger.warning("No suitable font file found, using default")
        return None
    
    def create_thumbnail_with_text(self, background: Image.Image, title: str, 
                                 subtitle: str = "") -> Image.Image:
        """
        Create a thumbnail by overlaying text on the background image.
        
        Args:
            background: PIL Image to use as background
            title: Main title text
            subtitle: Optional subtitle text
            
        Returns:
            PIL Image with text overlay
        """
        try:
            # Create a copy to work with
            thumbnail = background.copy()
            draw = ImageDraw.Draw(thumbnail)
            
            # Get image dimensions
            width, height = thumbnail.size
            
            # Font settings
            font_path = self.get_font_path('bold')
            
            # Calculate title font size
            title_config = self.font_configs['title']
            title_font_size = self._get_optimal_font_size(
                draw, title, width * 0.9, height * 0.3, 
                title_config['size_range'], font_path
            )
            
            try:
                if font_path:
                    title_font = ImageFont.truetype(font_path, title_font_size)
                else:
                    title_font = ImageFont.load_default()
            except:
                title_font = ImageFont.load_default()
            
            # Position title text
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            # Center horizontally, position in upper third
            title_x = (width - title_width) // 2
            title_y = height // 4
            
            # Draw title with stroke
            self._draw_text_with_stroke(
                draw, (title_x, title_y), title, title_font,
                title_config['color'], title_config['stroke_color'],
                title_config['stroke_width']
            )
            
            # Add subtitle if provided
            if subtitle:
                subtitle_config = self.font_configs['subtitle']
                subtitle_font_size = self._get_optimal_font_size(
                    draw, subtitle, width * 0.8, height * 0.2,
                    subtitle_config['size_range'], font_path
                )
                
                try:
                    if font_path:
                        subtitle_font = ImageFont.truetype(font_path, subtitle_font_size)
                    else:
                        subtitle_font = ImageFont.load_default()
                except:
                    subtitle_font = ImageFont.load_default()
                
                # Position subtitle below title
                subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                
                subtitle_x = (width - subtitle_width) // 2
                subtitle_y = title_y + title_height + 20
                
                self._draw_text_with_stroke(
                    draw, (subtitle_x, subtitle_y), subtitle, subtitle_font,
                    subtitle_config['color'], subtitle_config['stroke_color'],
                    subtitle_config['stroke_width']
                )
            
            # Add decorative elements
            self._add_thumbnail_decorations(draw, width, height)
            
            logger.info("Thumbnail created successfully with text overlay")
            return thumbnail
            
        except Exception as e:
            logger.error(f"Error creating thumbnail with text: {e}")
            return background
    
    def _get_optimal_font_size(self, draw: ImageDraw.Draw, text: str, 
                             max_width: float, max_height: float, 
                             size_range: Tuple[int, int], font_path: Optional[str]) -> int:
        """Find the optimal font size that fits within the given constraints."""
        min_size, max_size = size_range
        
        for size in range(max_size, min_size - 1, -2):
            try:
                if font_path:
                    font = ImageFont.truetype(font_path, size)
                else:
                    font = ImageFont.load_default()
                    
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                if text_width <= max_width and text_height <= max_height:
                    return size
            except:
                continue
        
        return min_size
    
    def _draw_text_with_stroke(self, draw: ImageDraw.Draw, position: Tuple[int, int],
                             text: str, font: ImageFont.ImageFont, 
                             fill_color: str, stroke_color: str, stroke_width: int):
        """Draw text with stroke outline for better readability."""
        x, y = position
        
        # Draw stroke
        for adj_x in range(-stroke_width, stroke_width + 1):
            for adj_y in range(-stroke_width, stroke_width + 1):
                if adj_x != 0 or adj_y != 0:
                    draw.text((x + adj_x, y + adj_y), text, font=font, fill=stroke_color)
        
        # Draw main text
        draw.text(position, text, font=font, fill=fill_color)
    
    def _add_thumbnail_decorations(self, draw: ImageDraw.Draw, width: int, height: int):
        """Add subtle decorative elements to make the thumbnail more appealing."""
        try:
            # Add a subtle gradient overlay at the bottom for better text readability
            for y in range(height - 100, height):
                alpha = int(255 * (height - y) / 100 * 0.3)  # Fade from 30% to 0%
                color = (0, 0, 0, alpha)
                # Note: This requires RGBA mode, but we're working with RGB
                # So we'll skip the gradient for now to keep it simple
                pass
            
            # Add corner accent (optional decorative element)
            accent_size = 30
            accent_color = "#FF6B35"  # Orange accent
            
            # Top-left corner accent
            draw.polygon([
                (0, 0), (accent_size, 0), (0, accent_size)
            ], fill=accent_color)
            
            # Bottom-right corner accent  
            draw.polygon([
                (width - accent_size, height), (width, height), (width, height - accent_size)
            ], fill=accent_color)
            
        except Exception as e:
            logger.warning(f"Error adding decorative elements: {e}")
    
    def generate_dalle_thumbnail(self, metadata: Dict) -> Optional[Image.Image]:
        """
        Generate a thumbnail using DALL-E (optional feature with free credits).
        
        Args:
            metadata: Video metadata for generating relevant imagery
            
        Returns:
            PIL Image generated by DALL-E or None if failed
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available for DALL-E generation")
            return None
        
        try:
            title = metadata.get('refined_title', metadata.get('title', ''))
            description = metadata.get('optimized_description', metadata.get('description', ''))
            
            # Create DALL-E prompt
            prompt = f"""
            Create a high-quality YouTube thumbnail image for a video titled "{title}".
            
            Requirements:
            - 1280x720 aspect ratio
            - Bold, eye-catching design
            - Professional and modern style
            - High contrast colors
            - Space for text overlay
            - Relevant to the video content about: {description[:200]}
            
            Style: Photorealistic, vibrant colors, professional lighting, engaging composition
            """
            
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",  # Closest to our target ratio
                quality="standard",
                n=1,
            )
            
            # Download the generated image
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            
            if image_response.status_code == 200:
                from io import BytesIO
                img = Image.open(BytesIO(image_response.content))
                
                # Resize to target dimensions
                img = img.resize(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                logger.info("DALL-E thumbnail generated successfully")
                return img
            else:
                logger.error(f"Failed to download DALL-E image: {image_response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating DALL-E thumbnail: {e}")
            return None
    
    def save_thumbnail(self, thumbnail: Image.Image, output_path: str) -> bool:
        """
        Save the thumbnail as JPEG with optimization to meet size requirements.
        
        Args:
            thumbnail: PIL Image to save
            output_path: Path where to save the thumbnail
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Start with high quality and reduce if file is too large
            for quality in range(95, 60, -5):
                # Save to memory first to check file size
                from io import BytesIO
                buffer = BytesIO()
                
                thumbnail.save(buffer, format=self.output_format, 
                             quality=quality, optimize=True)
                
                file_size = buffer.tell()
                
                if file_size <= self.max_file_size:
                    # Size is acceptable, save to disk
                    with open(output_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    
                    logger.info(f"Thumbnail saved: {output_path}")
                    logger.info(f"File size: {file_size / 1024:.1f} KB (Quality: {quality})")
                    return True
            
            # If we get here, even lowest quality is too large
            logger.error(f"Cannot save thumbnail under {self.max_file_size / 1024 / 1024:.1f}MB limit")
            return False
            
        except Exception as e:
            logger.error(f"Error saving thumbnail: {e}")
            return False
    
    def generate_complete_package(self, video_path: str, script_data: Dict, 
                                output_dir: str = "generated_thumbnails") -> Dict:
        """
        Generate complete SEO package: refined metadata + optimized thumbnail.
        
        Args:
            video_path: Path to the source video
            script_data: Dictionary containing script/metadata
            output_dir: Directory to save outputs
            
        Returns:
            Dictionary containing all generated assets and metadata
        """
        logger.info(f"Starting complete SEO package generation for: {os.path.basename(video_path)}")
        
        try:
            # Step 1: Refine metadata with GPT-3.5
            logger.info("Step 1: Refining metadata with GPT-3.5...")
            refined_metadata = self.refine_metadata_with_gpt(script_data)
            
            # Step 2: Extract high-contrast frame from video
            logger.info("Step 2: Extracting high-contrast frame...")
            video_frame = self.extract_high_contrast_frame(video_path)
            
            if video_frame is None:
                logger.warning("Could not extract video frame, using solid background")
                background = Image.new('RGB', self.thumbnail_size, (30, 40, 60))
            else:
                background = self.enhance_frame_for_thumbnail(video_frame)
            
            # Step 3: Create thumbnail with text overlay
            logger.info("Step 3: Creating thumbnail with text overlay...")
            title = refined_metadata.get('refined_title', refined_metadata.get('title', 'Video Title'))
            subtitle = "Watch Now!"  # Could be customized
            
            thumbnail = self.create_thumbnail_with_text(background, title, subtitle)
            
            # Step 4: Optional DALL-E enhancement
            dalle_thumbnail = None
            if self.openai_client:
                logger.info("Step 4: Attempting DALL-E thumbnail generation...")
                dalle_thumbnail = self.generate_dalle_thumbnail(refined_metadata)
            
            # Step 5: Save thumbnails and metadata
            logger.info("Step 5: Saving generated assets...")
            
            # Create unique identifier for this generation
            video_id = refined_metadata.get('video_id', hashlib.md5(video_path.encode()).hexdigest()[:12])
            timestamp = int(time.time())
            
            # Prepare output paths
            base_filename = f"thumbnail_{video_id}_{timestamp}"
            thumbnail_path = os.path.join(output_dir, f"{base_filename}.jpg")
            metadata_path = os.path.join(output_dir, f"{base_filename}_metadata.json")
            dalle_path = os.path.join(output_dir, f"{base_filename}_dalle.jpg")
            
            # Save main thumbnail
            thumbnail_success = self.save_thumbnail(thumbnail, thumbnail_path)
            
            # Save DALL-E thumbnail if available
            dalle_success = False
            if dalle_thumbnail:
                dalle_success = self.save_thumbnail(dalle_thumbnail, dalle_path)
            
            # Prepare final package
            package_data = {
                'video_source': video_path,
                'generation_timestamp': timestamp,
                'metadata': refined_metadata,
                'assets': {
                    'primary_thumbnail': {
                        'path': thumbnail_path if thumbnail_success else None,
                        'success': thumbnail_success,
                        'type': 'video_frame_with_text'
                    },
                    'dalle_thumbnail': {
                        'path': dalle_path if dalle_success else None,
                        'success': dalle_success,
                        'type': 'ai_generated'
                    }
                },
                'seo_optimization': {
                    'title_length': len(refined_metadata.get('refined_title', '')),
                    'description_length': len(refined_metadata.get('optimized_description', '')),
                    'tags_count': len(refined_metadata.get('strategic_tags', [])),
                    'seo_score': refined_metadata.get('seo_score', 0)
                }
            }
            
            # Save metadata package
            with open(metadata_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            logger.info("✅ Complete SEO package generated successfully!")
            logger.info(f"📁 Output directory: {output_dir}")
            logger.info(f"🖼️  Primary thumbnail: {'✅' if thumbnail_success else '❌'}")
            logger.info(f"🎨 DALL-E thumbnail: {'✅' if dalle_success else '❌'}")
            logger.info(f"📊 SEO Score: {refined_metadata.get('seo_score', 0)}/100")
            
            return package_data
            
        except Exception as e:
            logger.error(f"Error generating complete SEO package: {e}")
            return {"error": str(e)}

def main():
    """Main CLI interface for the SEO thumbnail generator."""
    parser = argparse.ArgumentParser(description="SEO Metadata & Thumbnail Generator")
    parser.add_argument('--video-path', required=True, help='Path to the source video file')
    parser.add_argument('--script-data', help='Path to JSON file containing script metadata')
    parser.add_argument('--output-dir', default='generated_thumbnails', 
                       help='Directory to save generated assets')
    parser.add_argument('--openai-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--title', help='Override title for thumbnail')
    parser.add_argument('--subtitle', default='', help='Subtitle text for thumbnail')
    parser.add_argument('--frame-number', type=int, help='Specific frame number to extract')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.video_path):
        logger.error(f"Video file not found: {args.video_path}")
        return 1
    
    # Load script data
    script_data = {}
    if args.script_data and os.path.exists(args.script_data):
        with open(args.script_data, 'r') as f:
            script_data = json.load(f)
    else:
        # Create minimal script data
        script_data = {
            'title': args.title or 'Engaging Video Content',
            'description': 'High-quality video content that delivers value.',
            'video_id': hashlib.md5(args.video_path.encode()).hexdigest()[:12]
        }
    
    # Initialize generator
    generator = SEOThumbnailGenerator(openai_api_key=args.openai_key)
    
    # Generate complete package
    result = generator.generate_complete_package(
        video_path=args.video_path,
        script_data=script_data,
        output_dir=args.output_dir
    )
    
    if 'error' in result:
        logger.error(f"Generation failed: {result['error']}")
        return 1
    
    print("\n🎉 SEO Thumbnail Generation Complete!")
    print(f"📁 Check your assets in: {args.output_dir}")
    
    return 0

if __name__ == "__main__":
    exit(main())
