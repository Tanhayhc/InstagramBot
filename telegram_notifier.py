import os
import logging
from typing import Optional
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        logger.info("Initializing Telegram Notifier")
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        if not self.bot_token or not self.chat_id:
            logger.error("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env file")
            raise ValueError("Telegram credentials not configured in environment variables")
        
        try:
            self.bot = Bot(token=self.bot_token)
            logger.info("Telegram Bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram Bot: {e}")
            raise
    
    async def send_notification(self, message: str, notification_type: str = "info"):
        try:
            emoji_map = {
                'success': '✅',
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️',
                'posted': '📸',
                'zip': '📦'
            }
            
            emoji = emoji_map.get(notification_type, 'ℹ️')
            formatted_message = f"{emoji} {message}"
            
            logger.info(f"Sending Telegram notification: {notification_type}")
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=formatted_message,
                parse_mode='HTML'
            )
            logger.info(f"Telegram notification sent successfully: {notification_type}")
            
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}", exc_info=True)
            logger.error(f"Failed message: {message[:100]}...")
    
    async def send_post_report(self, 
                              video_title: Optional[str] = None,
                              video_author: Optional[str] = None,
                              likes: Optional[int] = None,
                              views: Optional[int] = None,
                              video_url: Optional[str] = None,
                              caption: Optional[str] = None, 
                              media_id: Optional[str] = None, 
                              error: Optional[str] = None,
                              timestamp: Optional[object] = None,
                              duration: Optional[float] = None):
        try:
            logger.info("Preparing enhanced post report for Telegram")
            
            if media_id:
                # Success message with full details
                time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
                duration_str = f"{duration:.1f}s" if duration else 'N/A'
                
                message = f"""
📸 <b>Instagram Post Published!</b>

🎬 <b>Video:</b> {video_title if video_title else 'N/A'}
👤 <b>Author:</b> {video_author if video_author else 'N/A'}
❤️ <b>Likes:</b> {likes:,} | 👁 <b>Views:</b> {views:,} {f'({views})' if views else ''}

📝 <b>Caption Preview:</b>
{caption[:150] if caption else 'N/A'}...

✅ <b>Status:</b> Posted Successfully
🆔 <b>Media ID:</b> {media_id}
⏰ <b>Posted At:</b> {time_str}
⚡ <b>Duration:</b> {duration_str}
"""
                logger.info(f"Post successful - Media ID: {media_id}")
            else:
                # Error message
                time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
                
                message = f"""
❌ <b>Instagram Post Failed!</b>

🎬 <b>Video:</b> {video_title if video_title else 'N/A'}
👤 <b>Author:</b> {video_author if video_author else 'N/A'}
❤️ <b>Likes:</b> {likes:,} | 👁 <b>Views:</b> {views:,} {f'({views})' if views else ''}

📝 <b>Caption Preview:</b>
{caption[:150] if caption else 'N/A'}...

❌ <b>Status:</b> Failed
🔴 <b>Error:</b> {error}
⏰ <b>Attempted At:</b> {time_str}
"""
                logger.error(f"Post failed - Error: {error}")
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("Enhanced post report sent to Telegram successfully")
            
        except Exception as e:
            logger.error(f"Error sending post report to Telegram: {e}", exc_info=True)
    
    async def send_zip_download_link(self, download_url: str):
        try:
            logger.info("Sending ZIP download link to Telegram")
            message = f"""
📦 <b>Credit Limit Reached!</b>

Your Instagram bot has been packaged and is ready for download.

<b>Download Link:</b> {download_url}

The bot will continue running but you should download the package and deploy it to your own VPS to avoid additional charges.
"""
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("ZIP download link sent to Telegram successfully")
            
        except Exception as e:
            logger.error(f"Error sending ZIP download link to Telegram: {e}", exc_info=True)
