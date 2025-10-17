import os
import asyncio
import logging
import zipfile
from pathlib import Path
from typing import Optional
from telegram_notifier import TelegramNotifier
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class CreditMonitor:
    def __init__(self):
        logger.info("Initializing Credit Monitor")
        self.credit_limit = float(os.getenv('CREDIT_LIMIT', '3.0'))
        self.check_interval = int(os.getenv('CREDIT_CHECK_INTERVAL', '3600'))
        
        try:
            self.telegram = TelegramNotifier()
            logger.info("Telegram notifier initialized in credit monitor")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram in credit monitor: {e}")
            self.telegram = None
        
        self.zip_created = False
        logger.info(f"Credit Monitor initialized with limit: ${self.credit_limit}, check interval: {self.check_interval}s")
    
    async def get_replit_credit_usage(self) -> float:
        try:
            manual_trigger = os.getenv('TRIGGER_ZIP_CREATION', 'false').lower() == 'true'
            if manual_trigger:
                logger.info("Manual ZIP creation trigger detected in environment")
                return self.credit_limit
            
            logger.debug("No manual trigger, returning 0.0 usage")
            return 0.0
        except Exception as e:
            logger.error(f"Error getting credit usage: {e}", exc_info=True)
            return 0.0
    
    def create_project_zip(self) -> Optional[str]:
        try:
            logger.info("Starting project ZIP creation")
            zip_filename = 'instagram_bot_package.zip'
            zip_path = Path(zip_filename)
            
            if zip_path.exists():
                logger.info("Removing existing ZIP file")
                zip_path.unlink()
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                excluded_dirs = {'.pythonlibs', '__pycache__', '.git', 'node_modules', '.venv'}
                excluded_files = {
                    'instagram_bot_package.zip',
                    '.env',
                    '.env.local',
                    '.env.production',
                    'download_token.txt'
                }
                
                files_added = 0
                for root, dirs, files in os.walk('.'):
                    dirs[:] = [d for d in dirs if d not in excluded_dirs]
                    
                    for file in files:
                        if file not in excluded_files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, '.')
                            zipf.write(file_path, arcname)
                            logger.debug(f"Added to ZIP: {arcname}")
                            files_added += 1
            
            logger.info(f"Project ZIP created successfully: {zip_filename} ({files_added} files)")
            logger.info(f"SECURITY: .env and sensitive files excluded from ZIP")
            return zip_filename
            
        except Exception as e:
            logger.error(f"Error creating ZIP: {e}", exc_info=True)
            return None
    
    def generate_download_token(self) -> str:
        try:
            import secrets
            token = secrets.token_urlsafe(32)
            token_file = 'download_token.txt'
            with open(token_file, 'w') as f:
                f.write(token)
            logger.info("Generated download token for automatic trigger")
            return token
        except Exception as e:
            logger.error(f"Error generating download token: {e}", exc_info=True)
            raise
    
    async def handle_credit_limit_reached(self, download_token: Optional[str] = None):
        try:
            if self.zip_created:
                logger.info("ZIP already created, skipping")
                return
            
            logger.warning("Credit limit reached! Creating project package...")
            
            if self.telegram:
                await self.telegram.send_notification(
                    "⚠️ Credit limit reached! Packaging project...",
                    "warning"
                )
            
            zip_file = self.create_project_zip()
            
            if zip_file:
                replit_domain = os.getenv('REPLIT_DOMAINS', 'your-repl.replit.dev').split(',')[0]
                
                if not download_token:
                    download_token = self.generate_download_token()
                    logger.info("Auto-generated download token for credit limit trigger")
                
                download_url = f"https://{replit_domain}/download-zip?token={download_token}"
                
                if self.telegram:
                    await self.telegram.send_zip_download_link(download_url)
                
                self.zip_created = True
                logger.info(f"ZIP package ready for download at: {download_url}")
            else:
                logger.error("Failed to create project package")
                if self.telegram:
                    await self.telegram.send_notification(
                        "❌ Failed to create project package",
                        "error"
                    )
        
        except Exception as e:
            logger.error(f"Error handling credit limit: {e}", exc_info=True)
    
    async def monitor_credits(self):
        logger.info("Starting credit monitoring loop")
        while True:
            try:
                current_usage = await self.get_replit_credit_usage()
                logger.debug(f"Current credit usage: ${current_usage:.2f}")
                
                if current_usage >= self.credit_limit:
                    logger.warning(f"Credit limit reached: ${current_usage:.2f} >= ${self.credit_limit}")
                    await self.handle_credit_limit_reached()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in credit monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def start_monitoring(self):
        try:
            asyncio.create_task(self.monitor_credits())
            logger.info(f"Credit monitoring started (limit: ${self.credit_limit}, interval: {self.check_interval}s)")
        except Exception as e:
            logger.error(f"Failed to start credit monitoring: {e}", exc_info=True)
            raise
