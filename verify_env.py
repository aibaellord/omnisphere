#!/usr/bin/env python3
"""
🔍 OmniSphere Environment Verification Script

This script checks if all required API credentials are properly configured.
Run this after setting up your .env file to verify everything is working.
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

def check_credentials():
    """Check all API credentials and environment variables."""
    
    print("🌌 OmniSphere Environment Verification")
    print("=" * 50)
    
    # Load environment variables
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   Copy .env.template to .env and fill in your API keys")
        return False
    
    load_dotenv()
    
    # Required variables (must have at least these)
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API Key',
        'GOOGLE_CLOUD_PROJECT_ID': 'Google Cloud Project ID',
        'YOUTUBE_API_KEY': 'YouTube Data API Key',
    }
    
    # Fallback LLM options (need at least one)
    fallback_llm_vars = {
        'COHERE_API_KEY': 'Cohere API',
        'HUGGINGFACE_API_KEY': 'HuggingFace API',
        'OLLAMA_BASE_URL': 'Ollama Local API'
    }
    
    # Optional TTS services
    optional_tts_vars = {
        'ELEVENLABS_API_KEY': 'ElevenLabs TTS',
        'GOOGLE_TTS_API_KEY': 'Google Cloud TTS',
        'COQUUI_TTS_ENABLED': 'Coqui TTS (Local)'
    }
    
    # Optional OAuth credentials
    optional_oauth_vars = {
        'YOUTUBE_CLIENT_ID': 'YouTube OAuth Client ID',
        'YOUTUBE_CLIENT_SECRET': 'YouTube OAuth Client Secret',
    }
    
    all_passed = True
    
    # Check required variables
    print("\\n🔑 Required API Credentials:")
    print("-" * 30)
    for var, description in required_vars.items():
        value = os.getenv(var, '')
        if value and not value.startswith('your-') and not value.startswith('sk-your'):
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - Not configured")
            all_passed = False
    
    # Check fallback LLM options
    print("\\n🤖 Fallback LLM APIs (need at least one):")
    print("-" * 40)
    fallback_count = 0
    for var, description in fallback_llm_vars.items():
        value = os.getenv(var, '')
        if value and not value.startswith('your-'):
            if var == 'OLLAMA_BASE_URL':
                print(f"✅ {description} - {value}")
            else:
                print(f"✅ {description}")
            fallback_count += 1
        else:
            print(f"⚠️  {description} - Not configured")
    
    if fallback_count == 0:
        print("❌ No fallback LLM configured! Set up at least one:")
        print("   - Cohere API (recommended)")
        print("   - HuggingFace Inference API") 
        print("   - Ollama (local)")
        all_passed = False
    
    # Check optional TTS services
    print("\\n🎤 Text-to-Speech Services (optional):")
    print("-" * 35)
    tts_count = 0
    for var, description in optional_tts_vars.items():
        value = os.getenv(var, '')
        if value and not value.startswith('your-') and value != 'false':
            print(f"✅ {description}")
            tts_count += 1
        else:
            print(f"⚪ {description} - Not configured")
    
    if tts_count == 0:
        print("ℹ️  No TTS services configured (optional)")
    
    # Check OAuth credentials
    print("\\n🔐 OAuth Credentials (for advanced features):")
    print("-" * 40)
    oauth_count = 0
    for var, description in optional_oauth_vars.items():
        value = os.getenv(var, '')
        if value and not value.startswith('your-'):
            print(f"✅ {description}")
            oauth_count += 1
        else:
            print(f"⚪ {description} - Not configured")
    
    # Check Google Cloud Service Account
    print("\\n☁️  Google Cloud Service Account:")
    print("-" * 30)
    gcs_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './credentials/google-cloud-service-account.json')
    if Path(gcs_path).exists():
        print(f"✅ Service Account JSON - {gcs_path}")
    else:
        print(f"⚠️  Service Account JSON - Not found at {gcs_path}")
        print("   Download from Google Cloud Console and save to credentials/")
    
    # Test basic imports
    print("\\n📦 Python Dependencies:")
    print("-" * 25)
    
    try:
        import dotenv
        print("✅ python-dotenv")
    except ImportError:
        print("❌ python-dotenv - Run: pip install python-dotenv")
        all_passed = False
    
    try:
        import openai
        print("✅ openai (for OpenAI API)")
    except ImportError:
        print("⚠️  openai - Run: pip install openai")
    
    try:
        import google.auth
        print("✅ google-auth (for Google Cloud APIs)")
    except ImportError:
        print("⚠️  google-auth - Run: pip install google-auth google-api-python-client")
    
    # Summary
    print("\\n" + "=" * 50)
    print("📊 SUMMARY:")
    
    if all_passed:
        print("🎉 ✅ All required credentials configured!")
        print("🚀 Your OmniSphere environment is ready!")
        
        if fallback_count > 1:
            print(f"💪 {fallback_count} fallback LLM options configured")
        if tts_count > 0:
            print(f"🎤 {tts_count} TTS service(s) configured")
        if oauth_count > 0:
            print(f"🔐 {oauth_count} OAuth credential(s) configured")
        
        print("\\n🎯 Next steps:")
        print("   1. Test API connections with simple requests")
        print("   2. Run your application")
        print("   3. Monitor API usage and quotas")
        
        return True
    else:
        print("❌ Some required credentials are missing!")
        print("📋 Follow the setup guide: API_CREDENTIALS_GUIDE.md")
        print("🔧 Fix the issues above and run this script again")
        
        return False

def test_api_connections():
    """Test actual API connections (if credentials are available)."""
    print("\\n🧪 Testing API Connections:")
    print("-" * 30)
    
    # Test OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and not openai_key.startswith('your-'):
        try:
            import openai
            openai.api_key = openai_key
            # Simple API test (doesn't use credits)
            models = openai.Model.list()
            print("✅ OpenAI API - Connection successful")
        except Exception as e:
            print(f"❌ OpenAI API - Connection failed: {str(e)[:100]}...")
    else:
        print("⚪ OpenAI API - Key not configured")
    
    # Test Google Cloud (basic auth check)
    try:
        import google.auth
        from google.auth import default
        
        credentials, project = default()
        if project:
            print(f"✅ Google Cloud - Authenticated for project: {project}")
        else:
            print("⚠️  Google Cloud - Authentication found but no project")
    except Exception as e:
        print(f"⚠️  Google Cloud - Authentication issue: {str(e)[:100]}...")
    
    print("\\nℹ️  For full API testing, use individual service test scripts")

if __name__ == "__main__":
    success = check_credentials()
    
    if success:
        if "--test-apis" in sys.argv:
            test_api_connections()
        
        print("\\n" + "🎉" * 20)
        sys.exit(0)
    else:
        print("\\n" + "❌" * 20) 
        sys.exit(1)
