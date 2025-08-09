#!/usr/bin/env python3
"""
🎬 IDEATION & SCRIPT-WRITING AGENT 🎬

This agent:
• Ingests trending JSON data from collectors
• Selects content candidates by views/velocity & gap analysis with existing channel
• Prompts GPT-3.5 for high-energy hook, 8-point narrative, CTA; returns markdown
• Falls back to textgen-webui (Llama-3-8B) if OpenAI credits exhausted
• Saves script, title, description, tags to /data/scripts/{video_id}.md/json
• Unit-tests to enforce ≤ 90 seconds reading time

Features:
- Smart candidate selection based on trending metrics
- Advanced prompt engineering for viral content
- Fallback AI generation system
- Structured output in markdown format
- Reading time validation
- Gap analysis with existing content
"""

import os
import sys
import json
import logging
import asyncio
import aiofiles
import time
import re
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import openai
import httpx
from sqlmodel import SQLModel, Field, create_engine, Session, select
from pydantic import BaseModel
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('script_generator.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
SCRIPTS_DIR = Path("data/scripts")
TRENDING_DIR = Path("data/trending")
MAX_READING_TIME_SECONDS = 90
AVERAGE_READING_SPEED_WPM = 150  # Words per minute
MAX_WORDS_FOR_READING_TIME = (MAX_READING_TIME_SECONDS / 60) * AVERAGE_READING_SPEED_WPM

# Create directories
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
TRENDING_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class TrendingCandidate:
    """Represents a trending video candidate for script generation"""
    video_id: str
    title: str
    channel_title: str
    view_count: int
    published_at: datetime
    category_name: str
    region_code: str
    tags: List[str]
    description: str
    engagement_rate: float
    velocity_score: float
    gap_score: float
    selected_reason: str

@dataclass
class GeneratedScript:
    """Complete generated script package"""
    video_id: str
    title: str
    description: str
    script_content: str
    tags: List[str]
    hook: str
    narrative_points: List[str]
    cta: str
    word_count: int
    reading_time_seconds: float
    viral_score: float
    generated_at: datetime
    ai_model_used: str

class ScriptPromptTemplate:
    """Templates for AI prompts"""
    
    @staticmethod
    def get_gpt_system_prompt() -> str:
        return """You are a viral YouTube script writing expert who creates high-energy, engaging content that maximizes retention and engagement. Your scripts follow proven viral formulas and psychological triggers."""

    @staticmethod
    def get_main_script_prompt(candidate: TrendingCandidate, existing_content_gap: str) -> str:
        return f"""
Create a viral YouTube script based on this trending video analysis:

TRENDING VIDEO DATA:
- Title: {candidate.title}
- Views: {candidate.view_count:,}
- Category: {candidate.category_name}
- Engagement Rate: {candidate.engagement_rate:.2%}
- Channel: {candidate.channel_title}
- Tags: {', '.join(candidate.tags[:10])}
- Description: {candidate.description[:300]}...

CONTENT GAP ANALYSIS:
{existing_content_gap}

SCRIPT REQUIREMENTS:
1. HIGH-ENERGY HOOK (0-15 seconds): Grab attention immediately with curiosity/shock/controversy
2. 8-POINT NARRATIVE STRUCTURE:
   - Point 1: Problem/Pain Point Introduction
   - Point 2: Stakes Elevation (Why this matters NOW)
   - Point 3: Solution Tease (What you're about to learn)
   - Point 4: Authority/Credibility Establishment
   - Point 5: Main Content Delivery (Value-packed)
   - Point 6: Social Proof/Examples
   - Point 7: Urgency/Scarcity Creation
   - Point 8: Call-to-Action & Next Steps
3. STRONG CTA: Subscribe, like, comment with specific instructions
4. Reading time: MAXIMUM 90 seconds (≈225 words)
5. Use psychological triggers: curiosity gaps, social proof, authority, scarcity
6. Include engagement hooks every 15-20 seconds
7. Direct address ("you", "your") throughout

VIRAL OPTIMIZATION:
- Pattern interrupts to maintain attention
- Emotional peaks and valleys
- Cliffhangers before potential drop-offs
- Specific numbers and statistics
- Relatable examples and stories
- Clear value propositions

OUTPUT FORMAT (MARKDOWN):
```markdown
# [VIRAL TITLE HERE]

## Hook (0-15s)
[High-energy opening that immediately grabs attention]

## 8-Point Narrative

### 1. Problem Introduction
[Content here]

### 2. Stakes Elevation
[Content here]

### 3. Solution Tease
[Content here]

### 4. Authority Establishment
[Content here]

### 5. Main Content Delivery
[Content here]

### 6. Social Proof/Examples
[Content here]

### 7. Urgency Creation
[Content here]

### 8. Call-to-Action
[Content here]

## Script Summary
- **Target Keywords:** [list]
- **Psychological Triggers:** [list]
- **Engagement Points:** [list]

## Metadata
- **Description:** [YouTube description with SEO optimization]
- **Tags:** [15 relevant tags]
```

Generate a complete viral script following this structure exactly:
"""

class ScriptGenerator:
    """Main script generation engine"""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 textgen_webui_url: str = "http://localhost:7860",
                 db_path: str = "script_generator.db"):
        
        self.openai_api_key = openai_api_key
        self.textgen_webui_url = textgen_webui_url
        self.db_path = db_path
        
        # Initialize OpenAI if key provided
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_available = True
            logger.info("✅ OpenAI API initialized")
        else:
            self.openai_available = False
            logger.warning("⚠️  OpenAI API key not provided, will use fallback")
        
        # Initialize database
        self.engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(self.engine)
        
        logger.info("🎬 Script Generator initialized")
    
    async def generate_scripts_from_trending(self, 
                                          max_candidates: int = 5,
                                          min_velocity_score: float = 0.7) -> List[GeneratedScript]:
        """Main method: generate scripts from trending data"""
        
        logger.info(f"🚀 Starting script generation from trending data")
        
        # Load and analyze trending data
        trending_data = await self._load_trending_data()
        if not trending_data:
            logger.error("❌ No trending data found")
            return []
        
        # Select top candidates
        candidates = await self._select_candidates(
            trending_data, 
            max_candidates=max_candidates,
            min_velocity_score=min_velocity_score
        )
        
        if not candidates:
            logger.warning("⚠️  No suitable candidates found")
            return []
        
        logger.info(f"📋 Selected {len(candidates)} candidates for script generation")
        
        # Generate scripts for each candidate
        generated_scripts = []
        for candidate in candidates:
            try:
                script = await self._generate_script_for_candidate(candidate)
                if script:
                    # Validate reading time
                    if self._validate_reading_time(script):
                        generated_scripts.append(script)
                        await self._save_script(script)
                        logger.info(f"✅ Generated script for: {script.title[:50]}...")
                    else:
                        logger.warning(f"⚠️  Script rejected - reading time too long: {script.reading_time_seconds:.1f}s")
                
            except Exception as e:
                logger.error(f"❌ Error generating script for {candidate.video_id}: {e}")
                continue
        
        logger.info(f"🎯 Successfully generated {len(generated_scripts)} scripts")
        return generated_scripts
    
    async def _load_trending_data(self) -> List[Dict[str, Any]]:
        """Load latest trending data from JSON files"""
        
        trending_files = list(TRENDING_DIR.glob("*.json"))
        if not trending_files:
            logger.warning("⚠️  No trending data files found")
            return []
        
        # Get the most recent file
        latest_file = max(trending_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"📁 Loading trending data from: {latest_file}")
        
        try:
            async with aiofiles.open(latest_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                
                # Extract videos list
                if 'videos' in data:
                    return data['videos']
                elif isinstance(data, list):
                    return data
                else:
                    logger.error("❌ Unexpected trending data format")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error loading trending data: {e}")
            return []
    
    async def _select_candidates(self, 
                               trending_data: List[Dict[str, Any]], 
                               max_candidates: int = 5,
                               min_velocity_score: float = 0.7) -> List[TrendingCandidate]:
        """Select best candidates based on views/velocity and content gap analysis"""
        
        candidates = []
        
        for video_data in trending_data:
            try:
                # Calculate velocity score (views per hour since publication)
                published_at = datetime.fromisoformat(
                    video_data.get('published_at', '').replace('Z', '+00:00')
                )
                hours_since_publish = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
                views = int(video_data.get('view_count', 0))
                
                if hours_since_publish > 0:
                    velocity_score = min(views / (hours_since_publish * 1000), 1.0)  # Normalized
                else:
                    velocity_score = 0.0
                
                # Skip if velocity too low
                if velocity_score < min_velocity_score:
                    continue
                
                # Calculate content gap score
                gap_score = await self._calculate_content_gap(video_data)
                
                # Create candidate
                candidate = TrendingCandidate(
                    video_id=video_data.get('video_id', ''),
                    title=video_data.get('title', ''),
                    channel_title=video_data.get('channel_title', ''),
                    view_count=views,
                    published_at=published_at,
                    category_name=video_data.get('category_name', ''),
                    region_code=video_data.get('region_code', ''),
                    tags=json.loads(video_data.get('tags', '[]')) if isinstance(video_data.get('tags'), str) else video_data.get('tags', []),
                    description=video_data.get('description', ''),
                    engagement_rate=float(video_data.get('engagement_rate', 0.0)),
                    velocity_score=velocity_score,
                    gap_score=gap_score,
                    selected_reason=f"High velocity ({velocity_score:.2f}), gap opportunity ({gap_score:.2f})"
                )
                
                candidates.append(candidate)
                
            except Exception as e:
                logger.warning(f"⚠️  Error processing candidate {video_data.get('video_id', 'unknown')}: {e}")
                continue
        
        # Sort by combined score (velocity + gap + engagement)
        candidates.sort(
            key=lambda c: (c.velocity_score * 0.4 + c.gap_score * 0.3 + c.engagement_rate * 0.3), 
            reverse=True
        )
        
        # Return top candidates
        return candidates[:max_candidates]
    
    async def _calculate_content_gap(self, video_data: Dict[str, Any]) -> float:
        """Calculate content gap score - higher score means less similar existing content"""
        
        # Simple gap analysis based on title keywords
        # In production, this would compare against existing channel content
        title = video_data.get('title', '').lower()
        keywords = set(re.findall(r'\b\w+\b', title))
        
        # Check against common keywords in existing scripts
        existing_keywords = await self._get_existing_content_keywords()
        
        if not existing_keywords:
            return 1.0  # No existing content, maximum gap
        
        # Calculate uniqueness
        overlap = len(keywords.intersection(existing_keywords))
        total_keywords = len(keywords)
        
        if total_keywords == 0:
            return 0.5  # Default score for empty titles
        
        uniqueness_score = 1.0 - (overlap / total_keywords)
        return max(0.0, min(1.0, uniqueness_score))
    
    async def _get_existing_content_keywords(self) -> set:
        """Get keywords from existing generated content"""
        
        existing_keywords = set()
        
        # Scan existing script files
        script_files = list(SCRIPTS_DIR.glob("*.json"))
        
        for script_file in script_files[-20:]:  # Check last 20 scripts only
            try:
                async with aiofiles.open(script_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    script_data = json.loads(content)
                    
                    title = script_data.get('title', '').lower()
                    keywords = set(re.findall(r'\b\w+\b', title))
                    existing_keywords.update(keywords)
                    
            except Exception as e:
                logger.warning(f"⚠️  Error reading existing script {script_file}: {e}")
                continue
        
        return existing_keywords
    
    async def _generate_script_for_candidate(self, candidate: TrendingCandidate) -> Optional[GeneratedScript]:
        """Generate script for a specific candidate"""
        
        logger.info(f"🎬 Generating script for: {candidate.title[:50]}...")
        
        # Perform content gap analysis
        gap_analysis = await self._perform_gap_analysis(candidate)
        
        # Try OpenAI first, then fallback to textgen-webui
        script_content = None
        model_used = None
        
        if self.openai_available:
            try:
                script_content = await self._generate_with_openai(candidate, gap_analysis)
                model_used = "gpt-3.5-turbo"
                logger.info("✅ Generated script using OpenAI")
            except Exception as e:
                logger.warning(f"⚠️  OpenAI generation failed: {e}")
                self.openai_available = False  # Disable for this session
        
        # Fallback to textgen-webui
        if not script_content:
            try:
                script_content = await self._generate_with_textgen_webui(candidate, gap_analysis)
                model_used = "llama-3-8b"
                logger.info("✅ Generated script using textgen-webui (Llama-3)")
            except Exception as e:
                logger.error(f"❌ Textgen-webui generation failed: {e}")
                return None
        
        if not script_content:
            logger.error("❌ All AI generation methods failed")
            return None
        
        # Parse the generated script
        parsed_script = self._parse_script_content(script_content)
        
        # Calculate metrics
        word_count = len(script_content.split())
        reading_time = (word_count / AVERAGE_READING_SPEED_WPM) * 60  # seconds
        viral_score = self._calculate_viral_score(parsed_script)
        
        # Create script object
        script = GeneratedScript(
            video_id=self._generate_video_id(candidate),
            title=parsed_script.get('title', candidate.title),
            description=parsed_script.get('description', ''),
            script_content=script_content,
            tags=parsed_script.get('tags', []),
            hook=parsed_script.get('hook', ''),
            narrative_points=parsed_script.get('narrative_points', []),
            cta=parsed_script.get('cta', ''),
            word_count=word_count,
            reading_time_seconds=reading_time,
            viral_score=viral_score,
            generated_at=datetime.now(timezone.utc),
            ai_model_used=model_used
        )
        
        return script
    
    async def _perform_gap_analysis(self, candidate: TrendingCandidate) -> str:
        """Perform detailed content gap analysis"""
        
        gap_analysis = f"""
CONTENT GAP ANALYSIS for "{candidate.title}":

1. TRENDING METRICS:
   - Views: {candidate.view_count:,} 
   - Velocity Score: {candidate.velocity_score:.2f}
   - Engagement Rate: {candidate.engagement_rate:.2%}
   - Category: {candidate.category_name}

2. MARKET OPPORTUNITY:
   - Gap Score: {candidate.gap_score:.2f}/1.0
   - Content Uniqueness: {"HIGH" if candidate.gap_score > 0.7 else "MEDIUM" if candidate.gap_score > 0.4 else "LOW"}
   
3. CONTENT STRATEGY RECOMMENDATIONS:
   - {"Focus on unique angle and differentiation" if candidate.gap_score > 0.6 else "Build on trending topic with fresh perspective"}
   - Target keywords: {', '.join(candidate.tags[:5])}
   - Optimal narrative: {"Educational with entertainment" if candidate.category_name in ["Education", "Science & Technology"] else "High-energy entertainment"}

4. PSYCHOLOGICAL TRIGGERS TO EMPHASIZE:
   - Curiosity gap (high-performing in {candidate.category_name})
   - Social proof (leverage {candidate.view_count:,} views metric)
   - Authority positioning
   - Urgency/trending factor
"""
        return gap_analysis
    
    async def _generate_with_openai(self, 
                                  candidate: TrendingCandidate, 
                                  gap_analysis: str) -> str:
        """Generate script using OpenAI GPT-3.5"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": ScriptPromptTemplate.get_gpt_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": ScriptPromptTemplate.get_main_script_prompt(candidate, gap_analysis)
                    }
                ],
                max_tokens=2000,
                temperature=0.8,
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            raise
    
    async def _generate_with_textgen_webui(self, 
                                         candidate: TrendingCandidate, 
                                         gap_analysis: str) -> str:
        """Generate script using textgen-webui (Llama-3-8B) as fallback"""
        
        prompt = f"""<|system|>
{ScriptPromptTemplate.get_gpt_system_prompt()}
<|user|>
{ScriptPromptTemplate.get_main_script_prompt(candidate, gap_analysis)}
<|assistant|>
"""
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.textgen_webui_url}/api/v1/generate",
                    json={
                        "prompt": prompt,
                        "max_new_tokens": 1500,
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "do_sample": True,
                        "stopping_strings": ["<|user|>", "<|system|>"]
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result.get("results", [{}])[0].get("text", "").strip()
                
        except Exception as e:
            logger.error(f"❌ Textgen-webui API error: {e}")
            raise
    
    def _parse_script_content(self, script_content: str) -> Dict[str, Any]:
        """Parse the generated script content to extract structured data"""
        
        parsed = {
            'title': '',
            'description': '',
            'tags': [],
            'hook': '',
            'narrative_points': [],
            'cta': ''
        }
        
        try:
            # Extract title
            title_match = re.search(r'#\s*(.+?)(?:\n|$)', script_content)
            if title_match:
                parsed['title'] = title_match.group(1).strip()
            
            # Extract hook
            hook_match = re.search(r'##\s*Hook.*?\n(.*?)(?=##|\n##|\Z)', script_content, re.DOTALL)
            if hook_match:
                parsed['hook'] = hook_match.group(1).strip()
            
            # Extract narrative points
            narrative_matches = re.findall(r'###\s*\d+\.\s*(.+?)\n(.*?)(?=###|\n###|\Z)', script_content, re.DOTALL)
            for title, content in narrative_matches:
                parsed['narrative_points'].append(f"{title.strip()}: {content.strip()}")
            
            # Extract description
            desc_match = re.search(r'\*\*Description:\*\*\s*(.*?)(?=\n\*\*|\Z)', script_content, re.DOTALL)
            if desc_match:
                parsed['description'] = desc_match.group(1).strip()
            
            # Extract tags
            tags_match = re.search(r'\*\*Tags:\*\*\s*(.*?)(?=\n\*\*|\Z)', script_content, re.DOTALL)
            if tags_match:
                tags_text = tags_match.group(1).strip()
                # Parse tags from various formats
                tags = re.findall(r'[\w\s&-]+', tags_text.replace('#', '').replace(',', ' '))
                parsed['tags'] = [tag.strip() for tag in tags if tag.strip()][:15]
            
            # Extract CTA (usually in the last narrative point or separate section)
            cta_match = re.search(r'###\s*8\.\s*Call-to-Action.*?\n(.*?)(?=###|\n###|\Z)', script_content, re.DOTALL)
            if cta_match:
                parsed['cta'] = cta_match.group(1).strip()
                
        except Exception as e:
            logger.warning(f"⚠️  Error parsing script content: {e}")
        
        return parsed
    
    def _calculate_viral_score(self, parsed_script: Dict[str, Any]) -> float:
        """Calculate viral potential score based on script elements"""
        
        score = 50.0  # Base score
        
        # Title optimization
        title = parsed_script.get('title', '')
        if len(title) >= 40 and len(title) <= 60:
            score += 10
        if re.search(r'\d+', title):  # Contains numbers
            score += 5
        if any(word in title.lower() for word in ['secret', 'amazing', 'shocking', 'ultimate']):
            score += 5
        
        # Hook quality
        hook = parsed_script.get('hook', '')
        if len(hook) > 50:
            score += 10
        if any(trigger in hook.lower() for trigger in ['wait', 'before you', 'stop']):
            score += 5
        
        # Narrative structure
        narrative_points = parsed_script.get('narrative_points', [])
        if len(narrative_points) >= 8:
            score += 10
        
        # CTA presence
        if parsed_script.get('cta', ''):
            score += 5
        
        # Tags optimization
        tags = parsed_script.get('tags', [])
        if len(tags) >= 10:
            score += 5
        
        return min(score, 100.0)
    
    def _generate_video_id(self, candidate: TrendingCandidate) -> str:
        """Generate unique video ID for the script"""
        
        # Create unique ID based on original video ID and timestamp
        timestamp = str(int(time.time()))
        base_string = f"{candidate.video_id}_{timestamp}"
        return hashlib.md5(base_string.encode()).hexdigest()[:12]
    
    def _validate_reading_time(self, script: GeneratedScript) -> bool:
        """Validate that script reading time is within 90 seconds limit"""
        
        return script.reading_time_seconds <= MAX_READING_TIME_SECONDS
    
    async def _save_script(self, script: GeneratedScript) -> None:
        """Save generated script to both markdown and JSON formats"""
        
        try:
            # Save as JSON
            json_file = SCRIPTS_DIR / f"{script.video_id}.json"
            json_data = {
                'video_id': script.video_id,
                'title': script.title,
                'description': script.description,
                'script_content': script.script_content,
                'tags': script.tags,
                'hook': script.hook,
                'narrative_points': script.narrative_points,
                'cta': script.cta,
                'word_count': script.word_count,
                'reading_time_seconds': script.reading_time_seconds,
                'viral_score': script.viral_score,
                'generated_at': script.generated_at.isoformat(),
                'ai_model_used': script.ai_model_used
            }
            
            async with aiofiles.open(json_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(json_data, indent=2, ensure_ascii=False))
            
            # Save as Markdown
            md_file = SCRIPTS_DIR / f"{script.video_id}.md"
            async with aiofiles.open(md_file, 'w', encoding='utf-8') as f:
                await f.write(script.script_content)
            
            logger.info(f"💾 Saved script files: {json_file.name}, {md_file.name}")
            
        except Exception as e:
            logger.error(f"❌ Error saving script files: {e}")
            raise

# Unit test validation
def validate_reading_time(script_content: str) -> Tuple[bool, float]:
    """Unit test function to validate reading time constraint"""
    
    word_count = len(script_content.split())
    reading_time_seconds = (word_count / AVERAGE_READING_SPEED_WPM) * 60
    
    is_valid = reading_time_seconds <= MAX_READING_TIME_SECONDS
    
    return is_valid, reading_time_seconds

def run_reading_time_tests():
    """Run unit tests for reading time validation"""
    
    logger.info("🧪 Running reading time validation tests...")
    
    # Test cases
    test_cases = [
        ("Short script", "This is a short test script with just a few words."),
        ("Medium script", " ".join(["Word"] * 150)),  # ~150 words = ~60 seconds
        ("Long script", " ".join(["Word"] * 300)),     # ~300 words = ~120 seconds (should fail)
    ]
    
    for test_name, test_content in test_cases:
        is_valid, reading_time = validate_reading_time(test_content)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        
        logger.info(f"{status} {test_name}: {reading_time:.1f}s (limit: {MAX_READING_TIME_SECONDS}s)")
    
    logger.info("🧪 Reading time validation tests completed")

async def main():
    """Main execution function for testing and manual runs"""
    
    # Get API keys from environment
    openai_key = os.getenv('OPENAI_API_KEY')
    textgen_url = os.getenv('TEXTGEN_WEBUI_URL', 'http://localhost:7860')
    
    if not openai_key:
        logger.warning("⚠️  OPENAI_API_KEY not found, will use textgen-webui fallback only")
    
    # Initialize generator
    generator = ScriptGenerator(
        openai_api_key=openai_key,
        textgen_webui_url=textgen_url
    )
    
    # Run reading time validation tests
    run_reading_time_tests()
    
    # Generate scripts from trending data
    logger.info("🚀 Starting script generation from trending data...")
    
    scripts = await generator.generate_scripts_from_trending(
        max_candidates=3,
        min_velocity_score=0.5  # Lower threshold for testing
    )
    
    # Print results
    print("\n" + "="*60)
    print("🎬 SCRIPT GENERATION RESULTS")
    print("="*60)
    
    for script in scripts:
        print(f"📄 Title: {script.title}")
        print(f"🎯 Video ID: {script.video_id}")
        print(f"📊 Viral Score: {script.viral_score:.1f}/100")
        print(f"⏱️  Reading Time: {script.reading_time_seconds:.1f}s")
        print(f"📝 Word Count: {script.word_count}")
        print(f"🤖 AI Model: {script.ai_model_used}")
        print(f"🏷️  Tags: {', '.join(script.tags[:5])}...")
        print("-" * 40)
    
    print(f"✅ Generated {len(scripts)} viral scripts successfully!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
