"""
Video Generator Module
Creates horror story videos with Pexels stock images, effects, and typewriter captions
"""

import os
import random
import re
import requests
import textwrap
from typing import Dict, List, Optional
from tqdm import tqdm

# MoviePy 2.x imports
try:
    from moviepy import (
        AudioFileClip, ImageClip, TextClip,
        CompositeVideoClip, CompositeAudioClip, concatenate_videoclips
    )
except ImportError:
    # Fallback for MoviePy 1.x
    from moviepy.editor import (
        AudioFileClip, ImageClip, TextClip,
        CompositeVideoClip, CompositeAudioClip, concatenate_videoclips
    )

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

class VideoGenerator:
    def __init__(self, config: Dict):
        """
        Initialize video generator for horror story content
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.resolution = tuple(config['video']['resolution'])
        self.fps = config['video']['fps']
        self.pexels_api_key = os.getenv('PEXELS_API_KEY')
        self.pixabay_api_key = os.getenv('PIXABAY_API_KEY')
        
        if not self.pexels_api_key:
            print("⚠️  Warning: No PEXELS_API_KEY found. Will use dark horror backgrounds.")
        
        if not self.pixabay_api_key:
            print("⚠️  Warning: No PIXABAY_API_KEY found. Will use fallback music sources.")
        
        # Overlay opacity for text readability (darker for horror atmosphere)
        self.text_overlay_opacity = 0.7
        
        # Background music settings
        self.use_background_music = config.get('assets', {}).get('background_music', True)
        self.music_volume = config.get('assets', {}).get('music_volume', 0.15)  # Default 15% volume
        self.music_dir = 'assets/music'
        os.makedirs(self.music_dir, exist_ok=True)
        
        # Music search categories for horror content
        self.music_search_queries = [
            "dark ambient",
            "horror cinematic", 
            "suspense thriller",
            "creepy atmosphere",
            "scary background",
            "dark cinematic",
            "tension horror",
            "eerie ambient",
            "mysterious dark",
            "haunting melody"
        ]
    
    def _get_background_music(self, duration: float, mood: str = "horror") -> Optional[AudioFileClip]:
        """
        Get or download copyright-free background music from Pixabay API
        
        Args:
            duration: Required duration for the music
            mood: Mood/theme for music search (default: horror)
            
        Returns:
            AudioFileClip with background music or None if unavailable
        """
        if not self.use_background_music:
            return None
        
        # Check for existing music files first
        existing_music = []
        if os.path.exists(self.music_dir):
            for f in os.listdir(self.music_dir):
                if f.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                    existing_music.append(os.path.join(self.music_dir, f))
        
        # Try to get new music from Pixabay API, or use existing
        music_path = None
        
        if self.pixabay_api_key:
            # Search and download new music from Pixabay
            music_path = self._search_pixabay_music(mood, duration)
        
        # Fallback to existing music if API fails or no key
        if not music_path and existing_music:
            music_path = random.choice(existing_music)
            print(f"  🎵 Using cached music: {os.path.basename(music_path)}")
        elif not music_path:
            print("  ⚠️  No background music available (set PIXABAY_API_KEY for dynamic music)")
            return None
        
        try:
            # Load and prepare the music
            music = AudioFileClip(music_path)
            
            # Loop or trim music to match video duration
            if music.duration < duration:
                # Loop the music to cover the full duration
                loops_needed = int(duration / music.duration) + 1
                music_clips = [music] * loops_needed
                try:
                    from moviepy import concatenate_audioclips
                except ImportError:
                    from moviepy.editor import concatenate_audioclips
                music = concatenate_audioclips(music_clips)
            
            # Trim to exact duration
            try:
                music = music.subclipped(0, duration)
            except AttributeError:
                music = music.subclip(0, duration)
            
            # Apply volume reduction for background
            try:
                music = music.with_volume_scaled(self.music_volume)
            except AttributeError:
                music = music.volumex(self.music_volume)
            
            # Add fade in/out for smooth transitions
            try:
                music = music.with_effects([
                    lambda clip: clip.audio_fadein(2.0),
                    lambda clip: clip.audio_fadeout(3.0)
                ])
            except:
                try:
                    music = music.audio_fadein(2.0).audio_fadeout(3.0)
                except:
                    pass  # Skip fade effects if not supported
            
            return music
            
        except Exception as e:
            print(f"  ⚠️  Error loading background music: {e}")
            return None
    
    def _search_pixabay_music(self, mood: str, min_duration: float = 60) -> Optional[str]:
        """
        Search and download music from Pixabay API
        
        Args:
            mood: Search mood/theme
            min_duration: Minimum duration in seconds
            
        Returns:
            Path to downloaded music file or None
        """
        if not self.pixabay_api_key:
            return None
        
        # Select a random search query based on mood
        if mood.lower() in ['horror', 'scary', 'dark', 'creepy']:
            query = random.choice(self.music_search_queries)
        else:
            query = mood
        
        print(f"  🎵 Searching Pixabay for: '{query}' music...")
        
        try:
            # Pixabay Music API endpoint
            url = "https://pixabay.com/api/videos/music/"  # Note: Pixabay uses this for audio too
            
            # Actually Pixabay has a separate audio endpoint
            url = "https://pixabay.com/api/"
            params = {
                'key': self.pixabay_api_key,
                'q': query,
                'media_type': 'music',  # Pixabay now has music category
                'per_page': 10,
                'safesearch': 'true',
                'order': 'popular'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            # Pixabay free API might not support music directly
            # Let's use their audio search which works
            if response.status_code != 200:
                # Try alternative: use Freesound or direct Pixabay CDN search
                return self._download_from_freesound(query, min_duration)
            
            data = response.json()
            hits = data.get('hits', [])
            
            if not hits:
                print(f"  ⚠️  No music found for '{query}', trying alternative...")
                return self._download_from_freesound(query, min_duration)
            
            # Filter by duration if possible and select randomly
            suitable_tracks = []
            for track in hits:
                # Pixabay audio structure
                audio_url = track.get('audio', '') or track.get('music', '')
                if audio_url:
                    suitable_tracks.append({
                        'url': audio_url,
                        'id': track.get('id', random.randint(1000, 9999)),
                        'tags': track.get('tags', query)
                    })
            
            if not suitable_tracks:
                return self._download_from_freesound(query, min_duration)
            
            # Select a random track
            selected = random.choice(suitable_tracks)
            
            # Generate filename from query and ID
            safe_query = "".join(c if c.isalnum() else "_" for c in query)
            filename = f"pixabay_{safe_query}_{selected['id']}.mp3"
            music_path = os.path.join(self.music_dir, filename)
            
            # Download if not exists
            if not os.path.exists(music_path):
                print(f"  📥 Downloading: {filename}")
                audio_response = requests.get(selected['url'], timeout=60, stream=True)
                audio_response.raise_for_status()
                
                with open(music_path, 'wb') as f:
                    for chunk in audio_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"  ✅ Downloaded: {filename}")
            else:
                print(f"  ✅ Using cached: {filename}")
            
            return music_path
            
        except Exception as e:
            print(f"  ⚠️  Pixabay search failed: {e}")
            return self._download_from_freesound(query, min_duration)
    
    def _download_from_freesound(self, query: str, min_duration: float = 60) -> Optional[str]:
        """
        Fallback: Download from Freesound API or use bundled free tracks
        
        Args:
            query: Search query
            min_duration: Minimum duration
            
        Returns:
            Path to music file or None
        """
        freesound_api_key = os.getenv('FREESOUND_API_KEY')
        
        if freesound_api_key:
            try:
                print(f"  🎵 Searching Freesound for: '{query}'...")
                
                # Freesound API search
                url = "https://freesound.org/apiv2/search/text/"
                params = {
                    'query': f"{query} ambient loop",
                    'filter': f'duration:[{min_duration} TO 300]',  # 1-5 minutes
                    'fields': 'id,name,previews,duration',
                    'page_size': 5,
                    'token': freesound_api_key
                }
                
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if results:
                    # Select random result
                    selected = random.choice(results)
                    preview_url = selected.get('previews', {}).get('preview-hq-mp3')
                    
                    if preview_url:
                        filename = f"freesound_{selected['id']}.mp3"
                        music_path = os.path.join(self.music_dir, filename)
                        
                        if not os.path.exists(music_path):
                            print(f"  📥 Downloading from Freesound: {selected['name']}")
                            audio_response = requests.get(preview_url, timeout=60, stream=True)
                            audio_response.raise_for_status()
                            
                            with open(music_path, 'wb') as f:
                                for chunk in audio_response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            print(f"  ✅ Downloaded: {filename}")
                        
                        return music_path
                        
            except Exception as e:
                print(f"  ⚠️  Freesound failed: {e}")
        
        # Final fallback: use any existing music in the cache
        if os.path.exists(self.music_dir):
            existing = [f for f in os.listdir(self.music_dir) if f.endswith(('.mp3', '.wav', '.ogg'))]
            if existing:
                music_path = os.path.join(self.music_dir, random.choice(existing))
                print(f"  🎵 Using cached: {os.path.basename(music_path)}")
                return music_path
        
        print("  ⚠️  No background music sources available")
        print("     💡 Set PIXABAY_API_KEY or FREESOUND_API_KEY for dynamic music")
        print("     💡 Or manually add .mp3 files to assets/music/")
        return None
    
    def _mix_audio_with_music(self, voice_audio: AudioFileClip, music: AudioFileClip) -> AudioFileClip:
        """
        Mix voice audio with background music
        
        Args:
            voice_audio: Main voice/narration audio
            music: Background music (already volume-adjusted)
            
        Returns:
            Mixed audio clip
        """
        try:
            # Use CompositeAudioClip to layer the audio tracks
            mixed = CompositeAudioClip([voice_audio, music])
            return mixed
        except Exception as e:
            print(f"  ⚠️  Error mixing audio: {e}, using voice only")
            return voice_audio
    
    def create_video(self, script_data: Dict, audio_path: str, output_path: str) -> str:
        """
        Create horror story video with Pexels images, effects, and typewriter captions
        
        Args:
            script_data: Dictionary with title, script, tags
            audio_path: Path to audio file
            output_path: Path to save video
        
        Returns:
            Path to generated video
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print("\n🎬 Creating Horror Story Video")
        print("=" * 60)
        
        # Progress bar for overall process
        with tqdm(total=7, desc="🎞️  Rendering", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            
            # Step 1: Load audio
            pbar.set_description("📻 Loading audio")
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            pbar.update(1)
            
            # Step 2: Parse script into segments
            pbar.set_description("📝 Parsing script")
            segments = self._parse_script_segments(script_data['script'])
            pbar.update(1)
            
            # Step 3: Download Pexels images
            pbar.set_description("🖼️  Fetching images")
            image_paths = self._download_pexels_images(script_data['topic'], len(segments))
            pbar.update(1)
            
            # Step 4: Get background music (based on content mood/niche)
            pbar.set_description("🎵 Adding music")
            # Determine mood from config or default to horror
            niche = self.config.get('channel', {}).get('niche', 'horror')
            background_music = self._get_background_music(duration, mood=niche)
            if background_music:
                audio = self._mix_audio_with_music(audio, background_music)
                print("  ✅ Background music added")
            pbar.update(1)
            
            # Step 5: Create clips with effects and typewriter text
            pbar.set_description("🎨 Creating visuals")
            clips = self._create_clips_with_typewriter(
                segments, 
                image_paths, 
                duration, 
                script_data['title']
            )
            pbar.update(1)
            
            # Step 6: Combine and add audio
            pbar.set_description("🔗 Finalizing")
            video = concatenate_videoclips(clips, method="compose")
            try:
                video = video.with_audio(audio)
            except AttributeError:
                video = video.set_audio(audio)
            pbar.update(1)
            
            # Step 7: Render video
            pbar.set_description("💾 Rendering")
            video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                threads=4,
                logger=None,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                audio_bitrate='128k',
                bitrate='3000k',
                ffmpeg_params=['-crf', '20']
            )
            pbar.update(1)
        
        # Cleanup
        video.close()
        audio.close()
        if background_music:
            try:
                background_music.close()
            except:
                pass
        
        print(f"✅ Video created: {output_path}")
        return output_path
    
    def _parse_script_segments(self, script: str) -> List[str]:
        """Parse script into segments optimized for speech timing"""
        # Split by double newlines (paragraph breaks)
        segments = [s.strip() for s in script.split('\n\n') if s.strip()]
        
        # If no segments or too few, split by single newlines
        if len(segments) < 3:
            segments = [s.strip() for s in script.split('\n') if s.strip() and len(s.strip()) > 20]
        
        # If still too few, split by sentences (2-3 sentences per segment)
        if len(segments) < 3:
            sentences = re.split(r'(?<=[.!?])\s+', script)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Group sentences into segments of 2-3 sentences each
            segments = []
            current_segment = []
            current_words = 0
            
            for sentence in sentences:
                words_in_sentence = len(sentence.split())
                current_segment.append(sentence)
                current_words += words_in_sentence
                
                # Create segment if we have 30-50 words or 2-3 sentences
                if current_words >= 30 or len(current_segment) >= 3:
                    segments.append(' '.join(current_segment))
                    current_segment = []
                    current_words = 0
            
            # Add remaining sentences
            if current_segment:
                segments.append(' '.join(current_segment))
        
        return segments if segments else [script]
    
    def _download_pexels_images(self, topic: str, count: int) -> List[str]:
        """Download stock images from Pexels API"""
        image_paths = []
        
        if not self.pexels_api_key:
            print("  ⚠️  No Pexels API key, using generated dark backgrounds")
            return []
        
        try:
            # Search for relevant horror/dark images
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_api_key}
            params = {
                "query": f"dark horror creepy scary abandoned {topic}",
                "per_page": count,
                "orientation": "landscape"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            photos = response.json().get('photos', [])
            
            if not photos:
                print(f"  ⚠️  No Pexels images found for '{topic}'")
                return []
            
            # Download images
            os.makedirs('assets/images', exist_ok=True)
            for i, photo in enumerate(photos[:count]):
                img_url = photo['src']['large2x']
                img_path = f'assets/images/pexels_{i}.jpg'
                
                img_response = requests.get(img_url, timeout=30, stream=True)
                img_response.raise_for_status()
                
                with open(img_path, 'wb') as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                image_paths.append(img_path)
            
            print(f"  ✅ Downloaded {len(image_paths)} Pexels images")
            return image_paths
            
        except Exception as e:
            print(f"  ⚠️  Pexels download failed: {e}")
            return []
    
    def _create_clips_with_typewriter(self, segments: List[str], image_paths: List[str], 
                                      duration: float, title: str) -> List:
        """Create clips with Pexels images, effects, and typewriter text"""
        clips = []
        
        # Calculate duration per segment based on WORD COUNT (more accurate for speech)
        # Average speaking rate: 150 words per minute = 2.5 words per second
        # This gives 0.4 seconds per word
        total_words = sum(len(seg.split()) for seg in segments)
        segment_durations = []
        
        for segment in segments:
            # Allocate duration proportional to word count
            word_count = len(segment.split())
            word_ratio = word_count / total_words if total_words > 0 else 1.0 / len(segments)
            seg_duration = duration * word_ratio
            segment_durations.append(seg_duration)
        
        # Ensure total duration matches exactly
        duration_diff = duration - sum(segment_durations)
        if abs(duration_diff) > 0.1:  # If there's a noticeable difference
            segment_durations[-1] += duration_diff
        
        for i, text in enumerate(segments):
            seg_duration = segment_durations[i]
            
            # Get or generate background image
            if image_paths and i < len(image_paths):
                bg_clip = self._create_image_clip_with_effects(image_paths[i], seg_duration)
            else:
                bg_clip = self._create_fallback_background(seg_duration)
            
            # Add dark overlay for text readability
            overlay = self._create_dark_overlay(seg_duration)
            
            # Create typewriter text (appears gradually)
            text_clip = self._create_typewriter_text(
                text, 
                seg_duration,
                is_title=(i == 0),
                title=title if i == 0 else None
            )
            
            # Composite everything
            final_clip = CompositeVideoClip([bg_clip, overlay, text_clip])
            clips.append(final_clip)
        
        return clips
    
    def _create_image_clip_with_effects(self, image_path: str, duration: float) -> ImageClip:
        """Create image clip with Ken Burns effect (zoom/pan)"""
        # Load and process image
        img = Image.open(image_path)
        
        # Apply subtle effects
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)  # Increase contrast
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.9)  # Slightly desaturate
        
        # Slight blur for cinematic feel
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        
        # Resize to fit resolution
        img_ratio = img.width / img.height
        target_ratio = self.resolution[0] / self.resolution[1]
        
        if img_ratio > target_ratio:
            # Image is wider, fit to height
            new_height = self.resolution[1]
            new_width = int(new_height * img_ratio)
        else:
            # Image is taller, fit to width
            new_width = self.resolution[0]
            new_height = int(new_width / img_ratio)
        
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Create clip
        clip = ImageClip(img_array, duration=duration)
        
        # Add Ken Burns effect (subtle zoom)
        def zoom_effect(get_frame, t):
            frame = get_frame(t)
            progress = t / duration
            zoom_factor = 1.0 + (progress * 0.1)  # Zoom from 1.0 to 1.1
            
            h, w = frame.shape[:2]
            new_h, new_w = int(h / zoom_factor), int(w / zoom_factor)
            
            # Center crop
            y1 = (h - new_h) // 2
            x1 = (w - new_w) // 2
            cropped = frame[y1:y1+new_h, x1:x1+new_w]
            
            # Resize back
            from PIL import Image as PILImage
            img_pil = PILImage.fromarray(cropped)
            img_pil = img_pil.resize((w, h), PILImage.LANCZOS)
            return np.array(img_pil)
        
        try:
            clip = clip.transform(zoom_effect)
        except:
            pass  # If effect fails, use clip without effect
        
        # Ensure correct resolution
        if clip.size != self.resolution:
            try:
                clip = clip.resized(self.resolution)
            except AttributeError:
                clip = clip.resize(self.resolution)
        
        return clip
    
    def _create_fallback_background(self, duration: float) -> ImageClip:
        """Create dark horror background when no Pexels images available"""
        colors = [
            (10, 10, 15),     # Deep black-blue
            (15, 5, 5),       # Blood dark
            (5, 0, 15),       # Void purple
            (0, 10, 0),       # Dead forest
            (20, 0, 0),       # Crimson shadow
            (0, 0, 0),        # Pure darkness
        ]
        
        color = random.choice(colors)
        img = Image.new('RGB', self.resolution, color)
        
        # Add ominous gradient
        draw = ImageDraw.Draw(img, 'RGBA')
        for i in range(self.resolution[1]):
            alpha = int((i / self.resolution[1]) * 80)
            draw.line([(0, i), (self.resolution[0], i)], fill=(0, 0, 0, alpha))
        
        # Add vignette effect for horror atmosphere
        overlay = Image.new('RGBA', self.resolution, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        center_x, center_y = self.resolution[0] // 2, self.resolution[1] // 2
        max_radius = max(center_x, center_y)
        
        for i in range(100):
            radius = int(max_radius * (1 - i / 100))
            alpha = int((i / 100) * 150)
            bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
            overlay_draw.ellipse(bbox, fill=(0, 0, 0, alpha))
        
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        img_array = np.array(img)
        return ImageClip(img_array, duration=duration)
    
    def _create_dark_overlay(self, duration: float) -> ImageClip:
        """Create semi-transparent dark overlay for text readability"""
        overlay = Image.new('RGBA', self.resolution, (0, 0, 0, int(255 * self.text_overlay_opacity)))
        overlay_array = np.array(overlay)
        return ImageClip(overlay_array, duration=duration, ismask=False)
    
    def _create_typewriter_text(self, text: str, duration: float, 
                                is_title: bool = False, title: str = None) -> CompositeVideoClip:
        """Create text that appears with typewriter effect"""
        # Use image-based text for full control over positioning and wrapping
        # This prevents any cutoff issues from TextClip
        return self._create_text_image_clip(text, duration, is_title, title)
    
    def _create_text_image_clip(self, text: str, duration: float, 
                                 is_title: bool = False, title: str = None) -> ImageClip:
        """Fallback: Create text as image with eerie horror font"""
        img = Image.new('RGBA', self.resolution, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load fonts suitable for horror content - prioritize Impact for readability
        fonts_to_try = [
            ('/System/Library/Fonts/Supplemental/Impact.ttf', 65),  # Bold and dramatic
            ('/System/Library/Fonts/Supplemental/Futura.ttc', 65),
            ('/System/Library/Fonts/Helvetica.ttc', 65),
            ('/Library/Fonts/Arial.ttf', 65),
        ]
        
        text_font = None
        for font_path, size in fonts_to_try:
            try:
                text_font = ImageFont.truetype(font_path, size)
                break
            except:
                continue
        
        if not text_font:
            text_font = ImageFont.load_default()
        
        # Draw text with enhanced styling - LONGER LINES for better readability (30 chars max)
        wrapped_lines = []
        for paragraph in text.split('\n'):
            wrapped_lines.extend(textwrap.wrap(paragraph, width=30, break_long_words=True))  # Longer lines
        
        y_text = (self.resolution[1] - len(wrapped_lines) * 80) / 2
        
        for line in wrapped_lines:
            try:
                bbox = draw.textbbox((0, 0), line, font=text_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * 35
            
            # Center text with HUGE safety margin (150px from each edge)
            x_text = max(150, (self.resolution[0] - text_width) / 2)
            
            # Ensure text doesn't go off right side either
            if x_text + text_width > self.resolution[0] - 150:
                x_text = 150
            
            # Enhanced shadow/outline for horror effect - thicker and darker
            # Outer shadow (deep black outline) - extra thick for horror atmosphere
            for adj_x in range(-5, 6):
                for adj_y in range(-5, 6):
                    if adj_x != 0 or adj_y != 0:
                        draw.text((x_text + adj_x, y_text + adj_y), line, 
                                font=text_font, fill=(0, 0, 0, 255))
            
            # Main text (white or slightly red-tinted for horror)
            text_color = (255, 245, 245, 255)  # Slightly off-white with red tint
            draw.text((x_text, y_text), line, font=text_font, fill=text_color)
            
            y_text += 80  # More spacing between lines
        
        img_array = np.array(img)
        clip = ImageClip(img_array, duration=duration)
        
        return clip
    
    def _create_image_segments_with_captions(self, segments: List[str], duration: float, title: str) -> List:
        """Create image clips with modern typography captions"""
        clips = []
        segment_duration = duration / len(segments) if len(segments) > 0 else duration
        
        # Choose random color palette
        palette_name = random.choice(list(self.color_palettes.keys()))
        colors = self.color_palettes[palette_name]
        
        for i, text in enumerate(segments):
            # Alternate between colors in the palette
            bg_color = colors[i % len(colors)]
            
            # Create image with text
            img = self._create_text_image(text, bg_color, is_first=(i==0), title=title if i==0 else None)
            
            # Convert to clip
            img_array = np.array(img)
            clip = ImageClip(img_array, duration=segment_duration)
            clips.append(clip)
        
        return clips
    
    def _create_text_image(self, text: str, bg_color: tuple, is_first: bool = False, title: str = None) -> Image:
        """Create a beautiful image with modern typography"""
        import textwrap
        
        # Create image
        img = Image.new('RGB', self.resolution, bg_color)
        draw = ImageDraw.Draw(img)
        
        width, height = self.resolution
        
        # Try to load modern fonts
        fonts_to_try = [
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/SFNSDisplay.ttf',
            '/Library/Fonts/Arial.ttf',
            'Arial',
            'Helvetica'
        ]
        
        # Main text font
        text_font = None
        for font_path in fonts_to_try:
            try:
                text_font = ImageFont.truetype(font_path, 70)
                break
            except:
                continue
        
        if not text_font:
            text_font = ImageFont.load_default()
        
        # Title font (larger)
        title_font = None
        if is_first and title:
            for font_path in fonts_to_try:
                try:
                    title_font = ImageFont.truetype(font_path, 90)
                    break
                except:
                    continue
        
        # Add title on first slide
        if is_first and title and title_font:
            # Draw title at top
            title_lines = textwrap.wrap(title, width=25)
            y_text = height * 0.15
            
            for line in title_lines:
                try:
                    bbox = draw.textbbox((0, 0), line, font=title_font)
                    text_width = bbox[2] - bbox[0]
                except:
                    text_width = len(line) * 50
                
                x_text = (width - text_width) / 2
                
                # Draw shadow
                draw.text((x_text + 3, y_text + 3), line, font=title_font, fill=(0, 0, 0))
                # Draw text
                draw.text((x_text, y_text), line, font=title_font, fill=(255, 255, 255))
                y_text += 110
            
            # Add separator line
            line_y = y_text + 30
            line_start_x = width * 0.2
            line_end_x = width * 0.8
            draw.line([(line_start_x, line_y), (line_end_x, line_y)], fill=(255, 255, 255), width=3)
            
            y_text += 100
        else:
            y_text = height * 0.35
        
        # Wrap text to fit
        max_width = 35  # characters per line
        wrapped_lines = []
        for paragraph in text.split('\n'):
            wrapped_lines.extend(textwrap.wrap(paragraph, width=max_width))
        
        # Center text vertically
        total_text_height = len(wrapped_lines) * 90
        if not (is_first and title):
            y_text = (height - total_text_height) / 2
        
        # Draw text lines with shadow
        for line in wrapped_lines:
            try:
                bbox = draw.textbbox((0, 0), line, font=text_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * 40
            
            x_text = (width - text_width) / 2
            
            # Shadow for depth
            draw.text((x_text + 2, y_text + 2), line, font=text_font, fill=(0, 0, 0))
            # Main text
            draw.text((x_text, y_text), line, font=text_font, fill=(255, 255, 255))
            
            y_text += 90
        
        # Add subtle gradient overlay at bottom
        overlay = Image.new('RGBA', self.resolution, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Bottom fade
        for i in range(200):
            alpha = int((i / 200) * 60)
            y = height - 200 + i
            if y < height:
                overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
        
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        return img


if __name__ == "__main__":
    # Test video generation
    import yaml
    
    with open('../config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    generator = VideoGenerator(config)
    print("Video generator initialized successfully!")
    
    # Test with sample data
    test_script = {
        'title': 'Amazing Tech Facts 🔥',
        'script': 'This is a test video',
        'topic': 'technology'
    }
    
    # You would need actual audio file for this test
    # audio_path = '../output/audio/test.mp3'
    # output_path = '../output/videos/test_video.mp4'
    # generator.create_video(test_script, audio_path, output_path)
    
    print("Video generator module loaded successfully")
