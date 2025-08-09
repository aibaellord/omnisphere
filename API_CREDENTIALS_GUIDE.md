# 🔑 API Credentials Setup Guide for OmniSphere

This guide will walk you through obtaining free API credentials for all required services.

## 🚀 Quick Start Checklist

- [ ] 1. YouTube Data v3 + Analytics v3 (Google Cloud)
- [ ] 2. OpenAI API Key (Required)
- [ ] 3. Fallback LLM APIs (Choose at least one)
- [ ] 4. Optional TTS Services
- [ ] 5. Verify setup with `python -m dotenv run`

---

## 📋 Step 1: Google Cloud Project + YouTube APIs

### Create Google Cloud Project (FREE)

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create New Project**:
   - Click "New Project"
   - Name: "omnisphere-project" (or your choice)
   - Click "Create"
   - Note your PROJECT_ID

### Enable YouTube APIs

3. **Enable APIs**:
   - Go to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3" → Enable
   - Search for "YouTube Analytics API" → Enable

### Create API Key

4. **Create API Key**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the API key
   - **Update .env**: `YOUTUBE_API_KEY=your-api-key-here`

### Create OAuth 2.0 Client

5. **Create OAuth Client**:
   - In "Credentials", click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Configure consent screen if prompted (Internal use for testing)
   - Application type: "Desktop application"
   - Name: "OmniSphere YouTube Client"
   - Download JSON file
   - **Update .env**:
     ```
     YOUTUBE_CLIENT_ID=your-client-id.apps.googleusercontent.com
     YOUTUBE_CLIENT_SECRET=your-client-secret
     ```

### Create Service Account (for Google Cloud APIs)

6. **Create Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Name: "omnisphere-service-account"
   - Create and download JSON key file
   - **Save as**: `./credentials/google-cloud-service-account.json`
   - **Update .env**: `GOOGLE_CLOUD_PROJECT_ID=your-project-id`

---

## 🤖 Step 2: OpenAI API Key (Required)

### Sign Up for OpenAI

1. **Visit OpenAI**: https://platform.openai.com/
2. **Create Account**: Sign up with a new email
3. **Phone Verification**: Add phone number for free credits
4. **Get API Key**:
   - Go to "API Keys" section
   - Click "Create new secret key"
   - Name: "OmniSphere"
   - Copy the key (starts with `sk-`)
   - **Update .env**: `OPENAI_API_KEY=sk-your-api-key-here`

### Find Organization ID (Optional)

5. **Get Org ID** (if you have one):
   - Go to "Settings" > "Organization"
   - Copy Organization ID
   - **Update .env**: `OPENAI_ORG_ID=org-your-org-id`

---

## 🔄 Step 3: Fallback LLM APIs (Choose at least ONE)

### Option A: Cohere API (Recommended)

1. **Visit Cohere**: https://cohere.ai/
2. **Sign Up**: Create free account
3. **Get API Key**:
   - Go to Dashboard > API Keys
   - Copy your API key
   - **Update .env**: `COHERE_API_KEY=your-cohere-api-key`

### Option B: HuggingFace Inference API

1. **Visit HuggingFace**: https://huggingface.co/
2. **Sign Up**: Create account
3. **Create Token**:
   - Go to Settings > Access Tokens
   - Create new token with "Inference API" scope
   - **Update .env**:
     ```
     HUGGINGFACE_API_KEY=hf_your-token-here
     HUGGINGFACE_HUB_TOKEN=hf_your-token-here
     ```

### Option C: Local Ollama (No API Key Needed)

1. **Install Ollama**: https://ollama.ai/
   ```bash
   # macOS
   brew install ollama
   
   # Or download from https://ollama.ai/download
   ```

2. **Start Ollama**:
   ```bash
   ollama serve
   ```

3. **Pull a Model**:
   ```bash
   ollama pull llama2
   # or
   ollama pull codellama
   ```

4. **Environment already set**:
   ```
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2
   ```

---

## 🎤 Step 4: TTS Voice Generation Services

**NEW: Complete voice-over generation system with multiple TTS backends!**  
📖 See [TTS_VOICE_GENERATION_GUIDE.md](TTS_VOICE_GENERATION_GUIDE.md) for full setup guide.

### Option A: ElevenLabs (10k chars/month FREE) - RECOMMENDED

1. **Visit ElevenLabs**: https://elevenlabs.io/
2. **Sign Up**: Create free account
3. **Get API Key**:
   - Go to Profile Settings
   - Copy API key
   - **Update .env**: `ELEVENLABS_API_KEY=your-api-key`
4. **Test Setup**:
   ```bash
   python test_voice_generation.py
   ```

### Option B: Google Cloud TTS (4M chars/month FREE)

1. **Enable TTS API** (in your existing Google Cloud project):
   - Go to APIs & Services > Library
   - Search "Cloud Text-to-Speech API" → Enable

2. **Install dependency**:
   ```bash
   pip install google-cloud-texttospeech
   ```

3. **Your service account JSON already has access**
   - No additional setup needed!

### Option C: Coqui TTS (Local, UNLIMITED)

1. **Install Coqui TTS**:
   ```bash
   pip install TTS
   ```

2. **Start TTS Server**:
   ```bash
   tts-server --model_name tts_models/en/ljspeech/tacotron2-DDC --port 5002
   ```

3. **Optional .env config**:
   ```
   COQUI_TTS_URL=http://localhost:5002
   ```

### Quick Voice Generation Test

```bash
# Generate voiceover from existing script
python generate_voice.py data/scripts/[your-script].md

# Check quota usage
python generate_voice.py --list-quota
```

---

## ✅ Step 5: Verify Setup

### Test Environment Loading

```bash
# Test if .env loads correctly
python -m dotenv run python -c "import os; print('✅ OpenAI:', 'OPENAI_API_KEY' in os.environ)"
```

### Test Individual APIs

```bash
# Test OpenAI
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

# Test OpenAI
try:
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')
    print('✅ OpenAI API key loaded')
except Exception as e:
    print('❌ OpenAI error:', e)
"
```

### Complete Verification Script

Create a test script to verify all credentials:

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = [
    'OPENAI_API_KEY',
    'GOOGLE_CLOUD_PROJECT_ID', 
    'YOUTUBE_API_KEY',
]

fallback_vars = [
    'COHERE_API_KEY',
    'HUGGINGFACE_API_KEY', 
    'OLLAMA_BASE_URL'
]

print('🔍 Checking required variables:')
for var in required_vars:
    status = '✅' if os.getenv(var) and os.getenv(var) != f'your-{var.lower().replace(\"_\", \"-\")}-here' else '❌'
    print(f'{status} {var}')

print('\n🔍 Checking fallback LLM options:')
fallback_count = 0
for var in fallback_vars:
    value = os.getenv(var)
    if value and not value.startswith('your-'):
        fallback_count += 1
        print(f'✅ {var}')
    else:
        print(f'⚠️  {var}')

print(f'\n📊 Summary:')
print(f'✅ Fallback LLMs configured: {fallback_count}/3')
print('✅ Setup complete!' if fallback_count > 0 else '❌ Configure at least one fallback LLM')
"
```

---

## 🛡️ Security Best Practices

1. **Never commit `.env`**: Ensure `.env` is in `.gitignore`
2. **Rotate keys regularly**: Especially for production
3. **Use environment-specific keys**: Different keys for dev/prod
4. **Monitor usage**: Check API usage dashboards regularly
5. **Set billing alerts**: Prevent unexpected charges

---

## 📞 Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'dotenv'"**
```bash
pip install python-dotenv
```

**"API key not found"**
- Check `.env` file exists in project root
- Verify no extra spaces around `=` signs
- Ensure no quotes around values (unless needed)

**"Google Cloud authentication error"**
- Verify service account JSON file exists at specified path
- Check file permissions are readable
- Ensure service account has necessary API permissions

**"YouTube API quota exceeded"**
- YouTube API has daily quotas
- Free tier: 10,000 units per day
- Monitor usage in Google Cloud Console

---

## 📚 API Documentation Links

- **YouTube Data API**: https://developers.google.com/youtube/v3
- **YouTube Analytics API**: https://developers.google.com/youtube/analytics
- **OpenAI API**: https://platform.openai.com/docs/api-reference
- **Cohere API**: https://docs.cohere.com/reference/about
- **HuggingFace**: https://huggingface.co/docs/api-inference/index
- **Ollama**: https://github.com/jmorganca/ollama
- **ElevenLabs**: https://docs.elevenlabs.io/api-reference/getting-started

---

## 🎯 Next Steps

After completing this setup:
1. Test API connections with simple requests
2. Implement error handling for API failures
3. Set up monitoring and logging
4. Configure rate limiting to stay within quotas
5. Plan for production deployment with proper key management

🎉 **Congratulations!** Your OmniSphere project is now ready with all necessary API credentials!
