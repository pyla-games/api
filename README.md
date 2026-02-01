![Vyla Game Scraper Logo](https://vyla-games.vercel.app/static/images/github-banner.png)

# Vyla Game Scraper

A Flask-based web application that scrapes and proxies game data from koyso.com, exposing a clean JSON API and a single-page web interface for browsing, searching, viewing details, and generating final download links.

## Features

• Browse games by genre with pagination
• Keyword search with paged results
• Detailed game metadata (title, description, size, version)
• Image and video extraction with deduplication and format preference
• Final download URL generation via site API emulation
• Per-game download cooldown and rate-limit handling
• Health check endpoint
• SPA routing with history/back-button support
• JSON-first API design

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

Access `/` in a browser.

Supports:
• Genre browsing
• Search
• Game detail views
• Download link generation
• Proper browser history navigation

## API Endpoints

### Health Check

```
GET /api/health
```

Returns scraper, connectivity, and API status.

### List Games

```
GET /api/games?genre={id}&page={n}&search={query}
```

### Search (Path-Based)

```
GET /search/{query}?page={n}
```

### Game Details

```
GET /api/game/{game_id}
```

Returns:
• Title
• Full description
• File size
• Version
• Images (up to 10)
• Videos (up to 5)
• Recommendations
• Download page metadata

### Download URL

```
GET /api/download/{game_id}
GET /game/{game_id}/download
```

Returns final direct download URL or cooldown/rate-limit status.

## Genres

1. All Games
2. Action
3. Adventure
4. R18+
5. Shooting
6. Casual
7. Sports / Racing
8. Simulation / Business
9. RPG
10. Strategy
11. Fighting
12. Horror
13. RTS
14. Card
15. Indie
16. LAN

## Configuration

Inside `VylaScraper`:

• `request_delay` – delay between HTTP requests (default: 0.05s)
• `download_cooldown` – per-game cooldown in seconds (default: 10s)
• `secret_key` – hash salt used for download API authentication

## Rate Limiting

• Per-game cooldown enforcement
• HTTP 429 handling
• Cookie-based temporary blocking
• Automatic wait-time responses

## How It Works

• Scrapes HTML using urllib with browser-like headers
• Parses content via regex (no external parsers)
• Emulates download API authentication using SHA-256
• Injects required cookies and headers
• Normalizes and filters media assets
• Serves everything through a SPA-friendly Flask router

## Error Handling

• Network and decode failures
• API format changes
• Rate limiting and cooldown violations
• Missing or invalid game data
• Graceful JSON error responses

## Disclaimer

This project interacts with a third-party website. Use responsibly and ensure compliance with applicable laws and the site’s terms of service. The author assumes no liability for misuse.

## License

See the [LICENSE](LICENSE) file for details.
