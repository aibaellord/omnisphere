#!/usr/bin/env python3
"""
Quick demo: Generate your first automated video script
"""
import asyncio
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# OpenAI API
import openai

class SimpleDemoGenerator:
    """Simplified script generator for demo purposes"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        # Try to get API key from environment
        self.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("✅ OpenAI API initialized")
        else:
            logger.warning("⚠️ OpenAI API key not found. Using demo mode.")
    
    async def generate_demo_script(self, 
                             topic: str = "The Future of AI Technology",
                             duration: int = 60,
                             style: str = "educational",
                             audience: str = "tech_enthusiasts") -> Dict[str, Any]:
        """Generate a demonstration script"""
        
        logger.info(f"🎬 Generating demo script on topic: {topic}")
        
        if not self.api_key:
            return self._generate_sample_script(topic)
        
        try:
            # Use OpenAI for real script generation
            system_prompt = """You are a viral YouTube script writing expert who creates high-energy, 
            engaging content that maximizes retention and engagement. Your scripts follow proven 
            viral formulas and psychological triggers."""
            
            user_prompt = f"""
            Create a viral YouTube script on this topic: {topic}
            
            SCRIPT REQUIREMENTS:
            1. Duration: {duration} seconds
            2. Style: {style}
            3. Target audience: {audience}
            4. Format: Include a hook, main points, and call-to-action
            5. Tone: High-energy, engaging, direct address
            
            OUTPUT FORMAT (MARKDOWN):
            ```markdown
            # [VIRAL TITLE HERE]
            
            ## Hook (0-15s)
            [High-energy opening that immediately grabs attention]
            
            ## Main Points
            
            ### Point 1
            [Content here]
            
            ### Point 2
            [Content here]
            
            ### Point 3
            [Content here]
            
            ## Call-to-Action
            [Strong CTA here]
            
            ## Metadata
            - **Description:** [YouTube description with SEO optimization]
            - **Tags:** [5-10 relevant tags]
            ```
            
            Generate a complete viral script following this structure exactly:
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            script_content = response.choices[0].message.content
            
            # Extract title from markdown
            title_match = re.search(r'# (.*)', script_content)
            title = title_match.group(1) if title_match else f"The Future of {topic}"
            
            # Extract description
            desc_match = re.search(r'Description:\*\* (.*)', script_content)
            description = desc_match.group(1) if desc_match else f"Learn about {topic} in this engaging video."
            
            # Extract tags
            tags_match = re.search(r'Tags:\*\* (.*)', script_content)
            tags_str = tags_match.group(1) if tags_match else f"{topic}, future, technology, AI"
            tags = [tag.strip() for tag in tags_str.split(',')]
            
            return {
                "title": title,
                "description": description,
                "script": script_content,
                "tags": tags,
                "topic": topic,
                "style": style,
                "audience": audience,
                "generated_at": datetime.now().isoformat(),
                "duration": duration
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating script with OpenAI: {e}")
            return self._generate_sample_script(topic)
    
    def _generate_sample_script(self, topic: str) -> Dict[str, Any]:
        """Generate a sample script when API is not available"""
        
        logger.info("📝 Generating sample script (DEMO MODE)")
        
        return {
            "title": f"The Future of {topic}: What No One is Telling You",
            "description": f"Discover the hidden truths about {topic} that experts don't want you to know. In this video, I reveal groundbreaking insights and predictions that will change how you think about technology forever.",
            "script": f"""# The Future of {topic}: What No One is Telling You

## Hook (0-15s)
What if everything you know about {topic} is about to change forever? In the next 60 seconds, I'll reveal three predictions that experts don't want you to hear.

## Main Points

### Point 1: The Disruption
By 2025, {topic} will make 40% of current jobs completely obsolete. But here's what they're not telling you - this creates an unprecedented opportunity for those who understand what's coming.

### Point 2: The Revolution
The next wave of {topic} won't come from Silicon Valley or big tech. Instead, the real revolution is happening in unexpected places, giving everyday people incredible new powers.

### Point 3: The Opportunity
While everyone else is panicking about these changes, I'll show you exactly how to position yourself to benefit enormously from this shift in the next 12 months.

## Call-to-Action
If you want to stay ahead of these massive changes, hit subscribe now and tap the notification bell. Drop a comment with "FUTURE" and I'll send you my exclusive report on preparing for the {topic} revolution.

## Metadata
- **Description:** The future of {topic} is evolving faster than anyone predicted. In this eye-opening video, I reveal the three major developments that will transform our world in the next 5 years and how you can prepare now to benefit from these changes.
- **Tags:** {topic}, future technology, AI revolution, tech predictions, future trends, emerging tech, technology disruption, future opportunities
""",
            "tags": [f"{topic}", "future technology", "AI revolution", "tech predictions", "future trends"],
            "topic": topic,
            "style": "educational",
            "audience": "tech_enthusiasts",
            "generated_at": datetime.now().isoformat(),
            "duration": 60
        }

async def generate_demo_video():
    """Generate a demo video script"""
    print("🎬 Creating your first automated video script...")
    
    # Get OpenAI API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # Create generator
    generator = SimpleDemoGenerator(api_key)
    
    try:
        # Generate a simple demo script
        topic = "AI-Powered Content Creation"
        script_data = await generator.generate_demo_script(
            topic=topic,
            duration=60,  # 1 minute demo
            style="educational",
            audience="tech_enthusiasts"
        )
        
        print(f"✅ Script generated: {len(script_data.get('script', ''))} characters")
        print(f"📝 Title: {script_data.get('title', 'Demo Video')}")
        
        # Save the script
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"demo_script_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(script_data, f, indent=2)
        
        print(f"💾 Script saved to: {filename}")
        
        # Print preview of the script
        print("\n🎯 SCRIPT PREVIEW:")
        script_lines = script_data.get('script', '').split('\n')
        print('\n'.join(script_lines[:10]) + "\n...")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Review the generated script")
        print("2. Run the complete video pipeline:")
        print("   python3 core/video_automation_pipeline.py")
        print("3. Check the generated_videos/ folder for output")
        
        return script_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔧 Make sure your API keys are set in .env file")
        return None

if __name__ == "__main__":
    import re  # Import here to avoid circular import issues
    asyncio.run(generate_demo_video())
