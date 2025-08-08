#!/bin/bash

# 🌌 OMNISPHERE EMPIRE INITIALIZATION SCRIPT 🌌
# The Ultimate YouTube Domination System Setup

echo "🌟 OMNISPHERE EMPIRE INITIALIZATION 🌟"
echo "======================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${PURPLE}🌟 $1${NC}"
    echo -e "${PURPLE}$(echo "$1" | sed 's/./=/g')${NC}"
}

# Check Python version
print_header "CHECKING SYSTEM REQUIREMENTS"
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    print_status "Python detected: $python_version"
else
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    print_error "Please run this script from the omnisphere project root"
    exit 1
fi

# Create virtual environment
print_header "SETTING UP VIRTUAL ENVIRONMENT"
if [[ ! -d "omnisphere_env" ]]; then
    print_info "Creating virtual environment..."
    python3 -m venv omnisphere_env
    print_status "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source omnisphere_env/bin/activate
print_status "Virtual environment activated"

# Install requirements
print_header "INSTALLING DEPENDENCIES"
print_info "Installing Python packages... (this may take a few minutes)"

# Update pip first
pip install --upgrade pip

# Install core packages first
pip install fastapi uvicorn pydantic python-multipart

# Install AI/ML packages
pip install openai anthropic transformers torch torchvision tensorflow

# Install remaining packages
pip install -r requirements.txt

print_status "All dependencies installed successfully"

# Create necessary directories
print_header "CREATING PROJECT STRUCTURE"
directories=(
    "logs"
    "data/raw"
    "data/processed"
    "models"
    "configs"
    "scripts"
    "api"
    "web"
    "backups"
)

for dir in "${directories[@]}"; do
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        print_status "Created directory: $dir"
    fi
done

# Create configuration files
print_header "CREATING CONFIGURATION FILES"

# Create .env file
if [[ ! -f ".env" ]]; then
    cat > .env << EOF
# 🌌 OMNISPHERE CONFIGURATION 🌌
# Environment Variables for Ultimate Domination

# Core Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# API Keys (Add your keys here)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here

# Database Settings
DATABASE_URL=postgresql://user:password@localhost:5432/omnisphere
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Empire Settings
MAX_CHANNELS_PER_NICHE=100
CONTENT_GENERATION_RATE=50
VIRAL_THRESHOLD=0.85
DOMINATION_LEVEL=GENESIS

# Platform Settings
YOUTUBE_UPLOAD_LIMIT=100
TIKTOK_UPLOAD_LIMIT=200
INSTAGRAM_UPLOAD_LIMIT=50

EOF
    print_status "Created .env configuration file"
else
    print_info ".env file already exists"
fi

# Create config.yaml
if [[ ! -f "configs/config.yaml" ]]; then
    cat > configs/config.yaml << EOF
# 🌌 OMNISPHERE MASTER CONFIGURATION 🌌
omnisphere:
  version: "1.0.0"
  name: "Ultimate YouTube Empire"
  
core:
  consciousness_level: "GENESIS"
  auto_evolution: true
  quantum_processing: true
  
intelligence_matrix:
  trend_prediction: true
  competitor_analysis: true
  market_analysis: true
  predictive_accuracy_target: 0.95
  
content_factory:
  production_rate: 100  # videos per day
  ai_voices_count: 50
  auto_optimization: true
  viral_engineering: true
  
psychological_engine:
  manipulation_algorithms: 15
  addiction_engineering: true
  viewer_profiling: true
  retention_optimization: true
  
platform_network:
  youtube: true
  tiktok: true
  instagram: true
  twitter: true
  reddit: true
  discord: true
  
revenue_maximizer:
  dynamic_pricing: true
  conversion_optimization: true
  multiple_streams: true
  target_monthly_revenue: 1000000
  
warfare_system:
  competitive_analysis: true
  market_flooding: true
  audience_migration: true
  reputation_management: true

monitoring:
  real_time_analytics: true
  performance_tracking: true
  alert_system: true
  dashboard_updates: 5  # seconds

EOF
    print_status "Created master configuration file"
else
    print_info "Configuration file already exists"
fi

# Create startup script
print_header "CREATING STARTUP SCRIPTS"

cat > start_empire.sh << 'EOF'
#!/bin/bash

# 🚀 OMNISPHERE EMPIRE STARTUP SCRIPT 🚀

echo "🌌 Starting Omnisphere Empire..."
echo "=================================="

# Activate virtual environment
source omnisphere_env/bin/activate

# Start the core system
python core/omnisphere_core.py

EOF

chmod +x start_empire.sh
print_status "Created empire startup script"

# Create monitoring script
cat > monitor_empire.sh << 'EOF'
#!/bin/bash

# 📊 EMPIRE MONITORING SCRIPT 📊

echo "📊 OMNISPHERE EMPIRE MONITORING"
echo "==============================="

while true; do
    clear
    echo "🌟 EMPIRE STATUS - $(date)"
    echo "=========================="
    
    # Check if core system is running
    if pgrep -f "omnisphere_core.py" > /dev/null; then
        echo "✅ Core System: ACTIVE"
    else
        echo "❌ Core System: INACTIVE"
    fi
    
    # Show system resources
    echo "💻 System Resources:"
    echo "   CPU: $(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')"
    echo "   Memory: $(top -l 1 | grep "PhysMem" | awk '{print $2}' | sed 's/M/MB/')"
    
    # Show network status
    echo "🌐 Network Status:"
    if ping -c 1 google.com &> /dev/null; then
        echo "   Internet: CONNECTED"
    else
        echo "   Internet: DISCONNECTED"
    fi
    
    echo "=========================="
    echo "Press Ctrl+C to exit monitoring"
    
    sleep 5
done

EOF

chmod +x monitor_empire.sh
print_status "Created empire monitoring script"

# Final setup steps
print_header "FINAL SETUP STEPS"

# Set permissions
chmod +x initialize_empire.sh
chmod +x core/omnisphere_core.py
print_status "Set execution permissions"

# Create logs directory with initial log file
touch logs/omnisphere.log
print_status "Created log files"

# Success message
print_header "🎉 INITIALIZATION COMPLETE 🎉"
echo ""
print_status "Omnisphere Empire has been successfully initialized!"
echo ""
print_info "Next steps:"
echo "   1. Edit .env file with your API keys"
echo "   2. Run: ./start_empire.sh to begin domination"
echo "   3. Run: ./monitor_empire.sh to monitor progress"
echo ""
print_warning "Remember to configure your API keys before starting!"
echo ""
echo -e "${PURPLE}🌌 WELCOME TO THE FUTURE OF CONTENT DOMINATION 🌌${NC}"
echo ""
