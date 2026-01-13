"""
Main Automation Script
Orchestrates the entire YouTube video creation and upload pipeline
"""

import os
import sys
import yaml
import json
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.content_generator import ContentGenerator
from scripts.text_to_speech import TextToSpeech
from scripts.video_generator import VideoGenerator
from scripts.youtube_uploader import YouTubeUploader


class YouTubePipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config_path: str = 'config.yaml', as_short: bool = False):
        """Initialize the pipeline with configuration
        
        Args:
            config_path: Path to configuration file
            as_short: If True, configure for YouTube Shorts (vertical, ≤60 seconds, faster audio)
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Store shorts mode flag
        self.as_short = as_short
        
        # Modify config for YouTube Shorts if needed
        if as_short:
            print("📱 Configuring for YouTube Shorts format...")
            # YouTube Shorts requirements:
            # - Vertical video (9:16 aspect ratio)
            # - Max 60 seconds duration
            # - Minimum 720x1280, recommended 1080x1920
            self.config['video']['resolution'] = [1080, 1920]  # Vertical 9:16
            self.config['video']['duration'] = min(self.config['video'].get('duration', 60), 60)  # Max 60 seconds
            print(f"   ✅ Resolution: 1080x1920 (vertical)")
            print(f"   ✅ Max duration: {self.config['video']['duration']} seconds")
            print(f"   ✅ Audio speed: 1.25x (faster narration for Shorts)")
        
        # Initialize components
        print("Initializing YouTube Automation Pipeline...")
        
        self.content_gen = ContentGenerator(
            self.config,
            gemini_key=os.getenv('GEMINI_API_KEY')
        )
        
        # Use Edge-TTS with appropriate speed
        # Shorts: 1.25x speed to fit content in under 60 seconds
        # Normal: 1.0x speed for comfortable listening
        audio_speed = 1.25 if as_short else 1.0
        self.tts = TextToSpeech(
            method='edge-tts', 
            speed_factor=audio_speed,
            voice='en-US-AriaNeural'  # Natural female voice, can be changed
        )
        
        self.video_gen = VideoGenerator(self.config)
        
        # YouTube uploader (will be initialized when needed)
        self.uploader = None
        
        # Create output directories
        self.setup_directories()
        
        print("Pipeline initialized successfully!")
    
    def setup_directories(self):
        """Create necessary directories"""
        dirs = ['content', 'output/audio', 'output/videos', 'assets', 'logs']
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    
    def create_video(self, upload: bool = True, custom_topic: str = None, test_mode: bool = False, 
                     as_short: bool = False) -> dict:
        """
        Create a complete video from start to finish
        
        Args:
            upload: Whether to upload to YouTube
            custom_topic: Optional custom topic for the video (must be philosophical)
            test_mode: If True, use hardcoded script instead of calling Gemini API
            as_short: If True, upload as YouTube Short with #Shorts tag
        
        Returns:
            Dictionary with video details
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            print("\n" + "🎬" * 30)
            print("📹 AUTOMATED VIDEO CREATION PIPELINE")
            print("🎬" * 30 + "\n")
            
            # Overall progress tracker
            total_steps = 4 if upload else 3
            with tqdm(total=total_steps, desc="🎯 Pipeline Progress", 
                     bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}') as main_pbar:
                
                # Step 1: Generate content
                main_pbar.set_description("📝 STEP 1/4: Content Generation")
                print("\n" + "="*60)
                print("📝 STEP 1: Generating Content")
                print("="*60)
                
                if test_mode:
                    # Use hardcoded test script
                    topic = custom_topic or "Testing Caption Sync"
                    print(f"  🧪 TEST MODE: Using hardcoded script for {topic}")
                    script_data = {
                        'title': 'The Nature of Existence',
                        'topic': topic,
                        'script': """Have you ever stopped to wonder why we exist?

This question has haunted humanity since the dawn of consciousness.

We wake each morning. We go through our routines. We interact with others.

But beneath it all lies a profound mystery.

The mystery of existence itself.

Why is there something rather than nothing?

This fundamental question reveals the depths of our philosophical inquiry.

Perhaps existence has no inherent purpose.

Or maybe purpose is something we must create ourselves.

The choice is ours to make.""",
                        'description': f'A philosophical exploration of {topic}',
                        'tags': ['philosophy', 'existence', 'meaning', 'consciousness']
                    }
                else:
                    # Use custom topic if provided, otherwise generate one
                    if custom_topic:
                        topic = custom_topic
                        print(f"  🎯 Using custom topic: {topic}")
                    else:
                        topic = self.content_gen.generate_topic()
                        print(f"  💡 Selected topic: {topic}")
                    
                    script_data = self.content_gen.generate_script_with_ai(
                        topic,
                        duration=self.config['video']['duration']
                    )
                
                script_data['timestamp'] = timestamp
                
                print(f"  📄 Title: {script_data['title']}")
                print(f"  📜 Script preview: {script_data['script'][:80]}...")
                
                # Save script
                script_file = self.content_gen.save_content(script_data)
                print(f"  💾 Script saved: {script_file}")
                main_pbar.update(1)
                
                # Step 2: Generate audio
                main_pbar.set_description("🎙️  STEP 2/4: Audio Generation")
                print("\n" + "="*60)
                print("🎙️  STEP 2: Generating Audio (Text-to-Speech at 1.5x)")
                print("="*60)
                audio_path = f"output/audio/{timestamp}.mp3"
                self.tts.generate_audio(script_data['script'], audio_path)
                main_pbar.update(1)
                
                # Step 3: Create video
                main_pbar.set_description("🎬 STEP 3/4: Video Creation")
                print("\n" + "="*60)
                print("🎬 STEP 3: Creating Video")
                print("="*60)
                video_path = f"output/videos/{timestamp}.mp4"
                self.video_gen.create_video(script_data, audio_path, video_path)
                print(f"\n  ✅ Video created: {video_path}")
                main_pbar.update(1)
                
                # Step 4: Upload to YouTube (if requested)
                video_id = None
                if upload:
                    main_pbar.set_description("📤 STEP 4/4: YouTube Upload")
                    print("\n" + "="*60)
                    if as_short:
                        print("📤 STEP 4: Uploading to YouTube as Short")
                    else:
                        print("📤 STEP 4: Uploading to YouTube")
                    print("="*60)
                    
                    if not self.uploader:
                        self.uploader = YouTubeUploader()
                    
                    video_id = self.uploader.upload_from_script(
                        video_path, script_data, self.config, as_short=as_short
                    )
                    
                    if video_id:
                        self.uploader.log_upload(video_id, script_data, 'logs/upload_log.json')
                        print(f"Video uploaded! URL: https://www.youtube.com/watch?v={video_id}")
                    main_pbar.update(1)
                
            
            # Return results
            result = {
                'success': True,
                'timestamp': timestamp,
                'topic': topic,
                'title': script_data['title'],
                'script_file': script_file,
                'audio_path': audio_path,
                'video_path': video_path,
                'video_id': video_id,
                'video_url': f"https://www.youtube.com/watch?v={video_id}" if video_id else None
            }
            
            # Log result
            self.log_result(result)
            
            print("\n" + "🎉" * 30)
            print("✅ VIDEO CREATION COMPLETE!")
            print("🎉" * 30)
            print(f"\n📊 Summary:")
            print(f"  📝 Topic: {topic}")
            print(f"  🎬 Video: {video_path}")
            if video_id:
                print(f"  🔗 URL: https://www.youtube.com/watch?v={video_id}")
            print()
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'timestamp': timestamp,
                'error': str(e)
            }
            self.log_result(error_result)
            print(f"\n❌ Error creating video: {e}")
            import traceback
            traceback.print_exc()
            return error_result
    
    def log_result(self, result: dict):
        """Log pipeline execution result"""
        log_file = 'logs/pipeline_log.json'
        
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        
        logs.append(result)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def run_scheduled(self):
        """Run pipeline on a schedule"""
        schedule_config = self.config['upload']['schedule']
        
        if schedule_config == 'daily':
            schedule.every().day.at("10:00").do(self.create_video)
            print("Scheduled: Daily at 10:00 AM")
        elif schedule_config == 'twice_daily':
            schedule.every().day.at("10:00").do(self.create_video)
            schedule.every().day.at("18:00").do(self.create_video)
            print("Scheduled: Twice daily at 10:00 AM and 6:00 PM")
        elif schedule_config == 'thrice_daily':
            schedule.every().day.at("10:00").do(self.create_video)
            schedule.every().day.at("14:00").do(self.create_video)
            schedule.every().day.at("18:00").do(self.create_video)
            print("Scheduled: Thrice daily at 10:00 AM, 2:00 PM, and 6:00 PM")
        elif schedule_config == 'weekly':
            schedule.every().monday.at("10:00").do(self.create_video)
            print("Scheduled: Weekly on Monday at 10:00 AM")
        
        print("\n📅 Scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\n⏹️  Scheduler stopped.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Automated YouTube Content Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create and upload one video
  python main.py
  
  # Create video without uploading
  python main.py --no-upload
  
  # Create video with custom topic
  python main.py --topic "The meaning of happiness"
  
  # Create a YouTube Short (vertical, 60 sec max)
  python main.py --short
  
  # Create Short without uploading (test locally)
  python main.py --short --no-upload
  
  # Run on schedule (configured in config.yaml)
  python main.py --schedule
  
  # Create multiple videos
  python main.py --count 5
  
  # Create multiple videos with custom topic
  python main.py --count 3 --topic "The nature of time"
        """
    )
    
    parser.add_argument(
        '--no-upload',
        action='store_true',
        help='Create video but do not upload to YouTube'
    )
    
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run on schedule (configured in config.yaml)'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of videos to create'
    )
    
    parser.add_argument(
        '--topic',
        type=str,
        default=None,
        help='Custom philosophical topic for the video (e.g., "The nature of consciousness")'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: Use hardcoded script instead of calling Gemini API (faster for testing captions/video)'
    )
    
    parser.add_argument(
        '--short',
        action='store_true',
        help='Create YouTube Short: vertical 1080x1920 video, max 60 seconds, adds #Shorts to title/description/tags'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline with shorts mode if specified
    pipeline = YouTubePipeline(args.config, as_short=args.short)
    
    # Run based on arguments
    if args.schedule:
        if args.topic:
            print("⚠️  Warning: Custom topic is ignored in scheduled mode")
        if args.test:
            print("⚠️  Warning: Test mode is ignored in scheduled mode")
        pipeline.run_scheduled()
    else:
        if args.test:
            print("\n🧪 TEST MODE ENABLED - Using hardcoded script (no Gemini API calls)\n")
        if args.short:
            print("\n📱 SHORT MODE ENABLED - Video will be uploaded as YouTube Short\n")
        
        for i in range(args.count):
            print(f"\n\n{'='*60}")
            print(f"Creating video {i+1}/{args.count}")
            print('='*60)
            
            result = pipeline.create_video(
                upload=not args.no_upload,
                custom_topic=args.topic,
                test_mode=args.test,
                as_short=args.short
            )
            
            if not result['success']:
                print(f"Failed to create video {i+1}")
                break
            
            # Wait between videos if creating multiple
            if i < args.count - 1:
                print("\nWaiting 10 seconds before next video...")
                time.sleep(10)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      🎥 AUTOMATED YOUTUBE CONTENT PIPELINE 🎥          ║
║                                                          ║
║  Fully automated video creation and upload system       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    main()
