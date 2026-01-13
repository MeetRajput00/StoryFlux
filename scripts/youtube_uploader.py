"""
YouTube Upload Module
Handles authentication and uploading videos to YouTube using the YouTube Data API v3
With SEO optimization for maximum impressions
"""

import os
import pickle
import json
from typing import Dict, Optional
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class YouTubeUploader:
    # YouTube API scopes - need both upload and readonly for full functionality
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube.readonly'
    ]
    
    # Video categories
    CATEGORIES = {
        'film_animation': '1',
        'autos_vehicles': '2',
        'music': '10',
        'pets_animals': '15',
        'sports': '17',
        'short_movies': '18',
        'travel_events': '19',
        'gaming': '20',
        'videoblogging': '21',
        'people_blogs': '22',
        'comedy': '23',
        'entertainment': '24',
        'news_politics': '25',
        'howto_style': '26',
        'education': '27',
        'science_technology': '28',
        'nonprofits_activism': '29'
    }
    
    # Optimal upload times for horror content (in hours, 24h format)
    # Based on YouTube analytics - evening/night performs best for horror
    OPTIMAL_HOURS = [20, 21, 22, 23, 0, 1]  # 8 PM - 1 AM
    
    def __init__(self, credentials_file: str = 'client_secrets.json', 
                 token_file: str = 'token.pickle'):
        """
        Initialize YouTube uploader
        
        Args:
            credentials_file: Path to OAuth2 client secrets JSON file
            token_file: Path to save authentication token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.youtube = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with YouTube API"""
        creds = None
        
        # Check if token already exists
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing access token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Please download OAuth2 credentials from Google Cloud Console:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create a project and enable YouTube Data API v3\n"
                        "3. Create OAuth2 credentials (Desktop app)\n"
                        "4. Download and save as 'client_secrets.json'"
                    )
                
                print("\n" + "="*60)
                print("🔐 YouTube Authentication Required")
                print("="*60)
                print("\n📝 Steps:")
                print("1. A browser window will open automatically")
                print("2. Sign in to your Google account")
                print("3. Click 'Allow' to grant permissions")
                print("4. You may see a warning - click 'Advanced' → 'Go to [app name] (unsafe)'")
                print("5. The browser will show 'Authentication successful'")
                print("\nStarting authentication...")
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    # Use run_local_server with a specific port
                    creds = flow.run_local_server(
                        port=8080,
                        prompt='consent',
                        authorization_prompt_message='Please authorize this app by visiting this URL: {url}',
                        success_message='Authentication successful! You can close this window.',
                        open_browser=True
                    )
                    print("\n✅ Authentication successful!")
                except Exception as e:
                    print(f"\n❌ Authentication failed: {e}")
                    print("\n💡 Troubleshooting:")
                    print("1. Make sure your client_secrets.json is correct")
                    print("2. Add http://localhost:8080/ to Authorized redirect URIs in Google Cloud Console")
                    print("3. If browser doesn't open, copy the URL and open it manually")
                    raise
            
            # Save credentials for next time
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.youtube = build('youtube', 'v3', credentials=creds)
        print("✅ Successfully authenticated with YouTube API")
    
    def get_optimal_upload_time(self) -> dict:
        """
        Get optimal upload time for maximum impressions
        Horror content performs best in evening/night hours
        
        Returns:
            dict with optimal time info and recommendation
        """
        now = datetime.now()
        current_hour = now.hour
        
        # Check if current time is optimal
        is_optimal = current_hour in self.OPTIMAL_HOURS
        
        if is_optimal:
            return {
                'is_optimal': True,
                'current_hour': current_hour,
                'message': f"✅ Great time to upload! ({now.strftime('%I:%M %p')}) - Peak horror viewing hours",
                'recommendation': 'Upload now for maximum initial impressions'
            }
        else:
            # Find next optimal hour
            for hour in self.OPTIMAL_HOURS:
                if hour > current_hour:
                    next_optimal = now.replace(hour=hour, minute=0, second=0)
                    break
            else:
                # Next optimal is tomorrow evening
                next_optimal = (now + timedelta(days=1)).replace(hour=20, minute=0, second=0)
            
            hours_until = (next_optimal - now).total_seconds() / 3600
            
            return {
                'is_optimal': False,
                'current_hour': current_hour,
                'next_optimal': next_optimal.strftime('%I:%M %p'),
                'hours_until': round(hours_until, 1),
                'message': f"⏰ Current time ({now.strftime('%I:%M %p')}) is not optimal for horror content",
                'recommendation': f"Best time: 8 PM - 1 AM. Next optimal window: {next_optimal.strftime('%I:%M %p')} ({round(hours_until, 1)} hours)"
            }
    
    def _optimize_tags(self, tags: list) -> list:
        """
        Optimize tags for maximum SEO impact
        
        YouTube tag optimization rules:
        1. Total character limit: 500 characters
        2. Most important tags first (YouTube weights them more)
        3. Mix of broad and specific tags
        4. No duplicates
        5. No special characters that could cause issues
        
        Args:
            tags: List of tag strings
            
        Returns:
            Optimized list of tags
        """
        if not tags:
            return []
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            tag_clean = tag.strip().lower()
            if tag_clean and tag_clean not in seen and len(tag_clean) > 1:
                seen.add(tag_clean)
                # Keep original case for readability
                unique_tags.append(tag.strip())
        
        # Ensure total length under 500 characters
        total_length = 0
        final_tags = []
        for tag in unique_tags:
            if total_length + len(tag) + 1 <= 500:  # +1 for separator
                final_tags.append(tag)
                total_length += len(tag) + 1
            else:
                break
        
        return final_tags

    def upload_video(self, 
                    video_path: str,
                    title: str,
                    description: str,
                    tags: list,
                    category_id: str = '28',
                    privacy_status: str = 'public',
                    made_for_kids: bool = False,
                    thumbnail_path: Optional[str] = None) -> Optional[str]:
        """
        Upload video to YouTube with SEO optimization
        
        Args:
            video_path: Path to video file
            title: Video title (max 100 characters)
            description: Video description (max 5000 characters)
            tags: List of tags (max 500 characters total)
            category_id: YouTube category ID
            privacy_status: 'public', 'private', or 'unlisted'
            made_for_kids: Whether video is made for kids
            thumbnail_path: Optional custom thumbnail
        
        Returns:
            Video ID if successful, None otherwise
        """
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None
        
        # Show upload timing recommendation
        timing = self.get_optimal_upload_time()
        print(f"\n📊 Upload Timing Analysis:")
        print(f"   {timing['message']}")
        print(f"   💡 {timing['recommendation']}\n")
        
        # Prepare video metadata with SEO optimization
        # Ensure tags are properly formatted (no duplicates, proper length)
        clean_tags = self._optimize_tags(tags) if tags else []
        
        body = {
            'snippet': {
                'title': title[:100],  # Max 100 chars
                'description': description[:5000],  # Max 5000 chars
                'tags': clean_tags,
                'categoryId': category_id,
                # Add default language for better SEO
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en'
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': made_for_kids,
                # Enable embedding for more reach
                'embeddable': True,
                # Allow public stats display (social proof)
                'publicStatsViewable': True
            }
        }
        
        # Create media file upload
        media = MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )
        
        try:
            print(f"Uploading video: {title}")
            
            # Execute upload
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"Upload progress: {progress}%")
            
            video_id = response['id']
            print(f"\n✅ Video uploaded successfully!")
            print(f"📺 Video ID: {video_id}")
            print(f"🔗 Video URL: https://www.youtube.com/watch?v={video_id}")
            
            # Show SEO tips for maximum impressions
            self._show_impression_tips(video_id)
            
            # Upload thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                self.set_thumbnail(video_id, thumbnail_path)
            
            return video_id
            
        except HttpError as e:
            error_content = e.content.decode('utf-8') if isinstance(e.content, bytes) else str(e.content)
            
            # Check for specific error types
            if e.resp.status == 400 and 'uploadLimitExceeded' in error_content:
                print("\n" + "="*70)
                print("⚠️  YOUTUBE UPLOAD LIMIT REACHED")
                print("="*70)
                print("\n📊 What this means:")
                print("  • YouTube has daily upload limits to prevent spam")
                print("  • Default limit: 6 uploads per day (for new/unverified channels)")
                print("  • Verified channels: 100+ uploads per day")
                print("\n🔧 Solutions:")
                print("  1. Wait 24 hours for quota to reset")
                print("  2. Verify your YouTube channel:")
                print("     → Go to: https://www.youtube.com/verify")
                print("     → Verify with phone number")
                print("     → Increases limit from 6 to 100+ uploads/day")
                print("  3. Request quota increase (for API project):")
                print("     → Go to: https://console.cloud.google.com/")
                print("     → APIs & Services → YouTube Data API v3 → Quotas")
                print("     → Request quota increase")
                print("\n💡 Workaround for now:")
                print("  • Use --no-upload flag to create videos without uploading")
                print("  • Videos are saved locally in: output/videos/")
                print("  • Upload manually later through YouTube Studio")
                print("\n📝 Example:")
                print("  python3 main.py --topic 'Your topic' --no-upload")
                print("="*70)
                print(f"\n✅ Your video is saved locally: {video_path}")
                print("   Upload it manually when quota resets!\n")
                
            elif e.resp.status == 403:
                print("\n" + "="*70)
                print("⚠️  PERMISSION ERROR")
                print("="*70)
                print("\n📊 Possible causes:")
                print("  • API quota exceeded (10,000 units/day for free tier)")
                print("  • YouTube Data API not enabled")
                print("  • Incorrect OAuth scopes")
                print("\n🔧 Solutions:")
                print("  1. Check quota: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas")
                print("  2. Enable YouTube Data API v3 in your project")
                print("  3. Re-authenticate: delete token.pickle and run again")
                print("="*70 + "\n")
                
            else:
                print(f"\n❌ An HTTP error {e.resp.status} occurred:")
                print(f"{error_content}\n")
            
            return None
            
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _show_impression_tips(self, video_id: str):
        """Show tips to maximize impressions after upload"""
        print("\n" + "="*60)
        print("📈 TIPS TO MAXIMIZE IMPRESSIONS:")
        print("="*60)
        print("""
🔥 FIRST 24 HOURS ARE CRITICAL:
   • Share on social media immediately
   • Reply to ALL comments within first hour
   • Pin a comment asking viewers to like & subscribe

📱 SHARE YOUR VIDEO:
   • Reddit (r/creepypasta, r/nosleep, r/horror)
   • Twitter/X with relevant hashtags
   • Discord horror communities
   • TikTok (repost snippet with link)

🎯 ENGAGEMENT HACKS:
   • Ask a question in the first comment
   • Use end screens (add in YouTube Studio)
   • Add cards linking to other videos
   • Create a playlist and add this video

📊 MONITOR & OPTIMIZE:
   • Check YouTube Studio analytics after 48 hours
   • Look at CTR (aim for >4%)
   • Check audience retention (aim for >50%)
   • Adjust future titles based on performance
""")
        print(f"🔗 Edit in YouTube Studio: https://studio.youtube.com/video/{video_id}/edit")
        print("="*60 + "\n")

    def set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Set custom thumbnail for video
        
        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print(f"Thumbnail uploaded for video {video_id}")
            return True
        except HttpError as e:
            print(f"Failed to upload thumbnail: {e}")
            return False
    
    def upload_from_script(self, video_path: str, script_data: Dict, 
                          config: Dict, as_short: bool = False) -> Optional[str]:
        """
        Upload video using script data and config
        
        Args:
            video_path: Path to video file
            script_data: Dictionary with title, description, tags
            config: Configuration dictionary
            as_short: If True, upload as YouTube Short with #Shorts tag
        
        Returns:
            Video ID if successful
        """
        upload_config = config.get('upload', {})
        
        # Get tags and add #Shorts if uploading as short
        tags = script_data.get('tags', []).copy()
        title = script_data.get('title', 'Automated Video')
        description = script_data.get('description', '')
        
        if as_short:
            print("  📱 Formatting for YouTube Shorts...")
            
            # Add #Shorts to title (YouTube strongly recommends this)
            if '#Shorts' not in title and '#shorts' not in title.lower():
                # Add to end of title if it fits, otherwise truncate
                shorts_suffix = " #Shorts"
                if len(title) + len(shorts_suffix) <= 100:
                    title = f"{title}{shorts_suffix}"
                else:
                    title = f"{title[:100-len(shorts_suffix)]}{shorts_suffix}"
            
            # Add #Shorts tag if not already present
            shorts_tags = ['#Shorts', 'shorts', 'short', 'youtubeshorts', 'youtube shorts']
            has_shorts_tag = any(tag.lower().replace('#', '') in ['shorts', 'short', 'youtubeshorts'] for tag in tags)
            if not has_shorts_tag:
                tags.insert(0, '#Shorts')  # Add at beginning for priority
                tags.insert(1, 'shorts')
                tags.insert(2, 'youtube shorts')
            
            # Add #Shorts to description at the very beginning (YouTube looks here too)
            if '#Shorts' not in description and '#shorts' not in description.lower():
                description = f"#Shorts\n\n{description}"
            
            print(f"    ✅ Title: {title}")
            print(f"    ✅ Tags: {tags[:5]}...")
        
        return self.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            category_id=upload_config.get('category_id', '28'),
            privacy_status=upload_config.get('privacy_status', 'public'),
            made_for_kids=upload_config.get('made_for_kids', False)
        )
    
    def get_channel_info(self) -> Optional[Dict]:
        """Get information about the authenticated channel"""
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics',
                mine=True
            )
            response = request.execute()
            
            if response['items']:
                channel = response['items'][0]
                return {
                    'title': channel['snippet']['title'],
                    'subscribers': channel['statistics'].get('subscriberCount', '0'),
                    'views': channel['statistics'].get('viewCount', '0'),
                    'videos': channel['statistics'].get('videoCount', '0')
                }
            return None
        except HttpError as e:
            print(f"Error getting channel info: {e}")
            return None
    
    def log_upload(self, video_id: str, script_data: Dict, log_file: str = 'upload_log.json'):
        """Log upload details for tracking"""
        log_entry = {
            'video_id': video_id,
            'upload_time': datetime.now().isoformat(),
            'title': script_data.get('title'),
            'topic': script_data.get('topic'),
            'tags': script_data.get('tags'),
            'url': f"https://www.youtube.com/watch?v={video_id}"
        }
        
        # Load existing log
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        
        # Append new entry
        logs.append(log_entry)
        
        # Save log
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        print(f"Upload logged to {log_file}")


if __name__ == "__main__":
    # Test YouTube uploader setup
    print("YouTube Uploader Module")
    print("=" * 50)
    print("\nTo use this module, you need:")
    print("1. Google Cloud Project with YouTube Data API v3 enabled")
    print("2. OAuth2 credentials (client_secrets.json)")
    print("\nSetup instructions:")
    print("1. Visit https://console.cloud.google.com/")
    print("2. Create a new project")
    print("3. Enable YouTube Data API v3")
    print("4. Create OAuth2 credentials (Desktop app)")
    print("5. Download credentials as 'client_secrets.json'")
    print("6. Place the file in the project root directory")
    print("\nOnce setup, authentication will happen automatically on first run.")
