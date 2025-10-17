import os
import asyncio
import logging
from datetime import datetime
from instagram_poster import InstagramPoster
from telegram_notifier import TelegramNotifier
from caption_generator import CaptionGenerator
from instagram_scraper import InstagramScraper
from video_downloader import VideoDownloader
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AutoRepostScheduler:
    def __init__(self):
        logger.info("Initializing Auto-Repost Scheduler")
        
        self.poster = None
        self.telegram = None
        self.caption_gen = CaptionGenerator()
        self.scraper = None
        self.downloader = None
        
        # Get posting interval from env (default: 3 hours = 10800 seconds)
        self.posting_interval = int(os.getenv('POSTING_INTERVAL_HOURS', '3')) * 3600
        logger.info(f"Posting interval: {self.posting_interval / 3600} hours")
        
        self.last_post_time = None
    
    async def initialize(self):
        """Initialize async components"""
        try:
            # Initialize Instagram poster
            self.poster = InstagramPoster()
            logger.info("Instagram Poster initialized in scheduler")
        except Exception as e:
            logger.error(f"Failed to initialize Instagram Poster: {e}")
            raise
        
        try:
            # Initialize Telegram notifier
            self.telegram = TelegramNotifier()
            logger.info("Telegram Notifier initialized in scheduler")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram Notifier: {e}")
            raise
        
        try:
            # Initialize Instagram scraper
            self.scraper = InstagramScraper()
            logger.info("Instagram Scraper initialized in scheduler")
        except Exception as e:
            logger.error(f"Failed to initialize Instagram Scraper: {e}")
            raise
        
        try:
            # Initialize video downloader (reuse scraper's client)
            self.downloader = VideoDownloader(instagram_client=self.scraper.client)
            logger.info("Video Downloader initialized in scheduler")
        except Exception as e:
            logger.error(f"Failed to initialize Video Downloader: {e}")
            raise
    
    async def find_and_post_viral_video(self):
        """Find a viral video from Explore, download it, and post to Instagram"""
        try:
            start_time = datetime.now()
            logger.info("=" * 60)
            logger.info(f"Starting new repost cycle at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)
            
            # Step 1: Find a viral video from Explore
            logger.info("Step 1: Fetching viral video from Instagram Explore")
            video_info = self.scraper.get_random_viral_video()
            
            if not video_info:
                error_msg = "Failed to find viral video from Explore"
                logger.error(error_msg)
                await self.telegram.send_notification(
                    f"❌ {error_msg}",
                    "error"
                )
                return
            
            video_title = f"{video_info['caption'][:50]}..." if video_info['caption'] else f"Video by @{video_info['user']['username']}"
            logger.info(f"✅ Found viral video: {video_title}")
            logger.info(f"   Author: @{video_info['user']['username']}")
            logger.info(f"   Likes: {video_info['like_count']:,}, Views: {video_info.get('view_count', 'N/A')}")
            
            # Step 2: Download video
            logger.info("Step 2: Downloading video without watermark")
            video_path = self.downloader.download_video(
                media_id=video_info['media_id'],
                video_code=video_info['code']
            )
            
            if not video_path:
                error_msg = f"Failed to download video {video_info['code']}"
                logger.error(error_msg)
                await self.telegram.send_notification(
                    f"❌ {error_msg}",
                    "error"
                )
                return
            
            video_file_info = self.downloader.get_video_info(video_path)
            logger.info(f"✅ Video downloaded: {video_file_info.get('filename', 'unknown')}")
            logger.info(f"   Size: {video_file_info.get('size_mb', 0)} MB")
            
            # Step 3: Generate AI caption
            logger.info("Step 3: Generating AI-powered caption")
            video_context = f"{video_info['caption'][:200]}" if video_info['caption'] else f"Viral video by {video_info['user']['username']}"
            caption = self.caption_gen.generate_caption(video_context=video_context)
            logger.info(f"✅ Caption generated (length: {len(caption)} chars)")
            
            # Step 4: Upload video to hosting (we need a public URL)
            # NOTE: For now, we'll skip this and just log a warning
            # In production, you'd upload to a CDN/hosting service
            logger.warning("⚠️  Video hosting not implemented - using placeholder URL")
            logger.warning("   You need to implement video hosting to get a public HTTPS URL")
            
            # For demo purposes, we'll use the downloaded video path
            # In real implementation, upload to CDN and get public URL
            video_url = os.getenv('VIDEO_URL', f'https://example.com/{video_file_info.get("filename", "video.mp4")}')
            
            # Step 5: Post to Instagram
            logger.info("Step 5: Posting video to Instagram")
            result = await self.poster.post_video(video_url, caption)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Step 6: Send detailed Telegram notification
            if result['success']:
                logger.info(f"✅ Successfully posted video in {duration:.1f} seconds")
                logger.info(f"   Media ID: {result['media_id']}")
                
                await self.telegram.send_post_report(
                    video_title=video_title,
                    video_author=f"@{video_info['user']['username']}",
                    likes=video_info['like_count'],
                    views=video_info.get('view_count', 0),
                    video_url=video_url,
                    caption=caption,
                    media_id=result['media_id'],
                    timestamp=start_time,
                    duration=duration
                )
                
                # Clean up old videos to save space
                self.downloader.cleanup_old_videos(keep_latest=5)
                
            else:
                logger.error(f"❌ Failed to post video: {result['error']}")
                await self.telegram.send_post_report(
                    video_title=video_title,
                    video_author=f"@{video_info['user']['username']}",
                    likes=video_info['like_count'],
                    views=video_info.get('view_count', 0),
                    video_url=video_url,
                    caption=caption,
                    error=result['error'],
                    timestamp=start_time,
                    duration=duration
                )
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Unexpected error in find_and_post_viral_video: {e}", exc_info=True)
            try:
                await self.telegram.send_notification(
                    f"❌ Critical error during repost cycle: {str(e)}",
                    "error"
                )
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {notify_error}")
    
    async def run_scheduler(self):
        """Async scheduler loop - posts every N hours"""
        logger.info("Starting auto-repost scheduler loop")
        logger.info(f"Will post every {self.posting_interval / 3600} hours")
        
        # Send startup notification
        try:
            await self.telegram.send_notification(
                f"🤖 Auto-Repost Bot Started\nPosting viral videos every {self.posting_interval / 3600} hours",
                "success"
            )
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
        
        while True:
            try:
                current_time = datetime.now()
                
                # Check if it's time to post
                should_post = False
                
                if self.last_post_time is None:
                    # First run - post immediately
                    should_post = True
                    logger.info("First run - posting immediately")
                else:
                    # Check if interval has passed
                    time_since_last_post = (current_time - self.last_post_time).total_seconds()
                    if time_since_last_post >= self.posting_interval:
                        should_post = True
                        logger.info(f"Interval passed ({time_since_last_post / 3600:.1f} hours) - posting now")
                
                if should_post:
                    await self.find_and_post_viral_video()
                    self.last_post_time = datetime.now()
                    
                    # Calculate next post time
                    next_post_time = self.last_post_time.timestamp() + self.posting_interval
                    next_post_datetime = datetime.fromtimestamp(next_post_time)
                    logger.info(f"Next post scheduled for: {next_post_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Sleep for 60 seconds before checking again
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    async def start(self):
        """Start async scheduler"""
        try:
            logger.info("Starting auto-repost scheduler")
            await self.initialize()
            
            # Create background task
            asyncio.create_task(self.run_scheduler())
            logger.info("Auto-repost scheduler started successfully and running in background")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.poster:
            await self.poster.close()
        if self.scraper:
            self.scraper.logout()
        logger.info("Scheduler cleanup completed")
