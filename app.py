from flask import Flask, render_template, request, jsonify, send_from_directory
import urllib.request
import urllib.parse
import re
import json
import html
import hashlib
import time
import urllib.error
from functools import wraps
import os
import http.cookiejar

app = Flask(__name__)

DEBUG = True

def debug_log(msg, *args):
    if DEBUG:
        print(f"[VYLA-BACKEND] {msg}", *args)

class VylaScraper:
    def __init__(self):
        self.base_url = "https://koyso.com"
        self.all_games = []
        self.opener = urllib.request.build_opener()
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Connection', 'keep-alive'),
            ('Upgrade-Insecure-Requests', '1'),
        ]
        self.genres = {
            '1': ('All Games', '/'),
            '2': ('Action Games', '/category/action'),
            '3': ('Adventure Games', '/category/adventure'),
            '4': ('R18+', '/category/r18'),
            '5': ('Shooting Games', '/category/shooting'),
            '6': ('Casual Games', '/category/casual'),
            '7': ('Sports Racing', '/category/sports_racing'),
            '8': ('Simulation Business', '/category/simulation'),
            '9': ('Role Playing', '/category/rpg'),
            '10': ('Strategy Games', '/category/strategy'),
            '11': ('Fighting Games', '/category/fighting'),
            '12': ('Horror Games', '/category/horror'),
            '13': ('Real-time strategy', '/category/rts'),
            '14': ('Card Game', '/category/card'),
            '15': ('Indie Games', '/category/indie'),
            '16': ('LAN connection', '/category/lan')
        }
        self.secret_key = "f6i6@m29r3fwi^yqd"
        self.request_delay = 0.05
        self.proxy_cache = {}
        self.failed_urls = set()

    def fetch_page(self, url, timeout=15):
        try:
            time.sleep(self.request_delay)
            request = urllib.request.Request(url)
            response = self.opener.open(request, timeout=timeout)
            content = response.read()
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    decoded = content.decode(encoding)
                    if '<html' in decoded.lower() or '<!doctype' in decoded.lower():
                        return decoded
                    return decoded
                except UnicodeDecodeError:
                    continue
            return content.decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            debug_log(f"HTTPError fetching {url}: {e.code}")
            return None
        except urllib.error.URLError as e:
            debug_log(f"URLError fetching {url}: {str(e)}")
            return None
        except Exception as e:
            debug_log(f"Error fetching page {url}: {str(e)}")
            return None

    def _extract_games_from_page(self, html_content):
        if not html_content:
            return []
            
        games = []
        
        patterns = [
            r'<a class="game_item"[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)</span>',
            r'<a[^>]*class="game[^"]*"[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)</span>',
            r'<div[^>]*class="game[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>.*?<[^>]*>([^<]+)</[^>]*>'
        ]
        
        for pattern in patterns:
            game_item_matches = re.findall(pattern, html_content, re.DOTALL)
            if game_item_matches:
                debug_log(f"Found {len(game_item_matches)} games with pattern")
                break
        else:
            debug_log("No games found with any pattern")
            return []
        
        for idx, (game_url, image_url, game_title) in enumerate(game_item_matches):
            if not game_url or not game_title.strip():
                continue
                
            game_id = game_url.strip().split('/')[-1]
            if not game_id or not game_id.isdigit():
                continue
            
            proxied_image = self._create_proxy_url(image_url)
            
            game = {
                'title': html.unescape(game_title.strip()),
                'id': game_id,
                'image_url': proxied_image,
                'view': f'/api/game/{game_id}'
            }
            
            if idx < 3:
                debug_log(f"  Game {idx}: ID={game_id}, Title={game_title.strip()[:50]}")
            games.append(game)
        
        return games

    def _create_proxy_url(self, original_url):
        if not original_url or not original_url.startswith('http'):
            return '/static/placeholder.png'
        
        url_hash = hashlib.md5(original_url.encode()).hexdigest()
        self.proxy_cache[url_hash] = original_url
        
        return f'/proxy/{url_hash}'

    def _has_next_page(self, html_content, current_page):
        if not html_content:
            return False
            
        next_page_pattern = r'<a[^>]*href="[^"]*\?page={}"[^>]*>'.format(current_page + 1)
        next_arrow_pattern = r'<a[^>]*href="[^"]*\?page={}"[^>]*class="anticon"[^>]*>'.format(current_page + 1)
        
        if re.search(next_page_pattern, html_content) or re.search(next_arrow_pattern, html_content):
            return True
        
        pagination_text = re.search(r'<a>(\d+)/(\d+)</a>', html_content)
        if pagination_text:
            current, total = pagination_text.groups()
            if int(current) < int(total):
                return True
        
        return False

    def get_games(self, genre_id=None, search_query=None, page=1):
        debug_log(f"get_games: genre_id={genre_id}, search={search_query}, page={page}")
        
        if search_query:
            encoded_query = urllib.parse.quote(search_query)
            url = f"{self.base_url}/?keywords={encoded_query}" + (f"&page={page}" if page > 1 else "")
        elif genre_id and genre_id in self.genres:
            genre_name, genre_url = self.genres[genre_id]
            url = f"{self.base_url}{genre_url}" + (f"?page={page}" if page > 1 else "")
        else:
            url = f"{self.base_url}/" + (f"?page={page}" if page > 1 else "")
        
        debug_log(f"Fetching URL: {url}")
        html_content = self.fetch_page(url)
        
        if not html_content:
            debug_log("Failed to fetch page content")
            return [], False
        
        games = self._extract_games_from_page(html_content)
        has_next = self._has_next_page(html_content, page)
        
        debug_log(f"Extracted {len(games)} games, has_next={has_next}")
        return games, has_next

    def get_game_details(self, game_url):
        debug_log(f"get_game_details: {game_url}")
        html_content = self.fetch_page(game_url)
        
        if not html_content:
            debug_log("Failed to fetch game details")
            return None
        
        details = {}
        
        title_patterns = [
            r'<h1 class="content_title"[^>]*>(.*?)</h1>',
            r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h1>',
            r'<title>([^<]+)</title>'
        ]
        
        for pattern in title_patterns:
            title_match = re.search(pattern, html_content, re.DOTALL)
            if title_match:
                details['title'] = html.unescape(re.sub(r'<[^>]*>', '', title_match.group(1)).strip())
                break
        
        if 'title' not in details:
            details['title'] = 'Unknown Game'
        
        content_patterns = [
            r'<div class="content_body">(.*?)</div>',
            r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
            r'<article[^>]*>(.*?)</article>'
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
        
        all_images = re.findall(r'https?://[^\s"\'<>]+\.(?:jpg|png|gif|webp|avif|jpeg)', html_content, re.IGNORECASE)
        all_videos = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|webm)', html_content, re.IGNORECASE)
        
        unique_images = list(dict.fromkeys(all_images))[:30]
        unique_videos = list(dict.fromkeys(all_videos))[:10]
        
        proxied_images = [self._create_proxy_url(img) for img in unique_images]
        proxied_videos = [self._create_proxy_url(vid) for vid in unique_videos]
        
        details['media'] = {
            'images': proxied_images,
            'videos': proxied_videos
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
            rec_image = self._create_proxy_url(rec_img_match.group(1)) if rec_img_match else '/static/placeholder.png'
            
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
        debug_log(f"get_final_download_url: {game_id}")
        
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
            req.add_header('Cookie', 'site_auth=1; key=NBQEah#h@6qHr7T!k')
            
            response = urllib.request.urlopen(req, timeout=30)
            response_data = response.read().decode('utf-8')
            
            try:
                json_response = json.loads(response_data)
                
                if isinstance(json_response, str) and json_response.startswith('http'):
                    return {"status": "success", "url": json_response}
                elif 'url' in json_response:
                    return {"status": "success", "url": json_response['url']}
                elif 'data' in json_response and isinstance(json_response['data'], dict) and 'url' in json_response['data']:
                    return {"status": "success", "url": json_response['data']['url']}
                
                return {"status": "error", "message": "No download URL in response"}
                
            except json.JSONDecodeError:
                if response_data and response_data.startswith('http'):
                    return {"status": "success", "url": response_data.strip()}
            
            return {"status": "error", "message": "Invalid response format"}
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return {"status": "rate_limited", "message": "Too many requests"}
            return {"status": "error", "message": f"HTTP {e.code}"}
            
        except Exception as e:
            debug_log(f"Download error: {str(e)}")
            return {"status": "error", "message": "Download service unavailable"}

scraper = VylaScraper()

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = app.make_response('')
        response.status_code = 204
        return response

def json_response(data, status_code=200):
    try:
        response = jsonify(data)
        response.status_code = status_code
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        debug_log(f"JSON response error: {str(e)}")
        fallback = jsonify({"error": "Internal server error", "details": str(e)})
        fallback.status_code = 500
        return fallback

def rate_limit_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

@app.route('/proxy/<url_hash>')
def proxy_media(url_hash):
    if url_hash not in scraper.proxy_cache:
        debug_log(f"Proxy cache miss: {url_hash}")
        return send_from_directory('static', 'placeholder.png') if os.path.exists('static/placeholder.png') else ('', 404)
    
    original_url = scraper.proxy_cache[url_hash]
    
    if original_url in scraper.failed_urls:
        debug_log(f"Skipping known failed URL: {original_url}")
        return send_from_directory('static', 'placeholder.png') if os.path.exists('static/placeholder.png') else ('', 404)
    
    try:
        req = urllib.request.Request(original_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Referer', 'https://koyso.com/')
        req.add_header('Accept', '*/*')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            
            flask_response = app.make_response(content)
            flask_response.headers['Content-Type'] = content_type
            flask_response.headers['Cache-Control'] = 'public, max-age=31536000'
            
            return flask_response
            
    except Exception as e:
        debug_log(f"Proxy error for {original_url}: {str(e)}")
        scraper.failed_urls.add(original_url)
        return send_from_directory('static', 'placeholder.png') if os.path.exists('static/placeholder.png') else ('', 404)

@app.route('/api/health')
def health_check():
    try:
        test_games, _ = scraper.get_games('1', None, 1)
        checks = {
            "scraping": len(test_games) > 0,
            "connectivity": True,
            "api_responsive": True
        }
        return json_response({
            "status": "healthy" if all(checks.values()) else "degraded",
            "checks": checks,
            "games_found": len(test_games),
            "timestamp": int(time.time())
        })
    except Exception as e:
        return json_response({
            "status": "fail",
            "error": str(e),
            "checks": {
                "scraping": False,
                "connectivity": False,
                "api_responsive": False
            },
            "timestamp": int(time.time())
        }, 500)

@app.route('/api/genres')
def get_genres():
    genres_list = []
    for genre_id, (genre_name, _) in scraper.genres.items():
        genres_list.append({
            "id": genre_id,
            "name": genre_name,
            "url": f"/api/games?genre={genre_id}&page=1"
        })
    
    return json_response({
        "api_version": "2.0",
        "total_genres": len(genres_list),
        "genres": genres_list,
        "endpoints": {
            "health": "/api/health",
            "genres": "/api/genres",
            "games": "/api/games?genre={genre_id}&page={page}",
            "search": "/api/search?q={query}&page={page}",
            "game_details": "/api/game/{game_id}",
            "download": "/api/download/{game_id}"
        }
    })

@app.route('/')
def index():
    accept_header = request.headers.get('Accept', '')
    
    if 'application/json' in accept_header:
        genres_list = []
        for genre_id, (genre_name, _) in scraper.genres.items():
            genres_list.append({
                "id": genre_id,
                "name": genre_name,
                "url": f"/api/games?genre={genre_id}&page=1"
            })
        
        return json_response({
            "api_version": "2.0",
            "available_genres": genres_list,
            "endpoints": {
                "health": "/api/health",
                "genres": "/api/genres",
                "games": "/api/games?genre={genre_id}&page={page}",
                "search": "/api/search?q={query}&page={page}",
                "game_details": "/api/game/{game_id}",
                "download": "/api/download/{game_id}"
            }
        })
    
    return render_template('index.html')

@app.route('/api/search')
@rate_limit_check
def api_search():
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    
    if not query:
        return json_response({'error': 'Query parameter required', 'back': request.url_root}, 400)
    
    games, has_next = scraper.get_games(None, query, page)
    
    result = {
        'status': 'success',
        'search_query': query,
        'total_results': len(games),
        'page': page,
        'has_next': has_next,
        'games': games
    }
    
    if page > 1:
        result['previous'] = f'/api/search?q={urllib.parse.quote(query)}&page={page-1}'
    if has_next:
        result['next'] = f'/api/search?q={urllib.parse.quote(query)}&page={page+1}'
    result['back'] = request.url_root
    
    return json_response(result)

@app.route('/api/games')
@rate_limit_check
def get_games():
    genre_id = request.args.get('genre', '1')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    
    games, has_next = scraper.get_games(genre_id, search, page)
    
    genre_name = scraper.genres.get(genre_id, ('Unknown', ''))[0] if not search else None
    
    result = {
        'status': 'success',
        'total_results': len(games),
        'page': page,
        'has_next': has_next,
        'games': games
    }
    
    if genre_name:
        result['genre'] = genre_name
        result['genre_id'] = genre_id
    if search:
        result['search_query'] = search
    
    if page > 1:
        prev_url = f'/api/games?genre={genre_id}&page={page-1}'
        if search:
            prev_url = f'/api/games?search={urllib.parse.quote(search)}&page={page-1}'
        result['previous'] = prev_url
    
    if has_next:
        next_url = f'/api/games?genre={genre_id}&page={page+1}'
        if search:
            next_url = f'/api/games?search={urllib.parse.quote(search)}&page={page+1}'
        result['next'] = next_url
    
    result['back'] = request.url_root
    
    return json_response(result)

@app.route('/api/game/<game_id>')
@rate_limit_check
def get_game(game_id):
    if not game_id.isdigit():
        return json_response({'error': 'Invalid game ID', 'back': request.url_root}, 400)
    
    game_url = f"https://koyso.com/game/{game_id}"
    details = scraper.get_game_details(game_url)
    
    if details:
        return json_response(details)
    
    return json_response({'error': 'Game not found or unavailable', 'back': request.url_root}, 404)

@app.route('/api/download/<game_id>')
@rate_limit_check
def get_download_url(game_id):
    if not game_id.isdigit():
        return json_response({'error': 'Invalid game ID', 'back': request.url_root}, 400)
    
    result = scraper.get_final_download_url(game_id)
    
    if not result or not isinstance(result, dict):
        return json_response({'error': 'Download service error', 'back': request.url_root}, 500)
    
    if result.get("status") == "rate_limited":
        return json_response({
            'error': 'rate_limited',
            'message': 'Too many requests to download service',
            'back': request.url_root
        }, 429)
    
    elif result.get("status") == "success":
        return json_response({
            'status': 'success',
            'download_url': result.get('url'),
            'back': request.url_root
        })
    
    else:
        return json_response({
            'error': result.get('message', 'Failed to get download URL'),
            'back': request.url_root
        }, 500)

@app.errorhandler(404)
def not_found(e):
    return json_response({'error': 'Endpoint not found', 'back': request.url_root}, 404)

@app.errorhandler(500)
def internal_error(e):
    return json_response({'error': 'Internal server error', 'back': request.url_root}, 500)

if __name__ == '__main__':
    app.run(debug=True)