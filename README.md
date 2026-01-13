# 🎥 Story Flux

A fully automated Python system to create and upload YouTube videos with minimal cost. This pipeline handles content generation, text-to-speech, video creation, and YouTube uploads.

## ✨ Features

- **Content Generation**: AI-powered script generation using free Hugging Face models
- **Text-to-Speech**: Convert scripts to speech using free gTTS or pyttsx3
- **Video Creation**: Automated video generation with MoviePy
- **Stock Media**: Optional integration with Pexels API for free stock footage
- **YouTube Upload**: Automated upload with metadata and scheduling
- **Scheduling**: Built-in scheduler for hands-free operation
- **Cost Optimization**: Uses free/low-cost services to minimize expenses

## 💰 Pricing Breakdown

| Component | Service | Cost |
|-----------|---------|------|
| Content Generation | Hugging Face Inference API | **FREE** (rate limited) |
| Text-to-Speech | Google TTS (gTTS) | **FREE** |
| Stock Media | Pexels API | **FREE** (200 requests/hour) |
| Video Processing | MoviePy (local) | **FREE** |
| YouTube API | Google Cloud | **FREE** (10,000 quota/day) |
| **Total** | | **$0/month** ✅ |

*Note: All services used are free tier. You only need a computer to run the scripts.*

## 📋 Prerequisites

- Python 3.8 or higher
- Google Cloud account (free)
- YouTube channel
- Optional: Hugging Face account (free)
- Optional: Pexels API key (free)

## 🚀 Installation

### 1. Clone or Download

```bash
cd /Users/meetrajput/Desktop/projects/youtube_pipeline
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install moviepy pillow opencv-python
pip install gTTS pyttsx3
pip install requests huggingface-hub
pip install python-dotenv schedule pyyaml
```

### 3. Set Up YouTube API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 credentials:
   - Application type: **Desktop app**
   - Download credentials
5. Save as `client_secrets.json` in the project root

### 4. Configure Environment Variables

Copy the example env file:
```bash
cp .env.example .env
```

Edit `.env` and add your keys:
```env
# Required for YouTube uploads
YOUTUBE_CLIENT_SECRETS_FILE=client_secrets.json

# Optional: Better content generation
HUGGINGFACE_TOKEN=your_hf_token_here

# Optional: Free stock videos/images (200 requests/hour)
PEXELS_API_KEY=your_pexels_key_here
```

**Getting API Keys:**
- **Hugging Face**: Sign up at [huggingface.co](https://huggingface.co/) → Settings → Access Tokens
- **Pexels**: Sign up at [pexels.com/api](https://www.pexels.com/api/) (free, instant approval)

### 5. Configure Your Channel

Edit `config.yaml` to customize your content:

```yaml
channel:
  name: "Your Channel Name"
  niche: "tech_facts"  # Choose: tech_facts, life_hacks, fun_facts, motivational, history_facts

video:
  duration: 60  # Video length in seconds
  resolution: [1920, 1080]
  fps: 30

upload:
  schedule: "daily"  # Options: daily, twice_daily, weekly
  privacy_status: "public"  # Options: public, private, unlisted
```

## 📖 Usage

### Create One Video

```bash
python main.py
```

This will:
1. Generate content based on your niche
2. Convert script to speech
3. Create video with visuals
4. Upload to YouTube

### Create Without Uploading

```bash
python main.py --no-upload
```

### Create Multiple Videos

```bash
python main.py --count 5
```

### Run on Schedule

```bash
python main.py --schedule
```

This runs continuously and creates videos based on your `config.yaml` schedule.

### Test Individual Components

```bash
# Test content generation
python scripts/content_generator.py

# Test text-to-speech
python scripts/text_to_speech.py

# Test video generation
python scripts/video_generator.py
```

## 📁 Project Structure

```
youtube_pipeline/
├── main.py                      # Main orchestration script
├── config.yaml                  # Configuration file
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (create this)
├── client_secrets.json          # YouTube OAuth credentials (create this)
│
├── scripts/
│   ├── content_generator.py    # Script generation with AI
│   ├── text_to_speech.py       # Audio generation
│   ├── video_generator.py      # Video creation
│   └── youtube_uploader.py     # YouTube API integration
│
├── content/                     # Generated scripts (JSON)
├── output/
│   ├── audio/                  # Generated audio files
│   └── videos/                 # Generated video files
├── assets/                      # Downloaded stock media (temp)
└── logs/                        # Execution and upload logs
```

## 🎨 Customization

### Change Video Niche

Edit `config.yaml`:
```yaml
channel:
  niche: "life_hacks"  # or: tech_facts, fun_facts, motivational, history_facts
```

### Add Custom Topics

Edit `config.yaml` and add your topics:
```yaml
content:
  topics_pool:
    your_niche:
      - "Topic 1"
      - "Topic 2"
      - "Topic 3"
```

### Change TTS Voice

In `scripts/text_to_speech.py`, modify:
```python
# Use pyttsx3 for offline TTS
tts = TextToSpeech(method='pyttsx3')

# Or use gTTS with different language
tts.generate_audio(text, output_path, language='en-uk')  # UK English
```

### Add Background Music

Place your music file in `assets/` and modify `video_generator.py`:
```python
background_music = AudioFileClip("assets/background.mp3")
background_music = background_music.volumex(0.1)  # Lower volume
video = video.set_audio(CompositeAudioClip([audio, background_music]))
```

## 🔧 Troubleshooting

### "Import errors" when running scripts
Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### "Credentials file not found"
Download OAuth2 credentials from Google Cloud Console and save as `client_secrets.json`

### "Audio generation failed"
If gTTS fails (requires internet), the script automatically falls back to pyttsx3 (offline)

### "Video upload quota exceeded"
YouTube API has daily quotas. Wait 24 hours or optimize by:
- Using `--no-upload` to test
- Reducing upload frequency

### "MoviePy errors"
Install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## 📊 Monitoring

### Check Logs

```bash
# View pipeline execution log
cat logs/pipeline_log.json

# View upload log
cat logs/upload_log.json
```

### View Generated Content

```bash
# List generated scripts
ls content/

# View a script
cat content/script_20260104_120000.json
```

## 🚀 Advanced Usage

### Run as Background Service (Linux/Mac)

Create a systemd service or use screen:
```bash
screen -S youtube_bot
python main.py --schedule
# Press Ctrl+A, then D to detach
```

### Automate with Cron

```bash
# Edit crontab
crontab -e

# Add line to run daily at 10 AM
0 10 * * * cd /path/to/youtube_pipeline && python main.py
```

### Deploy to Cloud

Deploy to free tiers:
- **Google Cloud Run**: Free tier available
- **AWS Lambda**: 1M free requests/month
- **Replit**: Free tier with always-on option
- **PythonAnywhere**: Free tier available

## 🔒 Security Notes

- Keep `client_secrets.json` and `token.pickle` secure
- Add them to `.gitignore` (already included)
- Never commit API keys to version control
- Use `.env` file for sensitive data

## 📝 Best Practices

1. **Start Small**: Test with `--no-upload` first
2. **Monitor Quality**: Review generated videos before full automation
3. **Respect Quotas**: Don't exceed API rate limits
4. **Diversify Content**: Use varied topics to keep audience engaged
5. **Track Performance**: Monitor which topics perform best

## 🔄 Updating

```bash
# Pull latest changes
git pull

# Update dependencies
pip install -r requirements.txt --upgrade
```

## ❓ FAQ

**Q: Is this really free?**  
A: Yes! All services used have generous free tiers that are sufficient for most use cases.

**Q: How many videos can I create per day?**  
A: YouTube API allows ~16 uploads/day with default quotas. Other services have higher limits.

**Q: Can I monetize these videos?**  
A: Follow YouTube's monetization policies. Ensure content is original and adds value.

**Q: What video quality will I get?**  
A: 1080p by default, configurable in `config.yaml`. Quality depends on stock media and TTS.

**Q: Can I use my own voice?**  
A: Yes! Record audio and modify `text_to_speech.py` to use your audio files.

## 🤝 Contributing

Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Share improvements

## 📄 License

This project is open source. Use at your own discretion and follow YouTube's Terms of Service.

## ⚠️ Disclaimer

- Comply with YouTube's Terms of Service
- Respect copyright laws
- Generate original, valuable content
- This tool is for educational purposes
- Monitor your channel's performance and adjust accordingly

## 🎯 Roadmap

- [ ] Thumbnail generation
- [ ] Subtitle generation
- [ ] Advanced video editing
- [ ] Analytics integration
- [ ] Multi-language support
- [ ] Custom voice cloning
- [ ] Shorts optimization

## 📞 Support

Having issues? Check:
1. This README
2. Error messages in logs
3. Individual script documentation
4. API documentation for services used

---

**Happy Automating! 🚀**

Made with ❤️ for content creators who want to scale efficiently.
