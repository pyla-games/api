# Vyla Game Scraper

A Flask web application that scrapes games from Vyla (koyso.com), providing a JSON-based interface to browse games, view details, and retrieve download links.

## Features

* Browse games by genre with pagination
* Search games by title or keywords
* View detailed game information (title, description, file size, version, images, videos)
* Retrieve final download links with rate limiting and cooldown protection
* Clean JSON API responses
* Dynamic single-page web interface
* Browser history support with working back button navigation

## Requirements

* Python 3.x
* Flask
* Standard libraries: `urllib`, `re`, `json`, `html`, `hashlib`, `time`, `http.cookiejar`

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install flask
```

## Usage

### Running the Server

```bash
python app.py
```

The server will start at `http://127.0.0.1:5000`

### Web Interface

Open your browser and navigate to `http://127.0.0.1:5000`

The interface provides:
* Browse all games or filter by genre
* Search functionality
* Click-through navigation to game details
* Direct download link generation
* Browser back button support

### API Endpoints

#### Get Games
```
GET /api/games?genre={genre_id}&page={page_number}&search={query}
```

Returns paginated list of games with navigation links.

#### Get Game Details
```
GET /api/game/{game_id}
```

Returns detailed information about a specific game including images, videos, and download endpoint.

#### Get Download URL
```
GET /api/download/{game_id}
```

Returns the final download URL for a game. Subject to rate limiting.

## Available Genres

1. All Games
2. Action Games
3. Adventure Games
4. R18+
5. Shooting Games
6. Casual Games
7. Sports Racing
8. Simulation Business
9. Role Playing
10. Strategy Games
11. Fighting Games
12. Horror Games
13. Real-time strategy
14. Card Game
15. Indie Games
16. LAN connection

## Configuration

The `VylaScraper` class includes configurable options:

* `request_delay` - Delay between requests (default: 0.05s)
* `download_cooldown` - Cooldown period between download requests (default: 10s)
* `secret_key` - Authentication key for download API

## Rate Limiting

The application implements:
* Per-game download cooldown (10 seconds)
* Server-side rate limit detection
* Automatic cooldown enforcement

## How It Works

1. **Scraping**: Uses `urllib` to fetch and parse HTML from koyso.com
2. **Authentication**: Generates SHA256 hashes for download requests
3. **Download Links**: Retrieves final download URLs through the site's API
4. **Frontend**: Single-page application with history state management

## Navigation

* Click any `/api/*` link to navigate
* Back button properly navigates through history
* URL query parameters maintain state (`?genre=X&page=Y`)

## Error Handling

The application handles:
* Network errors
* Rate limiting
* Download cooldowns
* Invalid responses
* Missing game data

## Disclaimer

This application interacts with a third-party website. Use responsibly and ensure compliance with the website's terms of service. Unauthorized distribution or use may be illegal.

## License

For educational purposes only.