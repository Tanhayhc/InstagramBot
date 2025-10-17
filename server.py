import os
import secrets
from flask import Flask, send_file, jsonify, request
from pathlib import Path
import logging
import asyncio
from dotenv import load_dotenv
from credit_monitor import CreditMonitor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
credit_monitor_instance = None

DOWNLOAD_TOKEN_FILE = 'download_token.txt'

def get_credit_monitor():
    global credit_monitor_instance
    if credit_monitor_instance is None:
        try:
            credit_monitor_instance = CreditMonitor()
            logger.info("Credit monitor instance created")
        except Exception as e:
            logger.error(f"Failed to create credit monitor: {e}")
    return credit_monitor_instance

def generate_download_token() -> str:
    try:
        token = secrets.token_urlsafe(32)
        with open(DOWNLOAD_TOKEN_FILE, 'w') as f:
            f.write(token)
        logger.info("Generated new download token")
        return token
    except Exception as e:
        logger.error(f"Error generating download token: {e}")
        raise

def validate_download_token(provided_token: str) -> bool:
    try:
        token_path = Path(DOWNLOAD_TOKEN_FILE)
        if not token_path.exists():
            logger.warning("Download token file does not exist")
            return False
        with open(DOWNLOAD_TOKEN_FILE, 'r') as f:
            stored_token = f.read().strip()
        is_valid = provided_token == stored_token
        logger.info(f"Download token validation: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error validating download token: {e}")
        return False

def validate_trigger_key() -> bool:
    try:
        provided_key = request.headers.get('X-Trigger-Key', '')
        expected_key = os.getenv('TRIGGER_API_KEY', '')
        
        if not expected_key:
            logger.error("TRIGGER_API_KEY not set in environment - trigger endpoint disabled")
            return False
        
        is_valid = provided_key == expected_key
        logger.info(f"Trigger key validation: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error validating trigger key: {e}")
        return False

@app.route('/')
def index():
    try:
        logger.info("Index route accessed")
        return jsonify({
            'status': 'running',
            'service': 'Instagram Automation Bot',
            'endpoints': {
                '/download-zip': 'GET with ?token=TOKEN - Download project package (secured)',
                '/trigger-package': 'POST with X-Trigger-Key header - Manually trigger packaging (secured)',
                '/health': 'Health check'
            },
            'security': 'All sensitive endpoints are protected with authentication'
        })
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/download-zip')
def download_zip():
    try:
        logger.info("Download ZIP route accessed")
        provided_token = request.args.get('token', '')
        
        if not validate_download_token(provided_token):
            logger.warning(f"Invalid download token attempt from {request.remote_addr}")
            return jsonify({'error': 'Invalid or missing download token'}), 403
        
        zip_file = 'instagram_bot_package.zip'
        zip_path = Path(zip_file)
        
        if not zip_path.exists():
            logger.error("ZIP file not found")
            return jsonify({'error': 'ZIP file not found. Package not created yet.'}), 404
        
        logger.info("Authorized ZIP download in progress")
        
        response = send_file(
            zip_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='instagram_bot_package.zip'
        )
        
        token_file = Path(DOWNLOAD_TOKEN_FILE)
        if token_file.exists():
            token_file.unlink()
            logger.info("Download token invalidated after successful download")
        
        return response
    
    except Exception as e:
        logger.error(f"Error serving ZIP file: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    try:
        logger.debug("Health check accessed")
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        logger.error(f"Error in health route: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/trigger-package', methods=['POST'])
def trigger_package():
    try:
        logger.info("Trigger package route accessed")
        
        expected_key = os.getenv('TRIGGER_API_KEY', '')
        if not expected_key:
            logger.error("TRIGGER_API_KEY not configured in environment")
            return jsonify({'error': 'Server misconfigured. TRIGGER_API_KEY must be set in .env file.'}), 500
        
        if not validate_trigger_key():
            logger.warning(f"Unauthorized trigger-package attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized. Provide valid X-Trigger-Key header.'}), 401
        
        logger.info("Valid trigger key provided, creating package")
        monitor = get_credit_monitor()
        download_token = generate_download_token()
        
        asyncio.run(monitor.handle_credit_limit_reached(download_token))
        
        replit_domain = os.getenv('REPLIT_DOMAINS', 'your-repl.replit.dev').split(',')[0]
        download_url = f"https://{replit_domain}/download-zip?token={download_token}"
        
        logger.info(f"Package created successfully, download URL: {download_url}")
        
        return jsonify({
            'success': True,
            'message': 'Project packaged successfully',
            'download_url': download_url,
            'download_token': download_token
        }), 200
    
    except Exception as e:
        logger.error(f"Error triggering package: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        port = int(os.getenv('PORT', 5000))
        logger.info(f"Starting Flask server on port {port}")
        logger.info("SECURITY: Ensure TRIGGER_API_KEY is set in .env file")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}", exc_info=True)
        raise
