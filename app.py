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
        self.last_download_request = {}
        self.download_cooldown = 10
        self.url_cache = {}

    def fetch_page(self, url):
        try:
            time.sleep(self.request_delay)
            request = urllib.request.Request(url)
            response = self.opener.open(request)
            content = response.read()
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return content.decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            debug_log(f"HTTPError fetching {url}: {e.code}")
            return ""
        except Exception as e:
            debug_log(f"Error fetching page {url}: {str(e)}")
            return ""

    def _extract_games_from_page(self, html_content):
        games = []
        game_item_pattern = r'<a class="game_item"[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)</span>'
        game_item_matches = re.findall(game_item_pattern, html_content, re.DOTALL)
        debug_log(f"_extract_games_from_page: Found {len(game_item_matches)} game items")
        for idx, (game_url, image_url, game_title) in enumerate(game_item_matches):
            game_id = game_url.strip().split('/')[-1]
            proxied_image = self._proxy_url(image_url, 'image')
            game = {
                'title': html.unescape(game_title.strip()),
                'id': game_id,
                'image_url': proxied_image,
                'view': f'/api/game/{game_id}'
            }
            if idx < 3:
                debug_log(f"  Game {idx}: ID={game_id}, URL={game_url}, Title={game_title.strip()[:50]}")
            games.append(game)
        return games

    def _proxy_url(self, url, media_type='image'):
        if not url or not url.startswith('http'):
            return url
        
        encoded_url = urllib.parse.quote(url, safe='')
        proxy_path = f'/proxy/{media_type}/{encoded_url}'
        self.url_cache[proxy_path] = url
        return proxy_path

    def _has_next_page(self, html_content, current_page):
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
        debug_log(f"get_games called: genre_id={genre_id}, search_query={search_query}, page={page}")
        games = []
        if search_query:
            encoded_query = urllib.parse.quote(search_query)
            if page == 1:
                url = f"{self.base_url}/?keywords={encoded_query}"
            else:
                url = f"{self.base_url}/?keywords={encoded_query}&page={page}"
        elif genre_id and genre_id in self.genres:
            genre_name, genre_url = self.genres[genre_id]
            if page == 1:
                url = f"{self.base_url}{genre_url}"
            else:
                url = f"{self.base_url}{genre_url}?page={page}"
        else:
            if page == 1:
                url = f"{self.base_url}/"
            else:
                url = f"{self.base_url}/?page={page}"
        debug_log(f"Fetching URL: {url}")
        html_content = self.fetch_page(url)
        if html_content:
            games = self._extract_games_from_page(html_content)
            has_next = self._has_next_page(html_content, page)
        else:
            has_next = False
        return games, has_next

    def get_game_details(self, game_url):
        debug_log(f"=== get_game_details called for: {game_url} ===")
        html_content = self.fetch_page(game_url)
        if not html_content:
            debug_log("Failed to fetch HTML content")
            return None
        
        details = {}
        
        title_match = re.search(r'<h1 class="content_title"[^>]*>(.*?)</h1>', html_content, re.DOTALL)
        if title_match:
            details['title'] = html.unescape(re.sub(r'<[^>]*>', '', title_match.group(1)).strip())
            debug_log(f"Title: {details['title']}")
        
        content_body_match = re.search(r'<div class="content_body">(.*?)</div>', html_content, re.DOTALL)
        if content_body_match:
            content_html = content_body_match.group(1)
            paragraphs = re.split(r'</p>|<p[^>]*>', content_html)
            clean_paragraphs = []
            for p in paragraphs:
                p = re.sub(r'<[^>]*>', '', p)
                p = re.sub(r'\s+', ' ', p).strip()
                if p:
                    clean_paragraphs.append(p)
            details['full_description'] = html.unescape('|||'.join(clean_paragraphs))
            debug_log(f"Description length: {len(details['full_description'])}")
            
            all_media = re.findall(r'https?://[^\s"\']+\.(?:jpg|png|gif|webp|avif|jpeg|mp4|webm)', html_content, re.IGNORECASE)
            img_pattern = r'<img[^>]*src="([^"]+\.(?:jpg|png|gif|webp|avif|jpeg))"'
            img_matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            picture_source_pattern = r'<source[^>]*srcset="([^"]+\.(?:webp|avif|jpg|png|gif|jpeg))"'
            picture_matches = re.findall(picture_source_pattern, html_content, re.IGNORECASE)
            all_media_urls = list(set(img_matches + picture_matches + all_media))
            
            video_webm = re.findall(r'https?://[^\s"\']+\.webm', html_content, re.IGNORECASE)
            video_mp4 = re.findall(r'https?://[^\s"\']+\.mp4', html_content, re.IGNORECASE)
            video_urls = video_webm + video_mp4
            unique_videos = []
            video_basenames = set()
            for video in video_urls:
                basename = video.split('/')[-1].split('.')[0]
                if basename not in video_basenames:
                    video_basenames.add(basename)
                    if video.endswith('.webm'):
                        unique_videos.append(video)
                    elif video.endswith('.mp4'):
                        if basename + '.webm' not in video_basenames:
                            unique_videos.append(video)
            
            unique_images = []
            image_basenames = set()
            image_preference = ['.webp', '.avif', '.png', '.jpg', '.jpeg', '.gif']
            for img in all_media_urls:
                if img.endswith(('.mp4', '.webm')):
                    continue
                basename = img.split('/')[-1].split('.')[0]
                if basename not in image_basenames:
                    image_basenames.add(basename)
                    selected = img
                    for other_img in all_media_urls:
                        if other_img.split('/')[-1].split('.')[0] == basename:
                            for ext in image_preference:
                                if other_img.endswith(ext):
                                    selected = other_img
                                    break
                    unique_images.append(selected)
            
            proxied_images = [self._proxy_url(img, 'image') for img in unique_images[:30]]
            proxied_videos = [self._proxy_url(vid, 'video') for vid in unique_videos[:10]]
            details['media'] = {
                'images': proxied_images,
                'videos': proxied_videos
            }
            debug_log(f"Found {len(proxied_images)} images and {len(proxied_videos)} videos")
        
        size_match = re.search(r'<li>\s*<span>Size</span>\s*<span>([^<]+)</span>', html_content, re.DOTALL)
        if size_match:
            details['size'] = size_match.group(1).strip()
            debug_log(f"Size: {details['size']}")
        
        version_match = re.search(r'<li>\s*<span>Version</span>\s*<span[^>]*>([^<]+)</span>', html_content, re.DOTALL)
        if version_match:
            details['version'] = version_match.group(1).strip()
            debug_log(f"Version: {details['version']}")
        
        recommendations = []
        rec_pattern = r'<a class="recommendations_item" href="https://koyso\.com/game/(\d+)"[^>]*title="([^"]*)"'
        rec_matches = re.findall(rec_pattern, html_content)
        debug_log(f"Found {len(rec_matches)} recommendations")
        for rec_id, rec_title in rec_matches:
            rec_img_pattern = f'<a class="recommendations_item" href="https://koyso\\.com/game/{rec_id}".*?<img[^>]*src="([^"]+)"'
            rec_img_match = re.search(rec_img_pattern, html_content, re.DOTALL)
            rec_image = self._proxy_url(rec_img_match.group(1), 'image') if rec_img_match else None
            recommendations.append({
                'id': rec_id,
                'title': html.unescape(rec_title),
                'image_url': rec_image,
                'view': f'/api/game/{rec_id}'
            })
        if recommendations:
            details['recommendations'] = recommendations
            debug_log(f"Recommendations: {[r['title'] for r in recommendations]}")
        
        game_id = game_url.split('/')[-1]
        details['id'] = game_id
        details['download_url'] = f"/api/download/{game_id}"
        details['back'] = f"{request.url_root}"
        
        debug_log(f"=== get_game_details complete for game {game_id} ===")
        return details

    def get_final_download_url(self, game_id):
        debug_log(f"\n=== get_final_download_url called for game_id: {game_id} ===")
        current_time = time.time()
        
        if game_id in self.last_download_request:
            time_since_last = current_time - self.last_download_request[game_id]
            if time_since_last < self.download_cooldown:
                wait_time = int(self.download_cooldown - time_since_last) + 1
                debug_log(f"Cooldown active, wait: {wait_time}s")
                return {"status": "cooldown", "wait": wait_time}
        
        self.last_download_request[game_id] = current_time
        
        try:
            timestamp = str(int(time.time()))
            hash_input = timestamp + game_id + self.secret_key
            sign = hashlib.sha256(hash_input.encode()).hexdigest()
            
            debug_log(f"Timestamp: {timestamp}")
            debug_log(f"Hash input: {hash_input}")
            debug_log(f"SHA256 Sign: {sign}")
            
            download_api_url = f"{self.base_url}/api/getGamesDownloadUrl"
            debug_log(f"Target URL: {download_api_url}")
            
            post_data = {
                'id': game_id,
                'timestamp': timestamp,
                'secretKey': sign,
                'canvasId': '0'
            }
            debug_log(f"POST data: {post_data}")
            
            encoded_data = urllib.parse.urlencode(post_data).encode('utf-8')
            req = urllib.request.Request(download_api_url, data=encoded_data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept', 'application/json, text/plain, */*')
            req.add_header('Referer', f'{self.base_url}/download/{game_id}')
            req.add_header('Cookie', 'site_auth=1; key=NBQEah#h@6qHr7T!k')
            
            debug_log("Sending request...")
            response = urllib.request.urlopen(req, timeout=30)
            response_data = response.read().decode('utf-8')
            debug_log(f"Response received: {response_data[:200]}")
            
            try:
                json_response = json.loads(response_data)
                debug_log(f"Parsed JSON: {json_response}")
                
                if isinstance(json_response, str) and json_response.startswith('http'):
                    debug_log(f"Response is direct URL: {json_response}")
                    return {"status": "success", "url": json_response}
                elif 'url' in json_response:
                    debug_log(f"Found URL in response: {json_response['url']}")
                    return {"status": "success", "url": json_response['url']}
                elif 'data' in json_response and isinstance(json_response['data'], dict) and 'url' in json_response['data']:
                    debug_log(f"Found URL in data: {json_response['data']['url']}")
                    return {"status": "success", "url": json_response['data']['url']}
                
                debug_log("No URL found in JSON response")
                return {"status": "error", "message": "No download URL in API response"}
                
            except json.JSONDecodeError as je:
                debug_log(f"JSON decode error: {je}")
                if response_data and response_data.startswith('http'):
                    debug_log(f"Response is plain URL: {response_data}")
                    return {"status": "success", "url": response_data.strip()}
            
            return {"status": "error", "message": "Invalid API response format"}
            
        except urllib.error.HTTPError as e:
            error_body = ''
            try:
                if e.fp:
                    raw_data = e.fp.read()
                    for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                        try:
                            error_body = raw_data.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
            except Exception:
                pass
            
            debug_log(f"HTTPError: {e.code} - {e.reason}")
            debug_log(f"Error body: {error_body[:200]}")
            
            if e.code == 429:
                return {"status": "rate_limited", "message": "Too many requests"}
            return {"status": "error", "message": f"HTTP {e.code}: {e.reason}"}
            
        except Exception as e:
            debug_log(f"Exception: {str(e)}")
            import traceback
            debug_log(f"Traceback: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}

scraper = VylaScraper()

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

@app.route('/OPTIONS', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path=''):
    response = app.make_response('')
    response.status_code = 204
    return response

def json_response(data, status_code=200):
    response = jsonify(data)
    response.status_code = status_code
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

def rate_limit_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

@app.route('/proxy/<media_type>/<path:encoded_url>')
def proxy_media(media_type, encoded_url):
    try:
        original_url = urllib.parse.unquote(encoded_url)
        debug_log(f"Proxying {media_type}: {original_url}")
        
        req = urllib.request.Request(original_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Referer', 'https://koyso.com/')
        req.add_header('Accept', '*/*')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            
            flask_response = app.make_response(content)
            flask_response.headers['Content-Type'] = content_type
            flask_response.headers['Cache-Control'] = 'public, max-age=31536000'
            flask_response.headers['Access-Control-Allow-Origin'] = '*'
            
            return flask_response
            
    except Exception as e:
        debug_log(f"Error proxying {original_url}: {str(e)}")
        return json_response({'error': 'Failed to fetch media', 'url': original_url}, 500)

@app.route('/image/<path:image_path>')
def serve_image(image_path):
    encoded_url = urllib.parse.quote(f'image/{image_path}', safe='')
    return proxy_media('image', encoded_url)

@app.route('/video/<path:video_path>')
def serve_video(video_path):
    encoded_url = urllib.parse.quote(f'video/{video_path}', safe='')
    return proxy_media('video', encoded_url)

@app.route('/download/<path:download_path>')
def serve_download(download_path):
    encoded_url = urllib.parse.quote(f'download/{download_path}', safe='')
    return proxy_media('download', encoded_url)

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
            "search": "/search/{query}?page={page}",
            "game_details": "/api/game/{game_id}",
            "download": "/game/{game_id}/download"
        }
    })

@app.route('/')
def index():
    debug_log("=== INDEX ROUTE ===")
    accept_header = request.headers.get('Accept', '')
    user_agent = request.headers.get('User-Agent', '').lower()
    debug_log(f"Accept header: {accept_header}")
    debug_log(f"User-Agent: {user_agent}")
    
    is_browser = 'mozilla' in user_agent or 'chrome' in user_agent or 'safari' in user_agent
    wants_json = 'application/json' in accept_header
    
    debug_log(f"is_browser: {is_browser}, wants_json: {wants_json}")
    
    if wants_json or not is_browser:
        debug_log("Returning JSON response")
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
                "search": "/search/{query}?page={page}",
                "game_details": "/api/game/{game_id}",
                "download": "/game/{game_id}/download"
            }
        })
    
    debug_log("Returning HTML template")
    return render_template('index.html')

@app.route('/search/<path:query>')
@rate_limit_check
def search_path(query):
    debug_log("=== SEARCH ROUTE ===")
    debug_log(f"Query: {query}")
    
    page = int(request.args.get('page', 1))
    decoded_query = urllib.parse.unquote(query)
    debug_log(f"Decoded query: {decoded_query}, Page: {page}")
    
    games, has_next = scraper.get_games(None, decoded_query, page)
    debug_log(f"Found {len(games)} games, has_next: {has_next}")
    
    result = {
        'status': 'success',
        'search_query': decoded_query,
        'total_results': len(games),
        'page': page,
        'has_next': has_next,
        'games': games
    }
    
    if page > 1:
        result['previous'] = f'/search/{urllib.parse.quote(decoded_query)}?page={page-1}'
    if has_next:
        result['next'] = f'/search/{urllib.parse.quote(decoded_query)}?page={page+1}'
    result['back'] = request.url_root
    
    debug_log("Returning JSON response")
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
    debug_log(f"=== API GAME ROUTE: {game_id} ===")
    game_url = f"https://koyso.com/game/{game_id}"
    details = scraper.get_game_details(game_url)
    
    if details:
        return json_response(details)
    
    debug_log("Game not found")
    return json_response({'error': 'Game not found', 'back': request.url_root}, 404)

@app.route('/game/<game_id>')
@rate_limit_check
def game_details_path(game_id):
    debug_log("=== GAME DETAILS ROUTE ===")
    debug_log(f"Game ID: {game_id}")
    
    game_url = f"https://koyso.com/game/{game_id}"
    details = scraper.get_game_details(game_url)
    
    if details:
        debug_log("Game details found, returning JSON")
        return json_response(details)
    
    debug_log("Game not found")
    return json_response({'error': 'Game not found', 'back': request.url_root}, 404)

@app.route('/api/download/<game_id>')
@app.route('/game/<game_id>/download')
@rate_limit_check
def get_download_url_unified(game_id):
    debug_log(f"\n=== DOWNLOAD REQUEST for game_id: {game_id} ===")
    result = scraper.get_final_download_url(game_id)
    debug_log(f"Download result type: {type(result)}")
    debug_log(f"Download result: {result}")
    
    if result is None:
        debug_log("ERROR: Result is None")
        return json_response({'error': 'Failed to get download URL', 'back': request.url_root}, 500)
    
    if isinstance(result, dict):
        debug_log(f"Result status: {result.get('status')}")
        
        if result.get("status") == "cooldown":
            debug_log(f"Cooldown: {result.get('wait')} seconds")
            return json_response({
                'error': 'cooldown',
                'wait_seconds': result.get('wait', scraper.download_cooldown),
                'back': request.url_root
            }, 429)
        
        elif result.get("status") == "rate_limited":
            debug_log("Rate limited by upstream")
            return json_response({
                'error': 'rate_limited',
                'message': 'Too many requests',
                'back': request.url_root
            }, 429)
        
        elif result.get("status") == "success":
            original_url = result.get('url')
            debug_log(f"Original download URL: {original_url}")
            return json_response({
                'status': 'success',
                'download_url': original_url,
                'back': request.url_root
            })
        
        elif result.get("status") == "error":
            error_msg = result.get('message', 'Unknown error')
            debug_log(f"ERROR: {error_msg}")
            return json_response({
                'error': error_msg,
                'back': request.url_root
            }, 500)
    
    debug_log("ERROR: Unexpected result format")
    return json_response({'error': 'Failed to get download URL', 'back': request.url_root}, 500)

if __name__ == '__main__':
    app.run(debug=True)