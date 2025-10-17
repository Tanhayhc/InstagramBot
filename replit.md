# Instagram Auto-Repost Bot

## Overview

An advanced automated Instagram bot that **automatically discovers, downloads, and reposts viral videos** from Instagram Explore every 3 hours. Features AI-powered caption generation using OpenAI GPT-5, intelligent video filtering based on engagement metrics, watermark-free video downloading, and comprehensive Telegram notifications.

**Key Upgrade (October 17, 2025):**
- Completely overhauled from static video posting to dynamic viral video discovery
- Integrated Instagram scraping to find trending content automatically
- Added OpenAI GPT-5 for AI-powered caption generation
- Implemented smart filtering based on likes, views, and engagement rate
- Enhanced Telegram notifications with detailed video statistics

## Recent Changes

**2025-10-17: Major Upgrade - Auto-Repost with Viral Video Scraping**
- **Instagram Scraper Module**: New `instagram_scraper.py` fetches viral videos from Explore page with configurable filters
- **Video Downloader Module**: New `video_downloader.py` downloads Instagram videos without watermarks using instagrapi library
- **AI Caption Generator**: Updated `caption_generator.py` to use OpenAI GPT-5 for intelligent, engaging caption creation with template fallback
- **Auto-Repost Scheduler**: Completely rewrote `scheduler.py` from timezone-based to interval-based (every 3 hours by default)
- **Enhanced Telegram Notifications**: Updated `telegram_notifier.py` to include video title, author, likes, views, timestamp, and processing duration
- **New Dependencies**: Added instagrapi (Instagram API), OpenAI SDK
- **Environment Configuration**: Added 10+ new environment variables for scraping, filtering, AI captions, and intervals

## User Preferences

Preferred communication style: Simple, everyday language.
Project scope: Automated content reposting with viral video discovery.

## System Architecture

### Core Design Pattern

The application follows a **modular service-oriented architecture** with async/await patterns for I/O operations. The new upgrade adds intelligent content discovery and AI-powered processing layers.

**Key architectural decisions:**

1. **Async-First Design** - Uses Python's asyncio for non-blocking I/O operations throughout the entire pipeline
2. **Environment-Based Configuration** - All credentials and settings stored in `.env` file for easy deployment
3. **Modular Services** - Each functional area isolated into dedicated modules for maintainability
4. **Intelligent Content Discovery** - Automated viral video scraping with configurable filtering criteria
5. **AI-Powered Content Generation** - OpenAI GPT-5 integration with graceful template-based fallback

### Backend Architecture

**Technology Stack:**
- Python 3.11 with asyncio for asynchronous operations
- Flask web server for HTTP endpoints
- Instagrapi for Instagram scraping and downloading
- OpenAI SDK for AI caption generation
- Instagram Graph API for posting
- Telegram Bot API for notifications

**Core Components:**

1. **Instagram Scraper (`instagram_scraper.py`)** - NEW
   - **Purpose**: Discovers viral videos from Instagram Explore page
   - **Features**: Session persistence, smart filtering, engagement analysis
   - **Process**: Login → Fetch Explore → Filter by virality → Return top videos
   - **Filters**: Minimum likes, views, engagement rate (all configurable)

2. **Video Downloader (`video_downloader.py`)** - NEW
   - **Purpose**: Downloads Instagram videos without watermarks
   - **Method**: Uses instagrapi's built-in download functionality
   - **Features**: File info extraction, automatic cleanup of old videos
   - **Storage**: Configurable download path (default: `downloaded_videos/`)

3. **Caption Generator (`caption_generator.py`)** - UPGRADED
   - **Old**: Template-based random caption generation
   - **New**: OpenAI GPT-5 AI-powered caption generation
   - **Features**: 
     - Context-aware captions based on video content
     - Viral hook generation with emojis
     - 15-20 trending hashtags
     - Call-to-action optimization
   - **Fallback**: Templates used if OpenAI API fails or is disabled

4. **Auto-Repost Scheduler (`scheduler.py`)** - COMPLETELY REWRITTEN
   - **Old**: Timezone-based daily posting (4 times/day at specific times)
   - **New**: Interval-based automatic reposting (every N hours)
   - **Process Flow**:
     1. Find viral video from Explore
     2. Download video without watermark
     3. Generate AI-powered caption
     4. Post to Instagram
     5. Send detailed Telegram report
     6. Wait for next interval
   - **Default Interval**: 3 hours (configurable via `POSTING_INTERVAL_HOURS`)

5. **Instagram Poster (`instagram_poster.py`)** - UNCHANGED
   - **Process**: Create container → Poll status → Publish
   - **Features**: Async with HTTP/2, connection pooling
   - **Error Handling**: Comprehensive timeout and retry logic

6. **Telegram Notifier (`telegram_notifier.py`)** - ENHANCED
   - **Old**: Basic success/failure notifications
   - **New**: Detailed reports with:
     - Video title and original author
     - Likes and views statistics
     - Caption preview
     - Media ID
     - Timestamp and processing duration
   - **All operations async** to prevent blocking

### Data Flow

**New Auto-Repost Flow:**
1. **Scheduler** triggers every N hours
2. **Instagram Scraper** fetches and filters viral videos from Explore
3. **Video Downloader** downloads selected video without watermark
4. **Caption Generator** creates AI-powered caption using OpenAI GPT-5
5. **Instagram Poster** uploads and publishes to Instagram Business account
6. **Telegram Notifier** sends comprehensive success/failure report

### Error Handling Strategy

**Principles:**
- Try/except blocks around all external API calls (Instagram, OpenAI, Telegram)
- Comprehensive logging at INFO level for tracking
- Graceful degradation (continues on non-critical failures)
- Fallback mechanisms (templates if OpenAI fails)
- Automatic session recovery for Instagram scraper

## External Dependencies

### Third-Party APIs

1. **Instagram Graph API (v21.0)** - For Posting
   - **Purpose**: Post videos to Instagram Business account
   - **Authentication**: Long-lived access token (60-day validity)
   - **Required Permissions**: `instagram_basic`, `instagram_content_publish`

2. **Instagrapi Library** - For Scraping & Downloading - NEW
   - **Purpose**: Scrape Explore page and download videos
   - **Authentication**: Regular Instagram username/password
   - **Features**: Session persistence, watermark-free downloads
   - **Note**: Separate from posting account (can be different account)

3. **OpenAI API (GPT-5)** - For AI Captions - NEW
   - **Purpose**: Generate engaging, viral captions
   - **Model**: gpt-5 (latest model as of August 2025)
   - **Authentication**: API key from OpenAI dashboard
   - **Fallback**: Template-based generation if API fails

4. **Telegram Bot API**
   - **Purpose**: Send detailed notifications
   - **Authentication**: Bot token from @BotFather
   - **Library**: python-telegram-bot v22.5

### External Services

1. **Video Hosting** - REQUIRED
   - **Requirement**: Public HTTPS URL for video hosting
   - **Note**: Videos are downloaded locally but need to be uploaded to CDN/cloud storage
   - **Recommended**: AWS S3, Cloudinary, Google Cloud Storage, Azure
   - **Why**: Instagram Graph API requires publicly accessible video URLs

2. **Environment Configuration**
   - **New Required Variables**:
     - `INSTAGRAM_SCRAPER_USERNAME` - Instagram account for scraping
     - `INSTAGRAM_SCRAPER_PASSWORD` - Password for scraper account
     - `OPENAI_API_KEY` - OpenAI API key for GPT-5
     - `POSTING_INTERVAL_HOURS` - Hours between posts (default: 3)
     - `MIN_LIKES`, `MIN_VIEWS`, `MIN_ENGAGEMENT_RATE` - Viral filters
     - `VIDEO_DOWNLOAD_PATH` - Where to save downloaded videos

### Python Packages

**New Dependencies:**
- `instagrapi==2.1.5` - Instagram private API for scraping and downloading
- `openai==2.4.0` - OpenAI SDK for GPT-5 caption generation
- `moviepy==1.0.3` - Video processing (dependency of instagrapi)
- `pydantic==2.11.5` - Data validation (dependency of instagrapi)

**Existing Dependencies:**
- `httpx==0.28.1` - Async HTTP client with HTTP/2 support
- `python-telegram-bot==22.5` - Telegram Bot API wrapper
- `python-dotenv==1.1.1` - Environment variable management
- `flask==3.1.2` - Web server for endpoints
- `requests==2.32.5` - HTTP client for Instagram Graph API

### Deployment Considerations

**Current Platform**: Replit
- Auto-restart on code changes
- Credit monitoring with auto-backup
- Environment variable management

**VPS Migration**: Portable to any VPS/cloud
- Requires Python 3.11+
- All dependencies in requirements.txt
- Systemd or supervisor for process management

## Configuration Guide

### Minimal Setup

1. **Instagram Accounts** (2 accounts):
   - Business account (for posting) - linked to Facebook Page
   - Regular account (for scraping) - any account, can be same or different

2. **API Keys**:
   - Instagram Graph API token (from Facebook Developer)
   - OpenAI API key (from OpenAI dashboard)
   - Telegram bot token (from @BotFather)

3. **Video Hosting**:
   - Set up CDN/cloud storage
   - Get public HTTPS URL endpoint

4. **Environment Variables**:
   - Copy `.env.example` to `.env`
   - Fill in all required credentials
   - Adjust filters and intervals as needed

### Recommended Settings

- `POSTING_INTERVAL_HOURS=3` - Safe interval, won't trigger rate limits
- `MIN_LIKES=10000` - Good threshold for viral content
- `MIN_VIEWS=50000` - Ensures popular videos
- `MIN_ENGAGEMENT_RATE=0.05` - 5% engagement is viral
- `EXPLORE_FETCH_COUNT=50` - Sufficient variety
- `USE_AI_CAPTIONS=true` - Enable AI for best results

## Operational Notes

### Performance
- Scraping takes 5-10 seconds
- Downloading takes 2-5 seconds per video
- AI caption generation takes 2-3 seconds
- Total cycle time: ~15-30 seconds per post

### Storage
- Downloaded videos stored in `downloaded_videos/`
- Auto-cleanup keeps only 5 most recent videos
- Typical video size: 5-20 MB

### Monitoring
- Check Telegram for detailed reports
- Review logs for any errors
- Monitor OpenAI API usage and billing

### Safety
- Respects Instagram rate limits
- 3-hour interval is conservative and safe
- Session persistence reduces login frequency
- Comprehensive error handling prevents crashes
