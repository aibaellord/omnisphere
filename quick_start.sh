#!/bin/bash

# 🚀 OmniSphere Quick Start Script
# Get your first automated YouTube channel running in minutes!

echo "🌌 OMNISPHERE QUICK START 🌌"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -f "core/omnisphere_core.py" ]; then
    echo "❌ Please run this script from the OmniSphere root directory"
    exit 1
fi

echo "✅ In correct directory: $(pwd)"
echo ""

# Check Python version
echo "🐍 Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is required. Please install Python 3.10+"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install --quiet -r requirements.txt
echo "✅ Dependencies installed"

# Check for .env file
echo "🔑 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.template .env
    echo "✅ .env file created from template"
    echo ""
    echo "🔧 IMPORTANT: Edit the .env file with your API keys:"
    echo "   1. OPENAI_API_KEY=your-key-here"
    echo "   2. YOUTUBE_API_KEY=your-key-here" 
    echo "   3. PEXELS_API_KEY=your-key-here (free)"
    echo ""
    echo "📝 You can edit .env with: nano .env"
    echo ""
    read -p "Press Enter after you've added your API keys..."
else
    echo "✅ .env file exists"
fi

# Quick system health check
echo "🏥 Running system health check..."
python3 -c "
import sys
try:
    import openai
    print('✅ OpenAI library installed')
except ImportError:
    print('⚠️  OpenAI library missing, installing...')
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openai'])
    print('✅ OpenAI library installed')

try:
    from core.omnisphere_core import OmniSphere
    print('✅ Core modules imported successfully')
except Exception as e:
    print(f'⚠️  Core module import issue: {e}')

print('✅ System health check complete')
"

# Create first demo video
echo "🎬 Creating your first demo video..."
cat > first_video_demo.py << 'EOF'
#!/usr/bin/env python3
"""
Quick demo: Generate your first automated video
"""
import asyncio
import os
from datetime import datetime

async def create_first_video():
    print("🎬 Creating your first automated video...")
    
    # Simple script generation
    from generate_script import ScriptGenerator
    
    try:
        generator = ScriptGenerator()
        
        # Generate a simple demo script
        topic = "The Future of AI Technology"
        script_data = await generator.generate_viral_script(
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
        
        import json
        with open(filename, 'w') as f:
            json.dump(script_data, f, indent=2)
        
        print(f"💾 Script saved to: {filename}")
        print("")
        print("🎯 NEXT STEPS:")
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
    asyncio.run(create_first_video())
EOF

chmod +x first_video_demo.py

echo ""
echo "🎯 QUICK START COMPLETE!"
echo "========================"
echo ""
echo "🚀 READY TO CREATE YOUR FIRST VIDEO:"
echo "   python3 first_video_demo.py"
echo ""
echo "📊 VIEW ANALYTICS DASHBOARD:"
echo "   python3 dashboard.py"
echo "   Then visit: http://localhost:8501"
echo ""
echo "🏗️ RUN FULL PROJECT MANAGER:"
echo "   python3 project_manager.py"
echo ""
echo "💡 TIPS:"
echo "   - Start with the demo video first"
echo "   - Check generated_videos/ for outputs"
echo "   - Monitor logs/ for debugging"
echo "   - Use dashboard.py for real-time analytics"
echo ""
echo "🌟 Your automated YouTube empire is ready to launch!"
echo "🔗 GitHub: https://github.com/aibaellord/omnisphere"
echo ""
