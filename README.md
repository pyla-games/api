![Vyla Game Scraper Logo](https://vyla-games.vercel.app/static/images/github-banner.png)

# Vyla Games API

A modern Flask-based game discovery and download API. Scrapes game data from koyso.com and serves it through a responsive web interface with full JSON API support.

## Features

* **Modern Web Interface** – Responsive design with smooth layout and animations
* **Complete JSON API** – RESTful endpoints for all game data
* **Stateless Architecture** – Base64 URL encoding for serverless deployment
* **CORS Enabled** – Use the API from any frontend
* **No Rate Limits** – Instant downloads without cooldowns
* **Media Proxying** – All images and videos served through the API
* **16 Game Categories** – Action, Adventure, RPG, Horror, and more
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

## Web Interface

Access the web interface at `/` for:

* Browse games by genre
* Search games by name
* Game cards in a grid layout
* Game details modal with screenshots, videos, and descriptions
* One-click downloads
* Recommendations for similar games
* Pagination for easy navigation

## API Documentation

### Base URL

```
Production: https://vyla-games.vercel.app
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
  "games_found": 42,
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
  "total_genres": 16,
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

* `genre` – Genre ID (1-16, default: 1)
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

## Configuration

Key settings in `VylaScraper`:

```python
self.base_url = "https://koyso.com"
self.request_delay = 0.05
self.secret_key = "f6i6@m29r3fwi^yqd"
```

## Architecture

**Stateless Design:** Base64 URL encoding allows serverless deployment:

```
Original URL: https://koyso.com/image.jpg
Encoded: /aHR0cHM6Ly9rb3lzby5jb20vaW1hZ2UuanBn
```

**Workflow:**

1. Scraping – Fetch HTML from koyso.com
2. Parsing – Extract game data, images, videos
3. Encoding – Media URLs base64-encoded
4. API Response – JSON with encoded proxy URLs
5. Media Proxy – Decodes and serves content

**Download Authentication:** SHA-256 signed requests to get final download links.

## Frontend Customization

Edit `index.html` to modify:

* Colors and gradients
* API base URL
* Grid layout
* Card styling

## Deployment Options

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

## CORS & Security

* Full CORS support
* JSON content-type headers
* OPTIONS preflight handling
* Public API, no authentication required

## Error Handling

All errors return JSON:

```json
{ "error": "Error description" }
```

HTTP Status Codes: 200 (Success), 400 (Bad request), 404 (Not found), 500 (Server error)

## Example Usage

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
  });
```

### cURL

```bash
curl https://vyla-games.vercel.app/api/search?q=horror&page=1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Test locally
5. Submit a pull request

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

**Live Demo:** [https://vyla-games.vercel.app](https://vyla-games.vercel.app)
**API Status:** Check `/api/health` endpoint