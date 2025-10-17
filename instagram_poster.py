import os
import asyncio
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import httpx

load_dotenv()

logger = logging.getLogger(__name__)

class InstagramPoster:
    def __init__(self):
        logger.info("Initializing Instagram Poster with HTTP connection pooling")
        self.access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.ig_user_id = os.getenv('INSTAGRAM_USER_ID')
        self.graph_api_version = os.getenv('GRAPH_API_VERSION', 'v21.0')
        self.base_url = f"https://graph.facebook.com/{self.graph_api_version}"
        
        if not self.access_token or not self.ig_user_id:
            logger.error("INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID must be set in .env file")
            raise ValueError("Instagram credentials not configured")
        
        # Create persistent HTTP client with connection pooling for speed
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            http2=True  # Enable HTTP/2 for faster requests
        )
        
        logger.info(f"Instagram Poster initialized with HTTP/2 and connection pooling")
        
    async def create_video_container(self, video_url: str, caption: str) -> Optional[str]:
        try:
            logger.info(f"Creating video container for URL: {video_url[:50]}...")
            endpoint = f"{self.base_url}/{self.ig_user_id}/media"
            params = {
                'access_token': self.access_token,
                'video_url': video_url,
                'media_type': 'REELS',
                'caption': caption,
                'share_to_feed': 'true'
            }
            
            response = await self.client.post(endpoint, params=params)
            response.raise_for_status()
            
            container_id = response.json().get('id')
            logger.info(f"Video container created successfully: {container_id}")
            return container_id
            
        except httpx.TimeoutException:
            logger.error("Timeout while creating video container")
            return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating video container: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating video container: {e}", exc_info=True)
            return None
    
    async def check_container_status(self, container_id: str) -> str:
        try:
            endpoint = f"{self.base_url}/{container_id}"
            params = {
                'fields': 'status_code',
                'access_token': self.access_token
            }
            
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            
            status = response.json().get('status_code', 'UNKNOWN')
            logger.debug(f"Container {container_id} status: {status}")
            return status
            
        except httpx.TimeoutException:
            logger.error("Timeout while checking container status")
            return 'ERROR'
        except httpx.HTTPError as e:
            logger.error(f"HTTP error checking container status: {e}")
            return 'ERROR'
        except Exception as e:
            logger.error(f"Unexpected error checking container status: {e}", exc_info=True)
            return 'ERROR'
    
    async def publish_container(self, container_id: str) -> Optional[str]:
        try:
            logger.info(f"Publishing container: {container_id}")
            endpoint = f"{self.base_url}/{self.ig_user_id}/media_publish"
            params = {
                'access_token': self.access_token,
                'creation_id': container_id
            }
            
            response = await self.client.post(endpoint, params=params)
            response.raise_for_status()
            
            media_id = response.json().get('id')
            logger.info(f"Video published successfully with media ID: {media_id}")
            return media_id
            
        except httpx.TimeoutException:
            logger.error("Timeout while publishing container")
            return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error publishing container: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error publishing container: {e}", exc_info=True)
            return None
    
    async def post_video(self, video_url: str, caption: str, max_wait_time: int = 600) -> Dict[str, Any]:
        result = {
            'success': False,
            'media_id': None,
            'error': None
        }
        
        try:
            logger.info("Starting async video post process")
            logger.info(f"Video URL: {video_url[:50]}...")
            logger.info(f"Caption length: {len(caption)} characters")
            
            container_id = await self.create_video_container(video_url, caption)
            if not container_id:
                result['error'] = 'Failed to create video container'
                logger.error(result['error'])
                return result
            
            start_time = asyncio.get_event_loop().time()
            check_interval = 5  # Check every 5 seconds for faster response
            
            while asyncio.get_event_loop().time() - start_time < max_wait_time:
                status = await self.check_container_status(container_id)
                
                if status == 'FINISHED':
                    logger.info("Container processing finished, attempting to publish")
                    media_id = await self.publish_container(container_id)
                    if media_id:
                        result['success'] = True
                        result['media_id'] = media_id
                        logger.info(f"Post completed successfully: {media_id}")
                        return result
                    else:
                        result['error'] = 'Failed to publish container'
                        logger.error(result['error'])
                        return result
                
                elif status == 'ERROR':
                    result['error'] = 'Container processing error'
                    logger.error(result['error'])
                    return result
                
                logger.info(f"Container status: {status}. Waiting {check_interval}s...")
                await asyncio.sleep(check_interval)
            
            result['error'] = 'Container processing timeout'
            logger.error(f"Container processing exceeded {max_wait_time} seconds")
            return result
        
        except Exception as e:
            result['error'] = f'Unexpected error in post_video: {str(e)}'
            logger.error(result['error'], exc_info=True)
            return result
    
    async def close(self):
        """Close HTTP client connection pool"""
        await self.client.aclose()
        logger.info("Instagram Poster HTTP client closed")
