import os
import random
import logging
from typing import List, Optional
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class CaptionGenerator:
    # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
    # do not change this unless explicitly requested by the user
    
    FALLBACK_HOOKS = [
        "🚀 This will change everything!",
        "🤯 Mind-blowing content you need to see!",
        "💡 This is incredible!",
        "🔥 This is absolutely game-changing!",
        "⚡ Everyone's talking about this!",
        "🌟 This just got a whole lot better!",
        "🎯 This is what we've been waiting for!",
        "💥 Groundbreaking content revealed!",
        "🚨 Alert: This changes the game completely!",
        "✨ The most impressive thing you'll see today!",
    ]
    
    HASHTAGS = [
        "#Viral", "#Trending", "#Amazing", "#Incredible", "#MustWatch",
        "#Explore", "#ForYou", "#Wow", "#Insane", "#Epic",
        "#ContentCreator", "#Insta", "#InstaGood", "#InstaDaily", "#InstaMood",
        "#PhotoOfTheDay", "#Video", "#Reel", "#Reels", "#Vibes",
        "#Motivation", "#Inspiration", "#Goals", "#Success", "#Lifestyle",
        "#Follow", "#Like", "#Share", "#Comment", "#Engagement"
    ]
    
    def __init__(self):
        logger.info("Initializing AI-powered Caption Generator")
        self.use_ai = os.getenv('USE_AI_CAPTIONS', 'true').lower() == 'true'
        
        if self.use_ai:
            try:
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    logger.warning("OPENAI_API_KEY not set, falling back to template captions")
                    self.use_ai = False
                    self.openai_client = None
                else:
                    self.openai_client = OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized with gpt-5 model")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.use_ai = False
                self.openai_client = None
        else:
            logger.info("AI captions disabled, using template-based generation")
            self.openai_client = None
    
    def generate_ai_caption(self, video_context: Optional[str] = None) -> Optional[str]:
        """
        Generate AI-powered caption using OpenAI gpt-5
        
        Args:
            video_context: Context about the video (title, description, etc.)
            
        Returns:
            Generated caption or None if failed
        """
        try:
            if not self.openai_client:
                return None
            
            logger.info("Generating AI caption with OpenAI gpt-5")
            
            context_text = f" The video is about: {video_context}" if video_context else ""
            
            prompt = f"""Generate a catchy, viral Instagram caption for a video.{context_text}

Requirements:
- Start with an attention-grabbing hook (use emojis)
- Make it engaging and compelling
- Keep it concise (under 150 characters for the main text)
- Add 15-20 relevant trending hashtags
- End with a call-to-action like "Follow for more!" or "Double tap if you agree!"
- Make it sound natural and authentic, not robotic
- Focus on creating FOMO (fear of missing out)

Format the caption exactly like this:
[Attention-grabbing hook with emoji]

[15-20 hashtags separated by spaces]

[Call to action]"""

            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a viral Instagram content creator expert who specializes in writing engaging, high-converting captions that drive engagement and followers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=500
            )
            
            caption = response.choices[0].message.content.strip()
            logger.info(f"AI caption generated successfully (length: {len(caption)} chars)")
            return caption
            
        except Exception as e:
            logger.error(f"Error generating AI caption: {e}", exc_info=True)
            return None
    
    @lru_cache(maxsize=128)
    def _get_cached_hashtags(self, count: int, seed: int) -> tuple:
        """Cache hashtag selections for faster generation"""
        rng = random.Random(seed)
        hashtags = tuple(rng.sample(self.HASHTAGS, k=min(count, len(self.HASHTAGS))))
        return hashtags
    
    def generate_template_caption(self) -> str:
        """Generate template-based caption (fallback method)"""
        hook = random.choice(self.FALLBACK_HOOKS)
        
        seed = random.randint(0, 1000000)
        hashtag_count = random.randint(15, 20)
        hashtags = self._get_cached_hashtags(hashtag_count, seed)
        hashtag_text = " ".join(hashtags)
        
        caption = f"""{hook}

{hashtag_text}

Follow for more! 💯"""
        
        return caption
    
    def generate_caption(self, video_context: Optional[str] = None) -> str:
        """
        Generate caption - tries AI first, falls back to templates
        
        Args:
            video_context: Optional context about the video
            
        Returns:
            Generated caption
        """
        if self.use_ai:
            ai_caption = self.generate_ai_caption(video_context)
            if ai_caption:
                return ai_caption
            else:
                logger.warning("AI caption generation failed, using template fallback")
        
        return self.generate_template_caption()
    
    def generate_custom_caption(self, custom_hook: Optional[str] = None, 
                               custom_hashtags: Optional[List[str]] = None,
                               video_context: Optional[str] = None) -> str:
        """
        Generate custom caption with AI or templates
        
        Args:
            custom_hook: Custom opening hook
            custom_hashtags: Custom hashtag list
            video_context: Video context for AI generation
            
        Returns:
            Generated caption
        """
        # If using AI and video context provided, use AI generation
        if self.use_ai and video_context:
            ai_caption = self.generate_ai_caption(video_context)
            if ai_caption:
                return ai_caption
        
        # Otherwise use template with custom elements
        hook = custom_hook if custom_hook else random.choice(self.FALLBACK_HOOKS)
        
        if custom_hashtags:
            hashtag_text = " ".join(custom_hashtags)
        else:
            seed = random.randint(0, 1000000)
            hashtag_count = random.randint(15, 20)
            hashtags = self._get_cached_hashtags(hashtag_count, seed)
            hashtag_text = " ".join(hashtags)
        
        caption = f"""{hook}

{hashtag_text}

Follow for more! 💯"""
        
        return caption
    
    def clear_cache(self):
        """Clear LRU cache if needed"""
        self._get_cached_hashtags.cache_clear()
