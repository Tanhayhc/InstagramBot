import os
import logging
from typing import Optional, Dict
from pathlib import Path
from instagrapi import Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self, instagram_client: Optional[Client] = None):
        """
        Initialize video downloader
        
        Args:
            instagram_client: Existing Instagram client (reuses session from scraper)
        """
        logger.info("Initializing Video Downloader")
        self.client = instagram_client
        self.download_path = Path(os.getenv('VIDEO_DOWNLOAD_PATH', 'downloaded_videos'))
        
        # Create download directory if it doesn't exist
        self.download_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Download path: {self.download_path.absolute()}")
    
    def download_video(self, media_id: str, video_code: str) -> Optional[str]:
        """
        Download Instagram video without watermark
        
        Args:
            media_id: Instagram media ID
            video_code: Instagram video code (shortcode)
            
        Returns:
            Path to downloaded video file or None if failed
        """
        try:
            logger.info(f"Downloading video: {video_code} (ID: {media_id})")
            
            if not self.client:
                logger.error("Instagram client not provided")
                return None
            
            # Download video using instagrapi (downloads without watermark)
            video_path = self.client.video_download(media_id, folder=str(self.download_path))
            
            if video_path and Path(video_path).exists():
                logger.info(f"Video downloaded successfully: {video_path}")
                return str(video_path)
            else:
                logger.error(f"Failed to download video: {video_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading video {video_code}: {e}", exc_info=True)
            return None
    
    def download_video_from_url(self, video_url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download video from direct URL (fallback method)
        
        Args:
            video_url: Direct video URL
            filename: Custom filename (optional)
            
        Returns:
            Path to downloaded file or None
        """
        try:
            import httpx
            
            logger.info(f"Downloading video from URL: {video_url[:50]}...")
            
            if not filename:
                filename = f"video_{os.urandom(8).hex()}.mp4"
            
            output_path = self.download_path / filename
            
            # Download with httpx
            with httpx.stream('GET', video_url, follow_redirects=True, timeout=60.0) as response:
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            
            logger.info(f"Video downloaded from URL: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error downloading from URL: {e}", exc_info=True)
            return None
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        Get video file information
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video metadata
        """
        try:
            path = Path(video_path)
            if not path.exists():
                return {}
            
            file_size = path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            info = {
                'path': str(path.absolute()),
                'filename': path.name,
                'size_bytes': file_size,
                'size_mb': round(file_size_mb, 2),
                'exists': True
            }
            
            logger.debug(f"Video info: {info}")
            return info
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}
    
    def cleanup_old_videos(self, keep_latest: int = 5):
        """
        Clean up old downloaded videos, keeping only the latest N files
        
        Args:
            keep_latest: Number of latest videos to keep
        """
        try:
            logger.info(f"Cleaning up old videos, keeping latest {keep_latest}")
            
            # Get all video files sorted by modification time
            video_files = sorted(
                self.download_path.glob('*.mp4'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Delete old files
            deleted_count = 0
            for video_file in video_files[keep_latest:]:
                try:
                    video_file.unlink()
                    logger.debug(f"Deleted old video: {video_file.name}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {video_file.name}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old videos")
            else:
                logger.info("No old videos to clean up")
                
        except Exception as e:
            logger.error(f"Error cleaning up videos: {e}", exc_info=True)
