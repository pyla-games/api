![Vyla Game Scraper Logo](https://vyla-games.vercel.app/static/images/github-banner.png)

# Vyla Games API

A Flask-based JSON API and zero-UI web interface for game discovery and downloads. Scrapes game data from koyso.com and serves it through scraper-friendly endpoints with proxied media assets.

## Features

* **Pure JSON API** – All endpoints return clean JSON responses.
* **Zero-UI Interface** – Clickable JSON navigation for browsers.
* **Unified Endpoints** – Same paths work for both API users and web browsers.
* **Proxied Media** – Images and videos served via `/image/` and `/video/` paths.
* **Direct Downloads** – `/api/download/{game_id}` generates real download URLs with cooldown handling.
* **Smart Detection** – Returns JSON for scrapers, HTML for browsers.
* **Genre Browsing** – 16 game categories with pagination.
* **Keyword Search** – Full-text search with page navigation.
* **Detailed Metadata** – Title, description, size, version, images, videos, and recommendations.
* **Download Generation** – Authenticated API calls with SHA-256 hashing and cooldowns.
* **Health Monitoring** – System status and connectivity checks.
* **History Support** – Browser back/forward navigation works.

## Requirements

* Python 3.9+
* Flask
* Standard library only (`urllib`, `re`, `json`, `html`, `hashlib`, `time`, `http.cookiejar`)

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

Access `/` in a browser for a zero-UI interface:

* Interactive JSON navigation.
* Clickable links in JSON responses.
* Browser history support.
* Mobile-friendly viewport.

## API Endpoints

### Health Check

```
GET /api/health
```

Returns:

```json
{
  "status": "healthy|degraded|fail",
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

Returns all genres with metadata and endpoints.

### List Games

```
GET /api/games?genre={id}&page={n}
GET /api/games?search={query}&page={n}
```

Parameters:

* `genre` – Genre ID (1–16).
* `search` – Optional search query.
* `page` – Page number (starts at 1).

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
  "previous": null,
  "back": "/"
}
```

### Search (Path-Based)

```
GET /search/{query}?page={n}
```

Alternative clean URL for searches; same response as `?search=` query.

### Game Details

```
GET /api/game/{game_id}
GET /game/{game_id}
```

Both return identical JSON.

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
  "recommendations": [
    {
      "id": "1930",
      "title": "Related Game",
      "image_url": "/image/1930/screenshot.jpg",
      "view": "/api/game/1930"
    }
  ],
  "download_url": "/api/download/1927",
  "back": "/"
}
```

### Download URL Generation

```
GET /api/download/{game_id}
GET /game/{game_id}/download
```

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
  "wait_seconds": 5,
  "back": "/"
}
```

* **Cooldown** – 10 seconds per game between download requests.
* **Rate-limited** – Handles upstream 429 errors.
* **Unified** – Both paths work identically.

### Proxied Media

```
GET /image/{path}
GET /video/{path}
```

* Proxies all images/videos from upstream.
* Returns proper content type and caching headers.
* URLs match those in API responses.

## Genres

| ID | Name                |
| -- | ------------------- |
| 1  | All Games           |
| 2  | Action Games        |
| 3  | Adventure Games     |
| 4  | R18+                |
| 5  | Shooting Games      |
| 6  | Casual Games        |
| 7  | Sports Racing       |
| 8  | Simulation Business |
| 9  | Role Playing        |
| 10 | Strategy Games      |
| 11 | Fighting Games      |
| 12 | Horror Games        |
| 13 | Real-time strategy  |
| 14 | Card Game           |
| 15 | Indie Games         |
| 16 | LAN connection      |

## Configuration

Inside `VylaScraper` class:

* `base_url` – Upstream site (`https://koyso.com`).
* `request_delay` – Delay between requests (default 0.05s).
* `download_cooldown` – Per-game cooldown (default 10s).
* `secret_key` – SHA-256 hash salt for download URL generation.
* `url_cache` – Stores proxied URLs in memory.

## How It Works

### Scraping

* Fetches HTML with browser-like headers.
* Extracts game metadata, images, and videos using regex.
* Deduplicates media with format preference: `.webp > .avif > .png > .jpg > .jpeg > .gif`.

### Download Authentication

* Generates SHA-256 hash: `timestamp + game_id + secret_key`.
* POSTs to `/api/getGamesDownloadUrl` upstream.
* Includes cookies `site_auth=1; key=NBQEah#h@6qHr7T!k`.
* Handles cooldowns and rate-limited responses.

### Media Proxying

* `/image/` and `/video/` paths map to original URLs via `url_cache`.
* Sets `Content-Type`, caching headers, and CORS (`*`) for cross-site use.

### Smart Response Format

* Detects `Accept: application/json` header.
* Returns JSON for scrapers, HTML for browsers.

## Error Handling

All errors return JSON:

```json
{
  "error": "Description",
  "back": "/"
}
```

Common errors:

* `Game not found` – 404
* `cooldown` – 429, includes `wait_seconds`
* `rate_limited` – 429 upstream
* Proxy errors – 500

## Debugging

Enable debug mode:

```python
if __name__ == '__main__':
    app.run(debug=True)
```

Includes:

* Timestamp and signature logs
* Upstream POST data and responses
* Stack traces for errors

## Architecture

```
User Request
    ↓
Flask Router
    ↓
VylaScraper
    ↓
Upstream (koyso.com)
    ↓
JSON Response
```

**File Structure**

* `app.py` – Flask application and scraper logic
* `templates/index.html` – Zero-UI interface
* `static/` – Assets

## Deployment

Use a WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or deploy via Vercel/Railway/Render.

## Disclaimer

* Educational use only.
* Respect upstream `robots.txt` and terms.
* Users responsible for copyright compliance and server load.
* Author not liable for misuse.

## License

See [LICENSE](LICENSE).