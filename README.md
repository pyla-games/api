![Vyla Game Scraper Logo](https://vyla-games.vercel.app/static/images/github-banner.png)

# Vyla Games API

A Flask-based JSON API and zero-UI web interface for game discovery and downloads. Scrapes game data from koyso.com and serves it through clean, scraper-friendly endpoints with proxied media assets.

## Features

• **Pure JSON API** - All endpoints return clean JSON responses
• **Zero-UI Interface** - Clickable JSON navigation for human browsing
• **Unified Endpoints** - Same paths work for both API users and web browsers
• **Proxied Media** - All images and videos served through your domain
• **Direct Downloads** - Download URLs point directly to CDN (no proxying)
• **Smart Detection** - Returns JSON for scrapers, HTML for browsers
• **Genre Browsing** - 16 game categories with pagination
• **Keyword Search** - Full-text search with paged results
• **Detailed Metadata** - Title, description, images, videos, download links
• **Download Generation** - Authenticated API calls with rate-limit handling
• **Health Monitoring** - System status and connectivity checks
• **History Support** - Browser back/forward navigation works perfectly

## Requirements

• Python 3.9+
• Flask
• Standard library only (urllib, re, json, html, hashlib, time, http.cookiejar)

## Installation

```bash
git clone <repo>
cd <repo>
pip install flask
```

## Running

```bash
python app.py
```

Server runs at:

```
http://127.0.0.1:5000
```

## Web Interface

Access `/` in any browser for a zero-UI, clickable JSON interface.

Features:
• Interactive JSON navigation
• Clickable links in JSON responses
• Clean URL paths (no `/proxy/` prefix in visible URLs)
• Browser history support
• Mobile-friendly viewport

## API Endpoints

### Health Check

```
GET /api/health
```

Returns:
```json
{
  "status": "success|partial|fail",
  "checks": {
    "scraping": true,
    "connectivity": true,
    "api_responsive": true
  },
  "timestamp": 1769996310
}
```

### Available Genres

```
GET /api/genres
```

Returns all available genres with API endpoints.

### List Games

```
GET /api/games?genre={id}&page={n}
GET /api/games?search={query}&page={n}
```

Parameters:
• `genre` - Genre ID (1-16)
• `page` - Page number (starts at 1)
• `search` - Search query (optional)

Returns:
```json
{
  "status": "success",
  "genre": "Action Games",
  "page": 1,
  "has_next": true,
  "total_results": 20,
  "games": [
    {
      "title": "Game Title",
      "id": "1927",
      "image_url": "/image/app_id/screenshot.jpg",
      "view": "/api/game/1927"
    }
  ],
  "next": "/api/games?genre=2&page=2",
  "back": "/"
}
```

### Search (Path-Based)

```
GET /search/{query}?page={n}
```

Clean URL alternative for search queries.

### Game Details

```
GET /api/game/{game_id}
GET /game/{game_id}
```

Both paths return identical JSON.

Returns:
```json
{
  "title": "Game Title",
  "id": "1927",
  "full_description": "Full game description",
  "size": "800MB",
  "version": "v1.0",
  "media": {
    "images": ["/image/app_id/screenshot1.jpg"],
    "videos": ["/video/app_id/trailer.webm"]
  },
  "download_url": "/api/download/1927",
  "back": "/"
}
```

### Download URL Generation

```
GET /api/download/{game_id}
GET /game/{game_id}/download
```

Both paths work identically - unified endpoint for all users.

Returns:
```json
{
  "status": "success",
  "download_url": "https://cdn.example.com/game.7z?verify=..."
}
```

Error responses:
```json
{
  "error": "cooldown",
  "wait_seconds": 5
}
```

### Proxied Media Assets

Images and videos are automatically proxied:

```
GET /image/{path}
GET /video/{path}
```

Examples:
• `/image/3668560/capsule_616x353.jpg`
• `/video/2710480/trailer.webm`

These URLs are returned in API responses and clickable in the web interface.

## Genres

| ID | Name |
|----|------|
| 1  | All Games |
| 2  | Action Games |
| 3  | Adventure Games |
| 4  | R18+ |
| 5  | Shooting Games |
| 6  | Casual Games |
| 7  | Sports Racing |
| 8  | Simulation Business |
| 9  | Role Playing |
| 10 | Strategy Games |
| 11 | Fighting Games |
| 12 | Horror Games |
| 13 | Real-time strategy |
| 14 | Card Game |
| 15 | Indie Games |
| 16 | LAN connection |

## Configuration

Inside `VylaScraper` class:

• `base_url` - Upstream scraping target (default: `https://koyso.com`)
• `request_delay` - Delay between requests (default: 0.05s)
• `download_cooldown` - Per-game download cooldown (default: 10s)
• `secret_key` - Hash salt for download authentication
• `url_cache` - In-memory cache for proxied URLs

## How It Works

### Scraping
• Fetches HTML with browser-like headers
• Parses using regex (no external dependencies)
• Extracts game metadata, images, and videos
• Deduplicates media with format preference (WebP > AVIF > PNG > JPG)

### Download Authentication
• Generates SHA-256 hash: `timestamp + game_id + secret_key`
• Posts to `/api/getGamesDownloadUrl` endpoint
• Includes required cookies: `site_auth=1`, `key=NBQEah#h@6qHr7T!k`
• Handles 429 responses (extracts download URL from error body)

### Media Proxying
• Stores original URLs in `url_cache` dictionary
• Returns clean paths like `/image/app_id/file.jpg`
• Proxy routes look up original URL from cache
• Serves media with proper content types and caching headers

### Smart Response Format
• Detects `Accept: application/json` header
• Checks User-Agent for bot/scraper patterns
• Returns JSON for API clients
• Returns HTML interface for browsers

## Rate Limiting

• **Per-game cooldown** - 10 seconds between download requests for same game
• **Upstream rate limits** - Handled gracefully with error messages
• **429 extraction** - Parses download URL from rate-limit response body
• **Cookie-based blocking** - Respects upstream authentication

## Error Handling

All errors return clean JSON:

```json
{
  "error": "Error description"
}
```

Common errors:
• `Game not found` (404)
• `cooldown` (429) - includes `wait_seconds`
• `rate_limited` (429) - upstream API limit
• `Failed to load image/video` (404) - proxy errors
• `Access forbidden` (403) - authentication issue

## Debugging

Enable debug mode in Flask for detailed logging:

```python
if __name__ == '__main__':
    app.run(debug=True)
```

Download requests include extensive debug output:
• Timestamp and signature generation
• POST data sent to upstream
• Full API responses
• Error details and stack traces

## Architecture

```
User Request
    ↓
Flask Router
    ↓
VylaScraper
    ↓
Upstream API (koyso.com)
    ↓
JSON Response
```

**File Structure:**
• `app.py` - Flask application and scraper logic
• `templates/index.html` - Zero-UI interface
• `static/` - Favicon and assets

## Deployment

For production, use a WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or use Vercel/Railway/Render with included configuration.

## Disclaimer

This project interacts with third-party websites for educational purposes. Users are responsible for:
• Respecting robots.txt and terms of service
• Complying with copyright and intellectual property laws
• Not overwhelming upstream servers with requests
• Using responsibly and ethically

The author assumes no liability for misuse or violations.

## License

See the [LICENSE](LICENSE) file for details.