![Pyla Game Scraper Logo](https://raw.githubusercontent.com/EndOverdosing/Pyla-API/refs/heads/main/static/images/banner.png)

# Pyla Games API

A modern Flask-based game discovery and download API. Scrapes game data from koyso.com and serves it through a responsive web interface with full JSON API support.

## Features

* **Modern Web Interface** – Responsive design with smooth layout and animations
* **Complete JSON API** – RESTful endpoints for all game data
* **Stateless Architecture** – Base64 URL encoding for serverless deployment
* **CORS Enabled** – Use the API from any frontend
* **No Rate Limits** – Instant downloads without cooldowns
* **Media Proxying** – All images and videos served through the API
* **15 Game Categories** – Action, Adventure, RPG, Horror, and more
* **Full-Text Search** – Find games by keyword with pagination
* **Rich Metadata** – Screenshots, videos, descriptions, recommendations
* **Mobile-Responsive** – Works on all devices

## Quick Start

### Requirements

* Python 3.9 or higher
* Flask

### Installation

```bash
git clone <repo>
cd <repo>
pip install flask
```

### Running Locally

```bash
python app_final.py
```

Server runs at `http://127.0.0.1:5000`

## Web Interface

* Browse games by genre with horizontal scrolling rows
* Search games by keyword with debounced input
* Hero carousel with auto-advancing slides and touch/swipe support
* Game cards with bookmark support
* Game detail modal with hero video/image, description, screenshots, and videos
* One-click downloads with loading state
* Recommendations grid inside game modal
* Sort games A–Z / Z–A within any view
* View All overlay per genre with pagination
* Dark/light theme toggle
* Back-to-top button
* Mobile responsive with drag-to-close modals

## API Documentation

### Base URL

```
Production: https://pyla.pages.dev
Local: http://127.0.0.1:5000
```

### Endpoints

#### Health Check

```http
GET /api/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": 1738368000
}
```

#### List Genres

```http
GET /api/genres
```

**Response:**

```json
{
  "api_version": "2.0",
  "total_genres": 56,
  "genres": [
    { "id": "1", "name": "All Games", "url": "/api/games?genre=1&page=1" }
  ]
}
```

#### Browse Games

```http
GET /api/games?genre={id}&page={n}
```

**Parameters:**

* `genre` – Genre ID (1-15, default: 1)
* `page` – Page number (default: 1)

**Response:**

```json
{
  "status": "success",
  "genre": "Action Games",
  "genre_id": "2",
  "total_results": 42,
  "page": 1,
  "has_next": true,
  "games": [
    { "title": "Game Title", "id": "1927", "image_url": "/aHR0cHM6Ly9...", "view": "/api/game/1927" }
  ],
  "previous": null,
  "next": "/api/games?genre=2&page=2"
}
```

#### Search Games

```http
GET /api/search?q={query}&page={n}
```

**Parameters:**

* `q` – Search query (required)
* `page` – Page number (default: 1)

**Response:**

```json
{
  "status": "success",
  "search_query": "minecraft",
  "total_results": 15,
  "page": 1,
  "has_next": true,
  "games": [...],
  "previous": null,
  "next": "/api/search?q=minecraft&page=2"
}
```

#### Game Details

```http
GET /api/game/{game_id}
```

**Response:**

```json
{
  "id": "1927",
  "title": "Game Title",
  "full_description": "Paragraph 1|||Paragraph 2|||Paragraph 3",
  "size": "2.5GB",
  "version": "v1.0.5",
  "media": { "images": ["/aHR0cHM6Ly9..."], "videos": ["/aHR0cHM6Ly9..."] },
  "recommendations": [
    { "id": "1930", "title": "Similar Game", "image_url": "/aHR0cHM6Ly9...", "view": "/api/game/1930" }
  ],
  "download_url": "/api/download/1927",
  "back": "/"
}
```

#### Get Download Link

```http
GET /api/download/{game_id}
```

**Response:**

```json
{
  "status": "success",
  "download_url": "https://cdn.example.com/game.7z?token=..."
}
```

**Error Response:**

```json
{
  "error": "Download service unavailable"
}
```

#### Proxied Media

```http
GET /{base64_url}
```

* Decodes base64 URL
* Fetches media from upstream
* Returns it with proper headers and caching

## Available Genres

| ID | Genre Name          |
| -- | ------------------- |
| 1  | All Games           |
| 2  | Action Games        |
| 3  | Adventure Games     |
| 4  | Shooting Games      |
| 5  | Casual Games        |
| 6  | Sports Racing       |
| 7  | Simulation Business |
| 8  | Role Playing        |
| 9  | Strategy Games      |
| 10 | Fighting Games      |
| 11 | Horror Games        |
| 12 | Real-time strategy  |
| 13 | Card Game           |
| 14 | Indie Games         |
| 15 | LAN connection      |

## Disclaimer

* For educational purposes only
* Respect upstream site terms
* Users are responsible for copyright compliance
* No liability for misuse

## License

MIT License – See LICENSE file

## Acknowledgments

* Data sourced from koyso.com
* Built with Flask
* Deployed on Vercel

**Live Demo:** https://pyla.pages.dev
**API Status:** Check `/api/health` endpoint
