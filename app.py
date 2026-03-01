from flask import Flask, render_template, request, jsonify
import urllib.request
import urllib.parse
import re
import json
import html
import hashlib
import time
import urllib.error
from functools import wraps
import base64

app = Flask(__name__)

class VylaScraper:
    def __init__(self):
        self.base_url = "https://koyso.com"
        self.opener = urllib.request.build_opener()
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Connection', 'keep-alive'),
        ]
        self.genres = {
            '1': ('All Games', '/'),
            '2': ('Action Games', '/category/action'),
            '3': ('Adventure Games', '/category/adventure'),
            '4': ('Shooting Games', '/category/shooting'),
            '5': ('Casual Games', '/category/casual'),
            '6': ('Sports Racing', '/category/sports_racing'),
            '7': ('Simulation Business', '/category/simulation'),
            '8': ('Role Playing', '/category/rpg'),
            '9': ('Strategy Games', '/category/strategy'),
            '10': ('Fighting Games', '/category/fighting'),
            '11': ('Horror Games', '/category/horror'),
            '12': ('Real-time strategy', '/category/rts'),
            '13': ('Card Game', '/category/card'),
            '14': ('Indie Games', '/category/indie'),
            '15': ('LAN connection', '/category/lan')
        }
        self.secret_key = "f6i6@m29r3fwi^yqd"
        self.request_delay = 0.05

    def fetch_page(self, url, timeout=15):
        try:
            time.sleep(self.request_delay)
            req = urllib.request.Request(url)
            response = self.opener.open(req, timeout=timeout)
            content = response.read()
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    decoded = content.decode(encoding)
                    return decoded
                except UnicodeDecodeError:
                    continue
            return content.decode('utf-8', errors='replace')
        except Exception:
            return None

    def _extract_games_from_page(self, html_content):
        if not html_content:
            return []

        games = []
        patterns = [
            r'<a class="game_item"[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)</span>',
            r'<a[^>]*class="game[^"]*"[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)</span>',
        ]

        for pattern in patterns:
            game_item_matches = re.findall(pattern, html_content, re.DOTALL)
            if game_item_matches:
                break
        else:
            return []

        for game_url, image_url, game_title in game_item_matches:
            if not game_url or not game_title.strip():
                continue

            game_id = game_url.strip().split('/')[-1]
            if not game_id or not game_id.isdigit():
                continue

            proxied_image = self._create_proxy_url(image_url)

            games.append({
                'title': html.unescape(game_title.strip()),
                'id': game_id,
                'image_url': proxied_image,
                'view': f'/api/game/{game_id}'
            })

        return games

    def _create_proxy_url(self, original_url):
        if not original_url or not original_url.startswith('http'):
            return ''

        encoded = base64.urlsafe_b64encode(original_url.encode()).decode()
        return f'/{encoded}'

    def _has_next_page(self, html_content, current_page):
        if not html_content:
            return False

        next_page_pattern = r'<a[^>]*href="[^"]*\?page={}"[^>]*>'.format(current_page + 1)
        if re.search(next_page_pattern, html_content):
            return True

        pagination_text = re.search(r'<a>(\d+)/(\d+)</a>', html_content)
        if pagination_text:
            current, total = pagination_text.groups()
            if int(current) < int(total):
                return True

        return False

    def get_games(self, genre_id=None, search_query=None, page=1):
        if search_query:
            encoded_query = urllib.parse.quote(search_query)
            url = f"{self.base_url}/?keywords={encoded_query}" + (f"&page={page}" if page > 1 else "")
            html_content = self.fetch_page(url)
            if not html_content:
                return [], False
            games = self._extract_games_from_page(html_content)
            has_next = self._has_next_page(html_content, page)
            return games, has_next

        safe_genres = [gid for gid, (_, path) in self.genres.items() if gid != '1' and 'r18' not in path]

        if genre_id == '1' or genre_id not in self.genres:
            seen_ids = set()
            combined = []
            for gid in safe_genres:
                _, genre_url = self.genres[gid]
                url = f"{self.base_url}{genre_url}"
                html_content = self.fetch_page(url)
                if not html_content:
                    continue
                for g in self._extract_games_from_page(html_content):
                    if g['id'] not in seen_ids:
                        seen_ids.add(g['id'])
                        combined.append(g)
            page_size = 30
            start = (page - 1) * page_size
            end = start + page_size
            return combined[start:end], end < len(combined)

        _, genre_url = self.genres[genre_id]
        url = f"{self.base_url}{genre_url}" + (f"?page={page}" if page > 1 else "")
        html_content = self.fetch_page(url)
        if not html_content:
            return [], False
        return self._extract_games_from_page(html_content), self._has_next_page(html_content, page)

    def get_game_details(self, game_url):
        html_content = self.fetch_page(game_url)
        if not html_content:
            return None

        details = {}

        title_patterns = [
            r'<h1 class="content_title"[^>]*>(.*?)</h1>',
            r'<h1[^>]*>(.*?)</h1>',
            r'<title>([^<]+)</title>'
        ]

        for pattern in title_patterns:
            title_match = re.search(pattern, html_content, re.DOTALL)
            if title_match:
                title = html.unescape(re.sub(r'<[^>]*>', '', title_match.group(1)).strip())
                title = re.sub(r'\s*Free\s+Download\s*$', '', title, flags=re.IGNORECASE).strip()
                details['title'] = title
                break

        if 'title' not in details:
            details['title'] = 'Unknown Game'

        content_patterns = [
            r'<div class="content_body">(.*?)</div>',
            r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
        ]

        for pattern in content_patterns:
            content_match = re.search(pattern, html_content, re.DOTALL)
            if content_match:
                content_html = content_match.group(1)
                paragraphs = re.split(r'</p>|<p[^>]*>', content_html)
                clean_paragraphs = []
                for p in paragraphs:
                    p = re.sub(r'<[^>]*>', '', p)
                    p = re.sub(r'\s+', ' ', p).strip()
                    if p:
                        clean_paragraphs.append(p)
                details['full_description'] = html.unescape('|||'.join(clean_paragraphs))
                break

        if 'full_description' not in details:
            details['full_description'] = 'No description available'

        rec_split = re.split(r'class="recommendations', html_content, maxsplit=1)
        main_content = rec_split[0] if len(rec_split) > 1 else html_content

        all_images = re.findall(r'https?://[^\s"\'<>]+\.(?:jpg|png|gif|webp|avif|jpeg)', main_content, re.IGNORECASE)
        all_videos = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|webm)', main_content, re.IGNORECASE)

        unique_images = list(dict.fromkeys(all_images))[:30]
        seen_stems = set()
        deduped_videos = []
        for v in all_videos:
            stem = re.sub(r'\.(webm|mp4)$', '', v, flags=re.IGNORECASE)
            if stem not in seen_stems:
                seen_stems.add(stem)
                deduped_videos.append(v)
        unique_videos = deduped_videos[:10]

        details['media'] = {
            'images': [self._create_proxy_url(img) for img in unique_images],
            'videos': [self._create_proxy_url(vid) for vid in unique_videos]
        }

        size_match = re.search(r'<li>\s*<span>Size</span>\s*<span>([^<]+)</span>', html_content, re.DOTALL)
        details['size'] = size_match.group(1).strip() if size_match else 'Unknown'

        version_match = re.search(r'<li>\s*<span>Version</span>\s*<span[^>]*>([^<]+)</span>', html_content, re.DOTALL)
        details['version'] = version_match.group(1).strip() if version_match else 'Unknown'

        recommendations = []
        rec_pattern = r'<a class="recommendations_item" href="https://koyso\.com/game/(\d+)"[^>]*title="([^"]*)"'
        rec_matches = re.findall(rec_pattern, html_content)

        for rec_id, rec_title in rec_matches[:6]:
            rec_img_pattern = f'<a class="recommendations_item" href="https://koyso\\.com/game/{rec_id}".*?<img[^>]*src="([^"]+)"'
            rec_img_match = re.search(rec_img_pattern, html_content, re.DOTALL)
            rec_image = self._create_proxy_url(rec_img_match.group(1)) if rec_img_match else ''

            recommendations.append({
                'id': rec_id,
                'title': html.unescape(rec_title),
                'image_url': rec_image,
                'view': f'/api/game/{rec_id}'
            })

        if recommendations:
            details['recommendations'] = recommendations

        game_id = game_url.split('/')[-1]
        details['id'] = game_id
        details['download_url'] = f"/api/download/{game_id}"
        details['back'] = request.url_root

        return details

    def get_final_download_url(self, game_id):
        try:
            timestamp = str(int(time.time()))
            hash_input = timestamp + game_id + self.secret_key
            sign = hashlib.sha256(hash_input.encode()).hexdigest()

            download_api_url = f"{self.base_url}/api/getGamesDownloadUrl"

            post_data = {
                'id': game_id,
                'timestamp': timestamp,
                'secretKey': sign,
                'canvasId': '0'
            }

            encoded_data = urllib.parse.urlencode(post_data).encode('utf-8')
            req = urllib.request.Request(download_api_url, data=encoded_data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept', 'application/json, text/plain, */*')
            req.add_header('Referer', f'{self.base_url}/download/{game_id}')

            response = urllib.request.urlopen(req, timeout=30)
            response_data = response.read().decode('utf-8')

            try:
                json_response = json.loads(response_data)
                if isinstance(json_response, str) and json_response.startswith('http'):
                    return {"status": "success", "url": json_response}
                elif 'url' in json_response:
                    return {"status": "success", "url": json_response['url']}
                elif 'data' in json_response and 'url' in json_response['data']:
                    return {"status": "success", "url": json_response['data']['url']}
            except json.JSONDecodeError:
                if response_data and response_data.startswith('http'):
                    return {"status": "success", "url": response_data.strip()}

            return {"status": "error", "message": "No download URL found"}

        except urllib.error.HTTPError as e:
            if e.code == 429:
                return {"status": "rate_limited", "message": "Too many requests"}
            return {"status": "error", "message": f"HTTP {e.code}"}
        except Exception:
            return {"status": "error", "message": "Download service unavailable"}

scraper = VylaScraper()

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
    return response

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = app.make_response('')
        response.status_code = 204
        return response

def json_response(data, status_code=200):
    response = jsonify(data)
    response.status_code = status_code
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/<path:encoded_url>')
def proxy_media(encoded_url):
    try:
        original_url = base64.urlsafe_b64decode(encoded_url.encode()).decode()

        req = urllib.request.Request(original_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Referer', 'https://koyso.com/')
        req.add_header('Accept', 'image/webp,image/*,*/*')

        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
            content_type = response.headers.get('Content-Type', 'application/octet-stream')

            flask_response = app.make_response(content)
            flask_response.headers['Content-Type'] = content_type
            flask_response.headers['Cache-Control'] = 'public, max-age=31536000'

            return flask_response

    except Exception:
        return ('Image not available', 404)

@app.route('/api/health')
def health_check():
    try:
        test_games, _ = scraper.get_games('2', None, 1)
        return json_response({
            "status": "healthy" if len(test_games) > 0 else "degraded",
            "timestamp": int(time.time())
        })
    except Exception as e:
        return json_response({"status": "fail", "error": str(e)}, 500)

@app.route('/api/genres')
def get_genres():
    genres_list = [
        {"id": gid, "name": gname, "url": f"/api/games?genre={gid}&page=1"}
        for gid, (gname, _) in scraper.genres.items()
    ]

    return json_response({
        "api_version": "2.0",
        "total_genres": len(genres_list),
        "genres": genres_list
    })

@app.route('/')
def index():
    genres_list = [
        {"id": gid, "name": gname, "url": f"/api/games?genre={gid}&page=1"}
        for gid, (gname, _) in scraper.genres.items()
    ]

    return jsonify({
        "api_version": "2.0",
        "endpoints": {
            "health":       "/api/health",
            "genres":       "/api/genres",
            "games":        "/api/games?genre={genre_id}&page={page}",
            "search":       "/api/search?q={query}&page={page}",
            "game_details": "/api/game/{game_id}",
            "download":     "/api/download/{game_id}",
            "proxy_media":  "/{base64_encoded_url}"
        },
        "frontend": "https://vyla-games-frontend.vercel.app",
        "search": {
            "usage":   "GET /api/search?q={query}&page={page}",
            "example": "/api/search?q=minecraft&page=1",
            "note":    "Returns paginated results with has_next and next/previous links"
        },
        "available_genres": genres_list
    })

def _filter_valid_games(games):
    import concurrent.futures

    def check(game):
        try:
            url = f"https://koyso.com/game/{game['id']}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            response = urllib.request.urlopen(req, timeout=5)
            return game if response.status == 200 else None
        except:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check, games))

    return [g for g in results if g is not None]

@app.route('/api/games')
def get_games():
    genre_id = request.args.get('genre', '1')
    page = int(request.args.get('page') or 1)

    games, has_next = scraper.get_games(genre_id, None, page)
    games = _filter_valid_games(games)

    return json_response({
        'status': 'success',
        'genre': scraper.genres.get(genre_id, ('Unknown', ''))[0],
        'genre_id': genre_id,
        'total_results': len(games),
        'page': page,
        'has_next': has_next,
        'games': games,
        'previous': f'/api/games?genre={genre_id}&page={page-1}' if page > 1 else None,
        'next': f'/api/games?genre={genre_id}&page={page+1}' if has_next else None
    })

@app.route('/api/game/<game_id>')
def get_game(game_id):
    if not game_id.isdigit():
        return json_response({'error': 'Invalid game ID'}, 400)

    details = scraper.get_game_details(f"https://koyso.com/game/{game_id}")

    if details:
        return json_response(details)

    return json_response({'error': 'Game not found'}, 404)

@app.route('/api/download/<game_id>')
def get_download_url(game_id):
    if not game_id.isdigit():
        return json_response({'error': 'Invalid game ID'}, 400)

    result = scraper.get_final_download_url(game_id)

    if not result:
        return json_response({'error': 'Download service error'}, 500)

    if result.get("status") == "success":
        return json_response({
            'status': 'success',
            'download_url': result.get('url')
        })

    return json_response({
        'error': result.get('message', 'Download failed')
    }, 500)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    page = int(request.args.get('page') or 1)

    if not query:
        return json_response({'error': 'Query required'}, 400)

    games, has_next = scraper.get_games(None, query, page)
    games = _filter_valid_games(games)

    return json_response({
        'status': 'success',
        'search_query': query,
        'total_results': len(games),
        'page': page,
        'has_next': has_next,
        'games': games,
        'previous': f'/api/search?q={urllib.parse.quote(query)}&page={page-1}' if page > 1 else None,
        'next': f'/api/search?q={urllib.parse.quote(query)}&page={page+1}' if has_next else None
    })

@app.errorhandler(404)
def not_found(e):
    return json_response({'error': 'Not found'}, 404)

@app.errorhandler(500)
def internal_error(e):
    return json_response({'error': 'Internal server error'}, 500)