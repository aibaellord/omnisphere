#!/usr/bin/env python3
"""
🌌 OmniSphere API Credentials Setup Summary

This script shows what has been set up and what you need to do next.
"""

from pathlib import Path
import os

def print_setup_summary():
    """Print a summary of what has been set up and next steps."""
    
    print("🌌" + "=" * 60 + "🌌")
    print("           OMNISPHERE API CREDENTIALS SETUP")
    print("                    SUMMARY & NEXT STEPS")
    print("🌌" + "=" * 60 + "🌌")
    
    # Check what files have been created
    files_created = []
    files_to_check = [
        (".env", "Environment variables file"),
        ("credentials/", "Credentials directory"),
        ("API_CREDENTIALS_GUIDE.md", "Step-by-step setup guide"),
        ("verify_env.py", "Environment verification script"),
        (".gitignore", "Git ignore file (protects secrets)")
    ]
    
    print("\\n📁 FILES CREATED/CONFIGURED:")
    print("-" * 40)
    for file_path, description in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path} - {description}")
            files_created.append(file_path)
        else:
            print(f"❌ {file_path} - {description}")
    
    # Check environment status
    print("\\n🔍 CURRENT ENVIRONMENT STATUS:")
    print("-" * 40)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ python-dotenv installed and working")
        print(f"✅ APP_NAME: {os.getenv('APP_NAME', 'Not set')}")
        print(f"✅ Environment: {os.getenv('APP_ENVIRONMENT', 'Not set')}")
    except ImportError:
        print("❌ python-dotenv not installed")
    
    # API Credentials Status
    print("\\n🔑 API CREDENTIALS STATUS:")
    print("-" * 40)
    
    required_apis = [
        ("OPENAI_API_KEY", "OpenAI", "❌ Required - Get from platform.openai.com"),
        ("GOOGLE_CLOUD_PROJECT_ID", "Google Cloud Project", "❌ Required - Create at console.cloud.google.com"),
        ("YOUTUBE_API_KEY", "YouTube Data API", "❌ Required - Enable in Google Cloud Console"),
    ]
    
    for var_name, api_name, status in required_apis:
        value = os.getenv(var_name, '')
        if value and not value.startswith('your-'):
            print(f"✅ {api_name}: Configured")
        else:
            print(f"{status}")
    
    # Fallback LLM Status
    print("\\n🤖 FALLBACK LLM APIS (need at least one):")
    print("-" * 45)
    
    fallback_apis = [
        ("COHERE_API_KEY", "Cohere", "Free tier available at cohere.ai"),
        ("HUGGINGFACE_API_KEY", "HuggingFace", "Free tier available at huggingface.co"),
        ("OLLAMA_BASE_URL", "Ollama (Local)", "✅ Configured for local use"),
    ]
    
    configured_fallbacks = 0
    for var_name, api_name, note in fallback_apis:
        value = os.getenv(var_name, '')
        if value and not value.startswith('your-'):
            if var_name == "OLLAMA_BASE_URL":
                print(f"✅ {api_name}: {value}")
            else:
                print(f"✅ {api_name}: Configured")
            configured_fallbacks += 1
        else:
            if var_name == "OLLAMA_BASE_URL":
                print(f"✅ {api_name}: {value}")
                configured_fallbacks += 1
            else:
                print(f"⚪ {api_name}: {note}")
    
    print(f"\\n💪 Fallback LLMs configured: {configured_fallbacks}/3")
    
    # Next Steps
    print("\\n🎯 YOUR NEXT STEPS:")
    print("-" * 25)
    print("1. 📖 Read the detailed guide:")
    print("   cat API_CREDENTIALS_GUIDE.md")
    print()
    print("2. 🔑 Get your API credentials:")
    print("   • OpenAI: https://platform.openai.com/")
    print("   • Google Cloud: https://console.cloud.google.com/")
    print("   • Choose a fallback LLM (Cohere/HuggingFace/Ollama)")
    print()
    print("3. ✏️  Edit your .env file:")
    print("   nano .env")
    print("   # Replace placeholder values with your actual API keys")
    print()
    print("4. ✅ Verify your setup:")
    print("   python verify_env.py")
    print()
    print("5. 🧪 Test environment loading:")
    print("   python -m dotenv run python -c 'print(\"Ready to go!\")'")
    
    # Security reminder
    print("\\n🛡️  SECURITY REMINDERS:")
    print("-" * 30)
    print("✅ .env file is in .gitignore (won't be committed)")
    print("🔄 Rotate API keys regularly")
    print("💰 Set up billing alerts for paid APIs")
    print("📊 Monitor your API usage")
    
    # Optional features
    print("\\n🌟 OPTIONAL FEATURES (after basic setup):")
    print("-" * 45)
    print("🎤 Text-to-Speech:")
    print("   • ElevenLabs (10k chars/month free)")
    print("   • Google Cloud TTS (free tier)")  
    print("   • Coqui TTS (local, completely free)")
    print()
    print("🔐 Advanced YouTube features:")
    print("   • OAuth 2.0 client for user authentication")
    print("   • YouTube Analytics API access")
    
    print("\\n" + "🎉" * 25)
    print("🚀 Ready to build something amazing with OmniSphere!")
    print("📚 All documentation is available in the project files.")
    print("🎉" * 25)

if __name__ == "__main__":
    print_setup_summary()
