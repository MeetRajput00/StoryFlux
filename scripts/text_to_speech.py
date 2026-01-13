"""
Text-to-Speech Module
Converts script text to speech audio using free TTS options
"""

import os
import asyncio
import edge_tts
from typing import Dict
from tqdm import tqdm
from elevenlabs.client import ElevenLabs

class TextToSpeech:
    def __init__(self, method: str = 'edge-tts', speed_factor: float = 1.25, voice: str = 'en-US-AriaNeural'):
        """
        Initialize TTS engine
        
        Args:
            method: 'edge-tts' (Microsoft Edge TTS - free, natural voices, requires internet)
            speed_factor: Speed multiplier (1.0 = normal, 1.25 = 25% faster)
            voice: Voice to use (default: en-US-AriaNeural - female, natural)
                   Popular options:
                   - en-US-AriaNeural (female, clear and natural)
                   - en-US-GuyNeural (male, professional)
                   - en-US-JennyNeural (female, warm and friendly)
                   - en-GB-SoniaNeural (British female)
                   - en-AU-NatashaNeural (Australian female)
        """
        self.method = method
        self.speed_factor = speed_factor
        self.voice = voice
    
    def generate_audio(self, text: str, output_path: str, language: str = 'en') -> str:
        """
        Generate audio from text
        
        Args:
            text: Script text to convert
            output_path: Path to save audio file
            language: Language code (e.g., 'en', 'es', 'fr')
        
        Returns:
            Path to generated audio file
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            return self._generate_edge_tts(text, output_path)
        except Exception as e:
            print(f"Error generating audio with {self.method}: {e}")
            raise
    
    def _generate_edge_tts(self, text: str, output_path: str) -> str:
        """Generate audio using Microsoft Edge TTS (free, natural voices)"""
        # Calculate rate for speed adjustment
        # Edge-TTS rate format: "+X%" or "-X%"
        rate_percent = int((self.speed_factor - 1.0) * 100)
        rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
        
        with tqdm(total=1, desc="🎙️  Audio", leave=False) as pbar:
            pbar.set_description(f"🎙️  Generating speech ({self.voice})")
            
            # Run async function in sync context
            asyncio.run(self._async_generate_edge_tts(text, output_path, rate_str))
            
            pbar.update(1)
            speed_info = f" at {self.speed_factor}x speed" if self.speed_factor != 1.0 else ""
            print(f"  ✅ Audio generated{speed_info}: {output_path}")
        
        return output_path
    
    async def _async_generate_edge_tts(self, text: str, output_path: str, rate: str):
        """Async helper for Edge TTS generation"""
        # communicate = edge_tts.Communicate(text, self.voice, rate=rate)
        # await communicate.save(output_path)
        # using elevenlabs api for now as it is more reliable
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="onwK4e9ZLuTAKqWW03F9",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
    
    def generate_from_script(self, script_data: Dict, output_dir: str = 'output/audio') -> str:
        """
        Generate audio from script data
        
        Args:
            script_data: Dictionary containing script and metadata
            output_dir: Directory to save audio
        
        Returns:
            Path to generated audio file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        script_text = script_data.get('script', '')
        timestamp = script_data.get('timestamp', 'audio')
        
        output_path = f"{output_dir}/{timestamp}.mp3"
        return self.generate_audio(script_text, output_path)


class AudioProcessor:
    """Additional audio processing utilities"""
    
    @staticmethod
    def get_audio_duration(audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            # Try MoviePy 2.x import
            try:
                from moviepy import AudioFileClip
            except ImportError:
                from moviepy.editor import AudioFileClip
            
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            audio.close()
            return duration
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 0.0
    
    @staticmethod
    def adjust_speed(audio_path: str, output_path: str, speed_factor: float = 1.0):
        """
        Adjust audio speed
        
        Args:
            audio_path: Input audio file
            output_path: Output audio file
            speed_factor: Speed multiplier (1.0 = normal, 1.5 = 50% faster)
        """
        try:
            # Try MoviePy 2.x import
            try:
                from moviepy import AudioFileClip
            except ImportError:
                from moviepy.editor import AudioFileClip
            
            audio = AudioFileClip(audio_path)
            # Use with_speed_scaled for MoviePy 2.x (speed_factor: 1.5 = 1.5x faster)
            try:
                audio_adjusted = audio.with_speed_scaled(speed_factor)
            except AttributeError:
                # Fallback for MoviePy 1.x
                audio_adjusted = audio.speedx(speed_factor)
            
            audio_adjusted.write_audiofile(output_path, logger=None)
            audio.close()
            audio_adjusted.close()
            return output_path
        except Exception as e:
            print(f"Error adjusting audio speed: {e}")
            # If it fails, just copy the original
            import shutil
            if audio_path != output_path:
                shutil.copy(audio_path, output_path)
            return audio_path


if __name__ == "__main__":
    # Test TTS
    tts = TextToSpeech(method='edge-tts')
    
    test_script = {
        'script': "Hello! This is a test of the text to speech system. "
                 "It converts written text into natural sounding speech. "
                 "Subscribe for more amazing content!",
        'timestamp': 'test'
    }
    
    audio_path = tts.generate_from_script(test_script, output_dir='../output/audio')
    print(f"Test audio generated: {audio_path}")
    
    # Get duration
    processor = AudioProcessor()
    duration = processor.get_audio_duration(audio_path)
    print(f"Audio duration: {duration:.2f} seconds")
