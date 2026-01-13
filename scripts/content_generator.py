"""
Content Generator Module
Generates horror story scripts using Google Gemini
"""

import os
import random
import json
from datetime import datetime
from typing import Dict, List
import google.generativeai as genai
from tqdm import tqdm

class ContentGenerator:
    def __init__(self, config: Dict, gemini_key: str = None):
        self.config = config
        self.niche = config['channel']['niche']
        self.topics = config['content']['topics_pool'].get(self.niche, [])
        self.gemini_key = gemini_key or os.getenv('GEMINI_API_KEY')
        
        # Configure Gemini
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
            print("✨ Using Gemini for AI-powered horror story content")
        else:
            self.model = None
            print("⚠️  Warning: No Gemini API key found. Using template-based generation.")
        
        # Track used topics and story details to ensure uniqueness
        self.used_topics = set()
        self.used_story_elements = {
            'settings': set(),
            'characters': set(),
            'twists': set()
        }
    
    def generate_topic(self) -> str:
        """Generate a unique horror story topic each time"""
        available_topics = [t for t in self.topics if t not in self.used_topics]
        
        # Reset if all topics used
        if not available_topics:
            self.used_topics.clear()
            self.used_story_elements = {
                'settings': set(),
                'characters': set(),
                'twists': set()
            }
            available_topics = self.topics
        
        topic = random.choice(available_topics)
        self.used_topics.add(topic)
        return topic
    
    def generate_script_with_ai(self, topic: str, duration: int = 60) -> Dict[str, str]:
        """Generate horror story script with all metadata using a single Gemini prompt"""
        if not self.model:
            return self.generate_script_template(topic, duration)
        
        print(f"  🤖 Generating horror story for: {topic}")
        try:
            with tqdm(total=2, desc="📝 Content", leave=False) as pbar:
                pbar.set_description("📝 Creating horror content prompt")
                
                # Generate uniqueness constraints
                used_settings_str = ', '.join(list(self.used_story_elements['settings'])[-10:]) if self.used_story_elements['settings'] else 'none yet'
                used_characters_str = ', '.join(list(self.used_story_elements['characters'])[-10:]) if self.used_story_elements['characters'] else 'none yet'
                used_twists_str = ', '.join(list(self.used_story_elements['twists'])[-10:]) if self.used_story_elements['twists'] else 'none yet'
                
                # Calculate word count based on duration
                # Average speaking rate: ~150 words per minute at normal speed
                # For shorts (1.25x speed): ~187 words per minute
                # So for 60 seconds at 1.25x speed: ~120-150 words
                # For 120 seconds at 1.0x speed: ~280-320 words
                words_per_minute = 150
                target_words = int((duration / 60) * words_per_minute)
                word_range_min = max(80, target_words - 30)
                word_range_max = target_words + 20
                
                # Determine if this is a short (60 seconds or less)
                is_short = duration <= 60
                duration_text = f"{duration}-second" if is_short else f"{duration // 60}-minute"
                
                # Single comprehensive prompt that generates everything
                prompt = f"""You are a viral horror content creator for YouTube. Generate a complete horror video package about: {topic}

You must return a JSON object with the following structure. Return ONLY valid JSON, no markdown code blocks, no extra text.

{{
    "title": "Your click-worthy title here",
    "script": "Your horror story narration here",
    "description": "Your YouTube description here",
    "tags": ["tag1", "tag2", "tag3", ...]
}}

=== TITLE REQUIREMENTS ===
Create a title that will get MAXIMUM clicks (high CTR). Use these proven formats:
- Curiosity gap: "I Found Out What Happens When You See [Topic]..."
- Warning/urgency: "WARNING: Don't Watch This Alone"
- Social proof: "This Video Made 3 Million People Unable to Sleep"
- Mystery: "The Truth About [Topic] Nobody Wants You to Know"
- First-person terror: "I Experienced [Topic] and I'm Still Terrified"
- Challenge: "Only 1% Can Watch This Without Looking Away"

Title must be:
- Under 70 characters (optimal for YouTube display)
- Emotionally triggering (fear, curiosity, urgency)
- Specific to the topic but universally intriguing
- NO clickbait that doesn't deliver - the story must match the promise

=== SCRIPT REQUIREMENTS ===
Write a {duration_text} horror story narration.
**CRITICAL: The script MUST be {word_range_min}-{word_range_max} words. COUNT YOUR WORDS.**
{"This is for a YouTube SHORT - keep it VERY concise and punchy!" if is_short else ""}

UNIQUENESS - AVOID THESE RECENTLY USED ELEMENTS:
- Settings: {used_settings_str}
- Characters: {used_characters_str}  
- Twists: {used_twists_str}

{"STORY STRUCTURE FOR SHORT (under 60 seconds):" if is_short else "STORY STRUCTURE:"}
{"1. HOOK (5 seconds): Immediate dread. One shocking line." if is_short else "1. HOOK (First 15 seconds): Start with immediate dread. Something is wrong. Use \"you\" to trap the listener inside the experience. No slow buildup - begin where fear begins."}

{"2. ESCALATION (35-40 seconds): Quick, punchy horror beats. Maximum 4-5 short paragraphs." if is_short else "2. ESCALATION (Middle): Layer horror upon horror. Each detail more disturbing than the last. Short sentences for panic. Longer sentences to drag them deeper. Use what people fear in the dark - sounds, glimpses, touches that shouldn't be there."}

{"3. CLIMAX (10 seconds): One devastating twist line. End abruptly." if is_short else "3. CLIMAX (Final 15 seconds): A twist that shatters everything. The last line should be the most disturbing. No resolution. No escape. Leave them in pure terror."}

WRITING STYLE:
- Second person ("you") to make it personal
- Present tense for immediacy
- Visceral sensory details
- Psychological + physical horror combined
- Show, don't explain
- {"4-6 VERY short paragraphs (SHORT FORMAT)" if is_short else "8-10 short paragraphs separated by blank lines"}

STRICT RULES FOR SCRIPT:
- ONLY words to be spoken aloud
- NO timestamps, labels, or headings
- NO parentheses, brackets, or stage directions
- NO emojis or special formatting
- NO "[Sound effect]" or "[Visual]" notes
{"- KEEP IT SHORT! Maximum " + str(word_range_max) + " words!" if is_short else ""}

=== DESCRIPTION REQUIREMENTS ===
Create a YouTube description optimized for:
1. Search (SEO keywords in first 2 lines)
2. Engagement (clear calls-to-action)
3. Watch time (intrigue without spoilers)

Include:
- Hook from the story (first 1-2 sentences)
- Emoji-enhanced calls to action (🔔 Subscribe, 👍 Like, 💬 Comment)
- Warning about horror content
- Hashtags at the end: #horror #scarystories #creepypasta #shorts #viral

Keep under 800 characters total.

=== TAGS REQUIREMENTS ===
Generate 15-20 YouTube tags optimized for discoverability:
- Start with high-volume terms: "horror story", "scary stories", "creepypasta"
- Include trending terms: "shorts", "viral", "scary", "true horror"
- Add topic-specific variations
- Mix broad and niche terms
- Each tag should be lowercase
- No duplicate meanings

=== OUTPUT FORMAT ===
Return ONLY a valid JSON object. No markdown, no code blocks, no explanation.
The JSON must be parseable by Python's json.loads() function.

Generate the complete horror content package now:"""

                pbar.update(1)
                
                # Call Gemini
                pbar.set_description("🤖 Generating with Gemini")
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Parse JSON response
                content = self._parse_gemini_response(response_text, topic)
                
                # Extract story elements to track uniqueness
                self._extract_story_elements(content['script'])
                pbar.update(1)
            
            print(f"  ✅ Horror story + metadata generated!")
            
            # Add topic to the content
            content['topic'] = topic
            
            return content
            
        except Exception as e:
            print(f"  ⚠️  Gemini generation failed: {e}. Using template.")
            return self.generate_script_template(topic, duration)
    
    def _parse_gemini_response(self, response_text: str, topic: str) -> Dict:
        """
        Parse the JSON response from Gemini, with fallback handling
        
        Args:
            response_text: Raw response from Gemini
            topic: Original topic for fallback generation
            
        Returns:
            Dictionary with title, script, description, tags
        """
        import re
        
        # Try to extract JSON from response
        try:
            # First, try direct JSON parsing
            content = json.loads(response_text)
            return self._validate_content(content, topic)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON within markdown code blocks
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                content = json.loads(json_match.group(1))
                return self._validate_content(content, topic)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Try to find raw JSON object
        try:
            json_match = re.search(r'\{[^{}]*"title"[^{}]*"script"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                content = json.loads(json_match.group(0))
                return self._validate_content(content, topic)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Try to find JSON with nested structures
        try:
            # Find the first { and last }
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = response_text[start:end+1]
                content = json.loads(json_str)
                return self._validate_content(content, topic)
        except json.JSONDecodeError:
            pass
        
        # If all parsing fails, extract what we can and use fallbacks
        print("  ⚠️  Could not parse JSON, extracting content manually...")
        return self._extract_content_manually(response_text, topic)
    
    def _validate_content(self, content: Dict, topic: str) -> Dict:
        """Validate and fill in missing fields in parsed content"""
        validated = {}
        
        # Title - use parsed or generate fallback
        validated['title'] = content.get('title', '').strip()
        if not validated['title'] or len(validated['title']) < 10:
            validated['title'] = self.generate_horror_title(topic)
        
        # Script - use parsed or raise error (script is required)
        validated['script'] = content.get('script', '').strip()
        if not validated['script'] or len(validated['script']) < 100:
            raise ValueError("Script too short or missing")
        
        # Description - use parsed or generate fallback
        validated['description'] = content.get('description', '').strip()
        if not validated['description'] or len(validated['description']) < 50:
            validated['description'] = self.generate_description(validated['script'], topic)
        
        # Tags - use parsed or generate fallback
        tags = content.get('tags', [])
        if isinstance(tags, list) and len(tags) >= 5:
            validated['tags'] = [str(tag).strip().lower() for tag in tags[:20]]
        else:
            validated['tags'] = self.generate_horror_tags(topic)
        
        return validated
    
    def _extract_content_manually(self, response_text: str, topic: str) -> Dict:
        """Extract content manually when JSON parsing fails"""
        import re
        
        # Try to find title
        title_match = re.search(r'"title"\s*:\s*"([^"]+)"', response_text)
        title = title_match.group(1) if title_match else self.generate_horror_title(topic)
        
        # Try to find script
        script_match = re.search(r'"script"\s*:\s*"(.*?)"(?=\s*,\s*"(?:description|tags)"|$)', response_text, re.DOTALL)
        if script_match:
            script = script_match.group(1).replace('\\n', '\n').replace('\\"', '"')
        else:
            # If no script found in JSON format, assume the whole response might be the script
            # (Gemini sometimes ignores JSON format and writes the story directly)
            script = response_text
            if len(script) > 2000:
                script = script[:2000]
        
        # Try to find description
        desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', response_text)
        description = desc_match.group(1) if desc_match else self.generate_description(script, topic)
        
        # Try to find tags
        tags_match = re.search(r'"tags"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
        if tags_match:
            tags_str = tags_match.group(1)
            tags = re.findall(r'"([^"]+)"', tags_str)
            tags = [tag.strip().lower() for tag in tags[:20]]
        else:
            tags = self.generate_horror_tags(topic)
        
        return {
            'title': title,
            'script': script,
            'description': description,
            'tags': tags
        }

    def _extract_story_elements(self, script: str) -> None:
        """Extract and track story elements to ensure uniqueness in future stories"""
        script_lower = script.lower()
        
        # Common settings to track
        settings = ['house', 'basement', 'attic', 'forest', 'hospital', 'school', 
                   'apartment', 'hotel', 'car', 'mirror', 'bedroom', 'kitchen',
                   'office', 'subway', 'elevator', 'stairs', 'hallway', 'closet']
        for setting in settings:
            if setting in script_lower:
                self.used_story_elements['settings'].add(setting)
        
        # Common character types to track
        characters = ['child', 'woman', 'man', 'stranger', 'neighbor', 'friend',
                     'shadow', 'figure', 'reflection', 'doll', 'voice', 'thing']
        for char in characters:
            if char in script_lower:
                self.used_story_elements['characters'].add(char)
        
        # Common twist elements to track
        twists = ['dream', 'dead', 'ghost', 'possessed', 'alone', 'watching',
                 'trapped', 'yourself', 'never left', 'always been', 'too late']
        for twist in twists:
            if twist in script_lower:
                self.used_story_elements['twists'].add(twist)
    
    def generate_horror_title(self, topic: str) -> str:
        """Generate an SEO-optimized, click-worthy horror story title"""
        # High-performing title formats based on YouTube analytics patterns
        # These formats are proven to drive higher CTR (click-through rate)
        templates = [
            # Curiosity gap + emotional trigger
            f"I Found Out What Happens When You See {topic} (I Wish I Hadn't)",
            f"The Real Reason No One Talks About {topic}",
            f"What I Saw at 3AM Changed Everything | {topic}",
            
            # Warning/urgency format (high CTR)
            f"WARNING: {topic} - Don't Watch This Alone",
            f"If You See {topic}, RUN. Here's Why...",
            f"STOP! What You Don't Know About {topic} Could Save Your Life",
            
            # Mystery/intrigue format
            f"The Dark Truth Behind {topic} | True Horror Story",
            f"{topic}: The Story They Don't Want You to Know",
            f"Why {topic} Keeps Me Awake at Night",
            
            # Social proof + horror
            f"3 Million People Watched This and Couldn't Sleep | {topic}",
            f"The {topic} Incident That Nobody Can Explain",
            f"Viewers Begged Me Not to Post This | {topic}",
            
            # First-person authentic format
            f"I Experienced {topic} and I'm Still Terrified",
            f"My Encounter with {topic} (This is Not a Joke)",
            f"The Night {topic} Changed My Life Forever",
            
            # Challenge/dare format
            f"Watch {topic} at Night, I Dare You",
            f"Try Not to Get Scared: {topic}",
            f"Only 1% Can Finish Watching | {topic}",
        ]
        
        title = random.choice(templates)
        
        # Ensure title is under 100 chars but descriptive
        if len(title) > 100:
            title = title[:97] + "..."
        
        return title
    
    def generate_horror_tags(self, topic: str) -> List[str]:
        """Generate SEO-optimized horror-specific tags for maximum discoverability"""
        # Prioritize high-search-volume tags first (YouTube uses first few tags heavily)
        primary_tags = [
            'horror story',           # High volume
            'scary stories',          # High volume  
            'creepypasta',           # High volume, dedicated audience
            'horror',                # Broad but essential
            'scary',                 # High engagement
            'true scary stories',    # Trending format
            'horror stories to fall asleep to',  # Long-form search
            'creepy stories',        # Alternative search term
        ]
        
        # Secondary tags for broader reach
        secondary_tags = [
            'paranormal',
            'ghost stories',
            'nightmare fuel',
            'dont watch alone',
            'scary story time',
            'true horror stories',
            'real horror',
            'terrifying stories',
            '3am scary',
            'nightmare stories',
        ]
        
        # Trending/viral tags that boost algorithm visibility
        viral_tags = [
            'shorts',
            'viral',
            'trending',
            'fyp',
            'storytime',
            'reddit horror',
            'mr nightmare',
            'lets read',
        ]
        
        # Topic-specific tags (extract meaningful words)
        topic_words = [word.lower() for word in topic.split() if len(word) > 3]
        topic_tags = [f"{word} horror" for word in topic_words[:2]]
        topic_tags += [f"scary {word}" for word in topic_words[:2]]
        
        # Combine strategically - primary tags first for SEO weight
        all_tags = primary_tags[:6] + topic_tags[:4] + secondary_tags[:5] + viral_tags[:5]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in all_tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        
        return unique_tags[:20]  # YouTube recommends 15-20 tags max
    
    def generate_script_template(self, topic: str, duration: int = 60) -> Dict[str, str]:
        """Generate horror story template script (fallback)"""
        
        # Check if this is for a Short (60 seconds or less)
        is_short = duration <= 60
        
        if is_short:
            # Shorter templates for YouTube Shorts (under 60 seconds, ~100-120 words)
            horror_templates = [
                f"You wake up at 3 AM. Something feels wrong.\n\n"
                f"Your phone screen glows. A text from yourself: Don't look behind you.\n\n"
                f"You feel breath on your neck. Cold. Wet.\n\n"
                f"Another text: Too late.\n\n"
                f"The phone shows your camera. {topic} stands behind you. Smiling.\n\n"
                f"You never sent those texts.",
                
                f"The mirror shows your reflection. But something's off.\n\n"
                f"You raise your hand. It doesn't.\n\n"
                f"Instead, it presses against the glass from inside.\n\n"
                f"It mouths one word: Finally.\n\n"
                f"The glass cracks. {topic} reaches through.\n\n"
                f"You were never the real one.",
                
                f"You're home alone. You hear your mom call your name from downstairs.\n\n"
                f"You start walking down. Then your mom whispers from the closet behind you.\n\n"
                f"Don't go down there. I heard it too.\n\n"
                f"The voice downstairs calls again. It sounds exactly like her.\n\n"
                f"Then you hear a third voice. From the basement.\n\n"
                f"Also your mother's. {topic}.",
            ]
        else:
            # Full-length templates for regular videos
            horror_templates = [
                f"You hear it again. That sound from {topic}.\n\n"
                f"Three nights in a row now. Always at 3:47 AM. Always the same pattern.\n\n"
                f"Your rational mind tells you it's nothing. Old house settling. Wind in the pipes. "
                f"But your body knows better. Your body remembers what happened last time you ignored it.\n\n"
                f"Tonight, you decide to investigate. The hallway stretches longer than it should. "
                f"The darkness feels thick, almost solid. Your phone's flashlight cuts through it weakly.\n\n"
                f"The sound is coming from the basement. Of course it is. It's always the basement.\n\n"
                f"Each step down creaks. Your breathing echoes. You can hear your heartbeat in your ears.\n\n"
                f"Then you see it. {topic}. Right where you left it. Exactly where you left it.\n\n"
                f"Except now it's different. Now it's looking back at you.\n\n"
                f"And you realize with cold certainty: you should never have come down here.\n\n"
                f"Because now it knows you know. And it's not going to let you leave.",
                
                f"The text message appears on your phone. Unknown number. Three words: Check your closet.\n\n"
                f"You're home alone. You've been home alone all night. The doors are locked. "
                f"The windows are shut. No one could have gotten in.\n\n"
                f"Another message: I can see you from here.\n\n"
                f"Your blood runs cold. Slowly, you turn to face {topic}. "
                f"It's been there all evening. You walked past it a dozen times.\n\n"
                f"But now, in the dim light, you notice something you didn't before. "
                f"A shadow. Behind it. The wrong shape. The wrong size.\n\n"
                f"Your phone buzzes again: Don't turn around.\n\n"
                f"But you already have. And you see it now. {topic}. Right behind you. "
                f"Close enough to touch. Close enough to whisper.\n\n"
                f"How long has it been standing there?\n\n"
                f"Your phone buzzes one last time: Too late.\n\n"
                f"The lights go out. In the darkness, you feel breath on your neck. "
                f"And you realize the texts weren't a warning.\n\n"
                f"They were a countdown.",
                
                f"Everyone told you not to go near {topic}. There were stories. "
                f"People who went there and came back different. Or didn't come back at all.\n\n"
                f"But you didn't listen. You never do.\n\n"
                f"Now you understand why. Now, standing here in the silence, you finally understand.\n\n"
                f"Because {topic} isn't what you thought it was. It never was.\n\n"
                f"The air feels wrong here. Too still. Too quiet. Like the world is holding its breath. "
                f"Waiting for something.\n\n"
                f"Then you hear it. Your own voice. Speaking words you haven't said yet. "
                f"Coming from deeper inside.\n\n"
                f"You follow the sound, even though every instinct screams at you to run. "
                f"Your feet carry you forward. Not because you want them to. "
                f"Because they have to.\n\n"
                f"The voice gets louder. Your voice. Screaming now. Begging. "
                f"Begging for something you don't understand yet.\n\n"
                f"You round the corner and see yourself. Standing there. "
                f"Staring at {topic}. Just like you were five minutes ago.\n\n"
                f"And you realize with horror that you never left. You never moved.\n\n"
                f"You've been standing here the whole time. Watching yourself arrive. Again and again.\n\n"
                f"And you always will be."
            ]
        
        script = random.choice(horror_templates)
        
        return {
            'title': self.generate_horror_title(topic),
            'script': script,
            'description': self.generate_description(script, topic),
            'topic': topic,
            'tags': self.generate_horror_tags(topic)
        }
    
    def generate_title(self, topic: str) -> str:
        """Generate an engaging title (legacy method)"""
        return self.generate_horror_title(topic)
    
    def generate_description(self, script: str, topic: str = "") -> str:
        """Generate SEO-optimized video description for maximum impressions"""
        # Get hook from script (first impactful sentence)
        sentences = script.replace('\n', ' ').split('.')
        hook = sentences[0].strip() if sentences else "A terrifying tale awaits..."
        if len(hook) > 150:
            hook = hook[:147] + "..."
        
        # SEO-optimized description template
        # First 2-3 lines are crucial - they appear in search results
        description = f"""{hook}

😱 This horror story will keep you up at night. Watch if you dare...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔔 SUBSCRIBE for daily horror stories that will terrify you!
👍 LIKE if this scared you (or if you survived!)
💬 COMMENT your scariest experience below - I read them all!
🔗 SHARE with someone who needs a good scare!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📺 WHAT YOU'LL EXPERIENCE:
• A bone-chilling horror story narrated with dark atmosphere
• Creepy visuals that enhance the terror
• A twist ending you won't see coming

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ WARNING: This video contains horror content. Viewer discretion advised.
🎧 Best experienced with headphones in a dark room...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ TAGS:
#horror #scarystories #creepypasta #horrorstory #scary #truehorror #paranormal #ghoststories #nightmare #creepy #terrifying #shorts #viral #trending #storytime

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

� More Horror Content:
If you enjoyed this scary story, hit that subscribe button and turn on notifications (🔔) so you never miss a new horror story!

New horror stories uploaded daily at midnight... 🌙

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

© Midnight Horror Tales - Original Horror Content
All stories are original creations for entertainment purposes.
"""
        return description
    
    def generate_tags(self, topic: str) -> List[str]:
        """Generate relevant tags (legacy method)"""
        return self.generate_horror_tags(topic)
    
    def save_content(self, content: Dict, output_dir: str = 'content'):
        """Save generated content to file"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/script_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        return filename


if __name__ == "__main__":
    # Test the content generator
    import yaml
    
    with open('../config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    generator = ContentGenerator(config)
    topic = generator.generate_topic()
    content = generator.generate_script_with_ai(topic)
    
    print("Generated Content:")
    print(f"Title: {content['title']}")
    print(f"Script: {content['script'][:200]}...")
    print(f"Tags: {content['tags']}")
    
    filename = generator.save_content(content)
    print(f"\nSaved to: {filename}")
