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
        """Generate philosophical script using Gemini"""
        if not self.model:
            return self.generate_script_template(topic, duration)
        
        print(f"  🤖 Generating philosophical script for: {topic}")
        try:
            with tqdm(total=3, desc="📝 Content", leave=False) as pbar:
                pbar.set_description("📝 Creating philosophical prompt")
                
                # Philosophical prompt for Gemini
                prompt = f"""Create a deeply engaging, emotionally resonant {duration}-second spoken script about: {topic}

This script is for a philosophical YouTube channel focused on ideas that quietly unsettle the viewer and make them reflect long after the video ends.

CORE GOALS:
- Capture attention immediately
- Create inner tension or curiosity
- Feel personal, not academic
- Leave the viewer slightly uncomfortable, thoughtful, or awake

STRUCTURE REQUIREMENTS:

Opening (first 10–15 seconds):
Begin with a sharp, unsettling question, paradox, or observation that feels personal to the viewer.
It should challenge an assumption they didn’t realize they were making.
Avoid generic philosophy clichés.
The opening must make the viewer feel: “Wait… that’s true.”

Middle (majority of the script):
Explore {topic} through multiple angles:
- Inner psychology
- Everyday lived experience
- A quiet philosophical insight
Use simple language to express deep ideas.
Prefer concrete examples over abstract theory.
Build tension by slowly revealing implications.
Let thoughts evolve rather than explain everything at once.

Ending (final 10–15 seconds):
Do not summarize.
End with a lingering insight, reframed question, or realization that turns inward.
The final lines should invite silence, not answers.

STYLE & DELIVERY:
- Conversational, calm, and reflective
- Written as if speaking to one person late at night
- Short sentences. Varied rhythm.
- Occasional pauses implied through line breaks, not punctuation
- Use metaphors sparingly but vividly

FORMAT REQUIREMENTS:
- Break the script into SHORT SEGMENTS (2–4 sentences each)
- Separate segments with a blank line
- Each segment must express ONE complete thought
- Create at least 8–10 segments total

STRICT RULES:
- Write ONLY the words spoken aloud
- Do NOT include timestamps
- Do NOT include labels, headings, or explanations
- Do NOT include parentheses, brackets, or stage directions
- Do NOT include visual or camera instructions
- Do NOT include emojis
- Return ONLY the narration text

The result should feel intimate, unsettling, and quietly profound.

Return ONLY the script text that will be read by the narrator, nothing else.

Script:"""
                pbar.update(1)
                
                # Call Gemini
                pbar.set_description("🤖 Calling Gemini")
                response = self.model.generate_content(prompt)
                script = response.text.strip()
                pbar.update(1)
                
                pbar.set_description("✨ Creating metadata")
                title = self.generate_horror_title(topic)
                description = self.generate_description(script)
                
                # Extract story elements to track uniqueness
                self._extract_story_elements(script)
                pbar.update(1)
            
            print(f"  ✅ Horror story generated!")
            
            return {
                'title': title,
                'script': script,
                'description': description,
                'topic': topic,
                'tags': self.generate_horror_tags(topic)
            }
            
        except Exception as e:
            print(f"  ⚠️  Gemini generation failed: {e}. Using template.")
            return self.generate_script_template(topic, duration)
    
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
        """Generate a horror story title"""
        templates = [
            f"{topic} | True Horror Story",
            f"{topic} - A Terrifying Tale",
            f"{topic} | Scary Story",
            f"HORROR: {topic}",
            f"{topic} | Real Horror",
            f"{topic} - You Won't Sleep Tonight",
            f"TRUE STORY: {topic}",
            f"{topic} | Creepypasta",
            f"{topic} - Horror Story",
            f"SCARY: {topic}"
        ]
        return random.choice(templates)
    
    def generate_horror_tags(self, topic: str) -> List[str]:
        """Generate horror-specific tags"""
        base_tags = [
            'horror',
            'scary story',
            'creepypasta',
            'horror stories',
            'scary',
            'true horror',
            'scary stories',
            'horror story',
            'creepy',
            'terrifying'
        ]
        topic_tags = [word.lower() for word in topic.split() if len(word) > 3]
        return base_tags[:7] + topic_tags[:3]
    
    def generate_script_template(self, topic: str, duration: int = 60) -> Dict[str, str]:
        """Generate horror story template script (fallback)"""
        
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
            'description': self.generate_description(script),
            'topic': topic,
            'tags': self.generate_horror_tags(topic)
        }
    
    def generate_title(self, topic: str) -> str:
        """Generate an engaging title (legacy method)"""
        return self.generate_horror_title(topic)
    
    def generate_description(self, script: str) -> str:
        """Generate video description"""
        first_sentence = script.split('.')[0] if '.' in script else script[:100]
        return f"""{first_sentence}...

In this video, we explore fascinating insights and share valuable information you don't want to miss!

🔔 Subscribe for more amazing content!
👍 Like if you enjoyed this video!
💬 Comment your thoughts below!

#shorts #viral #facts #knowledge #educational
"""
    
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
