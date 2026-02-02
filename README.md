![Vyla Game Scraper Logo](https://vyla-games.vercel.app/static/images/github-banner.png)

# Vyla Games API

A modern Flask-based game discovery and download API. Scrapes game data from koyso.com and provides a responsive web interface with full JSON API support.

---

## Table of Contents

* [Features](#features)
* [Quick Start](#quick-start)
* [Web Interface](#web-interface)
* [API Documentation](#api-documentation)
* [Available Genres](#available-genres)
* [Configuration](#configuration)
* [Architecture](#architecture)
* [Frontend Customization](#frontend-customization)
* [Debugging](#debugging)
* [Deployment Options](#deployment-options)
* [CORS & Security](#cors--security)
* [Error Handling](#error-handling)
* [Example Usage](#example-usage)
* [Contributing](#contributing)
* [Disclaimer](#disclaimer)
* [License](#license)
* [Acknowledgments](#acknowledgments)

---

## Features

<details>
<summary>Click to expand</summary>

* Responsive web interface with modern design
* Complete RESTful JSON API
* Stateless architecture for serverless deployment
* Full CORS support
* No rate limits on downloads
* Media proxy for images and videos
* 16 game categories including Action, RPG, Horror, and more
* Full-text search with pagination
* Rich metadata including screenshots, videos, descriptions, and recommendations
* Mobile responsive

</details>

---

## Quick Start

<details>
<summary>Click to expand</summary>

### Requirements

* Python 3.9+
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

### Deploy to Vercel

1. Install Vercel CLI:

```bash
npm i -g vercel
```

2. Create `vercel.json`:

```json
{
  "version": 2,
  "builds": [
    { "src": "app_final.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "app_final.py" }
  ]
}
```

3. Deploy:

```bash
vercel --prod
```

</details>

---

## Web Interface

<details>
<summary>Click to expand</summary>

* Browse games by genre
* Search games by name
* Grid layout with cards
* Game details modal (screenshots, videos, description)
* One-click downloads
* Recommendations
* Pagination

</details>

---

## API Documentation

<details>
<summary>Click to expand</summary>

### Base URL

```
Production: https://vyla-games.vercel.app
Local: http://127.0.0.1:5000
```

### Endpoints

<details>
<summary>Health Check</summary>

```http
GET /api/health
```

**Response:**

```json
{
  "status": "healthy",
  "games_found": 42,
  "timestamp": 1738368000
}
```

</details>

<details>
<summary>List Genres</summary>

```http
GET /api/genres
```

**Response:**

```json
{
  "api_version": "2.0",
  "total_genres": 16,
  "genres": [
    { "id": "1", "name": "All Games", "url": "/api/games?genre=1&page=1" }
  ]
}
```

</details>

<details>
<summary>Browse Games</summary>

```http
GET /api/games?genre={id}&page={n}
```

**Parameters:**

* `genre` – Genre ID (1-16, default 1)
* `page` – Page number (default 1)

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
    { "title": "Game Title", "id": "1927", "image_url": "/proxy/aHR0cHM6Ly9...", "view": "/api/game/1927" }
  ],
  "previous": null,
  "next": "/api/games?genre=2&page=2"
}
```

</details>

<details>
<summary>Search Games</summary>

```http
GET /api/search?q={query}&page={n}
```

**Parameters:**

* `q` – Search query (required)
* `page` – Page number (default 1)

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

</details>

<details>
<summary>Game Details</summary>

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
  "media": { "images": ["/proxy/aHR0cHM6Ly9..."], "videos": ["/proxy/aHR0cHM6Ly9..."] },
  "recommendations": [
    { "id": "1930", "title": "Similar Game", "image_url": "/proxy/aHR0cHM6Ly9...", "view": "/api/game/1930" }
  ],
  "download_url": "/api/download/1927",
  "back": "/"
}
```

</details>

<details>
<summary>Get Download Link</summary>

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

</details>

<details>
<summary>Proxied Media</summary>

```http
GET /proxy/{base64_url}
```

* Decodes base64 URL
* Fetches media from upstream
* Returns content with proper headers and caching

</details>

</details>

---

## Available Genres

<details>
<summary>Click to expand</summary>

| ID | Genre Name          |
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

</details>

---

## Configuration

<details>
<summary>Click to expand</summary>

Key settings in `VylaScraper`:

```python
self.base_url = "https://koyso.com"
self.request_delay = 0.05
self.secret_key = "f6i6@m29r3fwi^yqd"
```

</details>

---

## Architecture

<details>
<summary>Click to expand</summary>

**Stateless Design:** Base64 URL encoding allows serverless deployment.

**Workflow:**

1. Scraping – Fetch HTML from koyso.com
2. Parsing – Extract game data, images, videos
3. Encoding – Media URLs base64-encoded
4. API Response – JSON with encoded proxy URLs
5. Media Proxy – Decodes and serves content

**Download Authentication:** SHA-256 signed requests to get final download links.

</details>

---

## Frontend Customization

<details>
<summary>Click to expand</summary>

Edit `index.html` to modify:

* Colors and gradients
* API base URL
* Grid layout
* Card styling

</details>

---

## Debugging

<details>
<summary>Click to expand</summary>

Enable debug logs:

```python
DEBUG = True
```

Logs include all HTTP requests, scraping results, proxy activity, and download authentication.

</details>

---

## Deployment Options

<details>
<summary>Click to expand</summary>

* Vercel: `vercel --prod`
* Railway: `railway up`
* Heroku: `git push heroku main`
* Docker:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install flask
CMD ["python", "app_final.py"]
```

* Traditional server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_final:app
```

</details>

---

## CORS & Security

<details>
<summary>Click to expand</summary>

* Full CORS support
* JSON content-type headers
* OPTIONS preflight handling
* Public API, no authentication required

</details>

---

## Error Handling

<details>
<summary>Click to expand</summary>

All errors return JSON:

```json
{ "error": "Error description" }
```

HTTP Status Codes: 200 (Success), 400 (Bad request), 404 (Not found), 500 (Server error)

</details>

---

## Example Usage

<details>
<summary>Click to expand</summary>

### Python

```python
import requests

response = requests.get('https://vyla-games.vercel.app/api/games?genre=2&page=1')
games = response.json()['games']

for game in games:
    print(f"{game['title']} - {game['id']}")
```

### JavaScript

```javascript
fetch('https://vyla-games.vercel.app/api/game/1927')
  .then(res => res.json())
  .then(game => {
    console.log(game.title);
    console.log(game.media.images);
  });
```

### cURL

```bash
curl https://vyla-games.vercel.app/api/search?q=horror&page=1
```

</details>

---

## Contributing

<details>
<summary>Click to expand</summary>

1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Test locally
5. Submit a pull request

</details>

---

## Disclaimer

<details>
<summary>Click to expand</summary>

* For educational purposes only
* Respect upstream site terms
* Users are responsible for copyright compliance
* No liability for misuse

</details>

---

## License

<details>
<summary>Click to expand</summary>

MIT License – See LICENSE file

</details>

---

## Acknowledgments

<details>
<summary>Click to expand</summary>

* Data sourced from koyso.com
* Built with Flask
* Deployed on Vercel

**Live Demo:** [https://vyla-games.vercel.app](https://vyla-games.vercel.app)
**API Status:** Check `/api/health` endpoint

</details>