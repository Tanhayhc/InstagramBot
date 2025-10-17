import os
import logging
import random
from typing import List, Dict, Optional
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class InstagramScraper:
    def __init__(self):
        logger.info("Initializing Instagram Scraper")
        self.username = os.getenv('INSTAGRAM_SCRAPER_USERNAME', '')
        self.password = os.getenv('INSTAGRAM_SCRAPER_PASSWORD', '')
        self.session_file = os.getenv('INSTAGRAM_SESSION_FILE', 'instagram_session.json')
        
        if not self.username or not self.password:
            logger.error("INSTAGRAM_SCRAPER_USERNAME and INSTAGRAM_SCRAPER_PASSWORD must be set")
            raise ValueError("Instagram scraper credentials not configured")
        
        self.client = Client()
        self.client.delay_range = [2, 5]
        
        # Load or create session
        self._login()
        logger.info("Instagram Scraper initialized successfully")
    
    def _login(self):
        """Login to Instagram with session persistence"""
        try:
            session_path = Path(self.session_file)
            
            # Try to load existing session
            if session_path.exists():
                logger.info("Loading existing Instagram session")
                try:
                    self.client.load_settings(session_path)
                    self.client.login(self.username, self.password)
                    logger.info("Successfully loaded existing session")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load session: {e}. Creating new session...")
            
            # Create new session
            logger.info("Creating new Instagram session")
            self.client.login(self.username, self.password)
            self.client.dump_settings(session_path)
            logger.info("New session created and saved")
            
        except LoginRequired as e:
            logger.error(f"Login required: {e}")
            raise
        except PleaseWaitFewMinutes as e:
            logger.error(f"Rate limited: {e}")
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}", exc_info=True)
            raise
    
    def get_explore_videos(self, count: int = 50) -> List[Dict]:
        """
        Fetch video posts from Instagram Explore page
        
        Args:
            count: Number of posts to fetch (default: 50)
            
        Returns:
            List of video post dictionaries with metadata
        """
        try:
            logger.info(f"Fetching {count} videos from Explore page")
            
            # Get explore medias
            medias = self.client.get_explore_media(count)
            
            # Filter for video posts (Reels and Videos)
            video_posts = []
            for media in medias:
                if media.media_type in [2, 8]:  # 2 = Video, 8 = Album with video
                    video_info = {
                        'media_id': media.pk,
                        'code': media.code,
                        'video_url': media.video_url if hasattr(media, 'video_url') else None,
                        'thumbnail_url': media.thumbnail_url,
                        'caption': media.caption_text if media.caption_text else '',
                        'like_count': media.like_count,
                        'view_count': media.view_count if hasattr(media, 'view_count') else 0,
                        'comment_count': media.comment_count,
                        'taken_at': media.taken_at,
                        'user': {
                            'username': media.user.username,
                            'full_name': media.user.full_name,
                            'is_verified': media.user.is_verified
                        }
                    }
                    video_posts.append(video_info)
            
            logger.info(f"Found {len(video_posts)} video posts from Explore")
            return video_posts
            
        except Exception as e:
            logger.error(f"Error fetching explore videos: {e}", exc_info=True)
            return []
    
    def filter_viral_videos(self, videos: List[Dict], 
                           min_likes: Optional[int] = None,
                           min_views: Optional[int] = None,
                           min_engagement_rate: Optional[float] = None) -> List[Dict]:
        """
        Filter videos based on virality criteria
        
        Args:
            videos: List of video dictionaries
            min_likes: Minimum number of likes (from env or default)
            min_views: Minimum number of views (from env or default)
            min_engagement_rate: Minimum engagement rate (from env or default)
            
        Returns:
            Filtered list of viral videos sorted by engagement
        """
        try:
            # Load filters from environment with defaults
            min_likes = min_likes or int(os.getenv('MIN_LIKES', '10000'))
            min_views = min_views or int(os.getenv('MIN_VIEWS', '50000'))
            min_engagement_rate = min_engagement_rate or float(os.getenv('MIN_ENGAGEMENT_RATE', '0.05'))
            
            logger.info(f"Filtering videos: min_likes={min_likes}, min_views={min_views}, engagement_rate={min_engagement_rate}")
            
            viral_videos = []
            for video in videos:
                likes = video.get('like_count', 0)
                views = video.get('view_count', 0)
                comments = video.get('comment_count', 0)
                
                # Calculate engagement rate
                if views > 0:
                    engagement_rate = (likes + comments) / views
                else:
                    engagement_rate = 0
                
                # Apply filters
                if likes >= min_likes and views >= min_views and engagement_rate >= min_engagement_rate:
                    video['engagement_rate'] = engagement_rate
                    viral_videos.append(video)
            
            # Sort by engagement rate (highest first)
            viral_videos.sort(key=lambda x: x['engagement_rate'], reverse=True)
            
            logger.info(f"Found {len(viral_videos)} viral videos after filtering")
            return viral_videos
            
        except Exception as e:
            logger.error(f"Error filtering viral videos: {e}", exc_info=True)
            return videos
    
    def get_random_viral_video(self) -> Optional[Dict]:
        """
        Get a random viral video from Explore page
        
        Returns:
            Dictionary with video information or None
        """
        try:
            # Fetch explore videos
            explore_count = int(os.getenv('EXPLORE_FETCH_COUNT', '50'))
            videos = self.get_explore_videos(count=explore_count)
            
            if not videos:
                logger.warning("No videos found in Explore")
                return None
            
            # Filter for viral videos
            viral_videos = self.filter_viral_videos(videos)
            
            if not viral_videos:
                logger.warning("No viral videos found after filtering")
                # Fallback to any video if no viral ones found
                viral_videos = videos[:10]  # Take top 10 from explore
            
            # Select random from top viral videos
            selected = random.choice(viral_videos[:5])  # Choose from top 5
            logger.info(f"Selected video: {selected['code']} by @{selected['user']['username']}")
            logger.info(f"Stats - Likes: {selected['like_count']}, Views: {selected.get('view_count', 'N/A')}")
            
            return selected
            
        except Exception as e:
            logger.error(f"Error getting random viral video: {e}", exc_info=True)
            return None
    
    def logout(self):
        """Logout and cleanup"""
        try:
            logger.info("Logging out from Instagram")
            self.client.logout()
        except Exception as e:
            logger.error(f"Error during logout: {e}")
