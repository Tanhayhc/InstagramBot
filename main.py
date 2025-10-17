import os
import asyncio
import logging
from dotenv import load_dotenv
from scheduler import AutoRepostScheduler
from credit_monitor import CreditMonitor
from telegram_notifier import TelegramNotifier

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("🚀 Starting Instagram Auto-Repost Bot with Viral Video Scraping...")
        logger.info("Loading environment variables from .env file")
        
        required_vars = [
            'INSTAGRAM_ACCESS_TOKEN',
            'INSTAGRAM_USER_ID',
            'INSTAGRAM_SCRAPER_USERNAME',
            'INSTAGRAM_SCRAPER_PASSWORD',
            'OPENAI_API_KEY',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHAT_ID',
            'TRIGGER_API_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please configure .env file with all required variables")
            return
        
        logger.info("✅ All required environment variables loaded successfully")
        
        # Initialize components concurrently for faster startup
        telegram = None
        try:
            telegram = TelegramNotifier()
            await telegram.send_notification("🚀 Instagram Auto-Repost Bot Started", "success")
            logger.info("✅ Telegram notifier initialized and test notification sent")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram notifier: {e}")
            logger.warning("Bot will continue but notifications will not be sent")
        
        # Start credit monitor and scheduler concurrently
        tasks = []
        
        try:
            credit_monitor = CreditMonitor()
            tasks.append(credit_monitor.start_monitoring())
            logger.info("✅ Credit monitor started")
        except Exception as e:
            logger.error(f"Failed to start credit monitor: {e}")
            logger.warning("Bot will continue without credit monitoring")
        
        try:
            scheduler = AutoRepostScheduler()
            await scheduler.start()
            logger.info("✅ Auto-Repost scheduler started successfully")
            logger.info(f"   Will automatically find and repost viral videos every {os.getenv('POSTING_INTERVAL_HOURS', '3')} hours")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            logger.error("Bot cannot continue without scheduler")
            if telegram:
                await telegram.send_notification(f"❌ Failed to start scheduler: {e}", "error")
            return
        
        logger.info("⚡ Bot running and scraping viral videos. Press Ctrl+C to stop.")
        
        # Run all background tasks concurrently
        try:
            await asyncio.gather(*tasks, asyncio.sleep(float('inf')))
        except KeyboardInterrupt:
            logger.info("Shutting down bot...")
            if telegram:
                await telegram.send_notification("🛑 Instagram Auto-Repost Bot Stopped", "info")
            
            # Cleanup
            try:
                await scheduler.cleanup()
            except:
                pass
    
    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
