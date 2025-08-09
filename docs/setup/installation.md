# 🛠️ OmniSphere Installation Guide

## 📋 **Prerequisites**

- **Python 3.8+** (3.10+ recommended)
- **Git** for cloning the repository
- **FFmpeg** for video processing
- **API Keys** for external services (details below)

## 🚀 **Quick Installation**

### **1. Clone Repository**
```bash
git clone https://github.com/your-org/omnisphere.git
cd omnisphere
```

### **2. Set Up Python Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
# Core dependencies
pip install -r requirements.txt

# Optional: Development dependencies
pip install -r requirements-dev.in

# Optional: Dashboard dependencies
pip install -r requirements-dashboard.txt
```

### **4. Install System Dependencies**

#### **macOS:**
```bash
# Install ffmpeg via Homebrew
brew install ffmpeg

# Install system audio tools (for TTS fallback)
# Already included in macOS
```

#### **Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg espeak espeak-data
```

#### **Windows:**
```bash
# Install ffmpeg (download from https://ffmpeg.org/download.html)
# Add to PATH environment variable
```

## 🔑 **API Configuration**

### **Required APIs**
1. **OpenAI API** - Content generation
2. **ElevenLabs API** - Voice synthesis  
3. **YouTube Data API** - Video upload
4. **Upstash Redis** - Task queuing (optional)

### **Setup Environment Variables**
```bash
# Copy template
cp .env.template .env

# Edit with your API keys
nano .env
```

**Required environment variables:**
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs Configuration  
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# YouTube API Configuration
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_REDIRECT_URI=http://localhost:8080

# Optional: Upstash Redis (for production scaling)
UPSTASH_REDIS_URL=your_upstash_redis_url
UPSTASH_REDIS_TOKEN=your_upstash_redis_token
```

For detailed API setup instructions, see [API Credentials Guide](api-credentials.md).

## ✅ **Verify Installation**

### **Run System Verification**
```bash
python verify_env.py
```

This will check:
- ✅ Python version compatibility
- ✅ All required dependencies installed
- ✅ API credentials configured
- ✅ System tools available (ffmpeg, etc.)
- ✅ Database connections working

### **Run Basic Tests**
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests (requires API keys)
pytest tests/integration/
```

## 🎯 **First Run**

### **Initialize System**
```bash
# Interactive setup wizard
python project_manager.py
```

### **Run Demo Workflow**
```bash
# Complete automation demo
python examples/demos/complete_video_workflow_example.py

# Individual component demos
python examples/demos/demo_script_generation.py
python examples/demos/demo_voice_integration.py  
python examples/demos/demo_analytics_dashboard.py
```

## 🐳 **Docker Installation (Alternative)**

### **Using Docker Compose**
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **Using Docker Directly**
```bash
# Build image
docker build -t omnisphere .

# Run container
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -e OPENAI_API_KEY=your_key \
  -e ELEVENLABS_API_KEY=your_key \
  omnisphere
```

## ☁️ **Cloud Deployment**

### **Render.com (Recommended)**
```bash
# Deploy using render.yaml
git push origin main
# Render will auto-deploy from repository
```

### **Replit**
```bash
# Import repository into Replit
# Configure secrets in Replit environment
# Run with: python project_manager.py
```

## 🔧 **Advanced Configuration**

### **Multi-Channel Setup**
```bash
# Create channel configurations
cp channels/tech-focus.yaml channels/your-channel.yaml
nano channels/your-channel.yaml
```

### **Custom Model Configuration**
```bash
# Modify core system settings
nano core/omnisphere_core.py

# Adjust AI parameters
nano components/content_factory/viral_content_generator.py
```

### **Production Scaling**
```bash
# Configure Redis for production
nano core/task_queue_manager.py

# Set up horizontal scaling
nano core/scaling_orchestrator.py
```

## 🛠️ **Troubleshooting**

### **Common Issues**

**1. Python Version Errors**
```bash
# Check Python version
python --version

# Use specific Python version
python3.10 -m venv venv
```

**2. FFmpeg Not Found**
```bash
# Check if ffmpeg is installed
ffmpeg -version

# Add to PATH (Windows)
# Or reinstall via package manager
```

**3. API Key Errors**
```bash
# Verify API keys are set
echo $OPENAI_API_KEY

# Test API connection
python -c "import openai; print(openai.api_key)"
```

**4. Permission Errors**
```bash
# Fix file permissions
chmod +x initialize_empire.sh
chmod +x trending_cli.py
```

### **Getting Help**

- 📖 Check [troubleshooting documentation](../development/troubleshooting.md)
- 🐛 Report issues on [GitHub Issues](https://github.com/your-org/omnisphere/issues)
- 💬 Join our [Discord community](https://discord.gg/omnisphere)
- 📧 Enterprise support: enterprise@omnisphere.ai

## 🎉 **Next Steps**

Once installation is complete:

1. 📚 **Learn the Basics** - Read [Workflow Examples](../examples/workflow-examples.md)
2. 🎬 **Create Your First Video** - Follow [Video Automation Guide](../components/video-automation.md) 
3. 📊 **Set Up Analytics** - Configure [Analytics Dashboard](../components/analytics-dashboard.md)
4. ⚡ **Scale Your System** - Deploy [Multi-Channel Setup](../components/scaling-system.md)

**Welcome to OmniSphere!** 🌌
