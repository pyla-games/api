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
            return ""
        except Exception as e:
            print(f"Error fetching page {url}: {str(e)}")
            return ""

    def _extract_games_from_page(self, html_content):
        games = []
        game_item_pattern = r'<a class="game_item"[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)</span>'
        game_item_matches = re.findall(game_item_pattern, html_content, re.DOTALL)
        for game_url, image_url, game_title in game_item_matches:
            game_id = game_url.strip().split('/')[-1]
            proxied_image = self._proxy_url(image_url, 'image')
            game = {
                'title': html.unescape(game_title.strip()),
                'id': game_id,
                'image_url': proxied_image,
                'view': f'/api/game/{game_id}'
            }
            games.append(game)
        return games

    def _proxy_url(self, url, media_type='image'):
        if not url or not url.startswith('http'):
            return url
        
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        
        if media_type == 'download':
            filename = parsed.path.split('/')[-1]
            if parsed.query:
                filename = f"{filename}?{parsed.query}"
            clean_path = f'/download/{filename}'
        else:
            url_clean = url.replace('https://', '').replace('http://', '')
            parts = url_clean.split('/')
            if len(parts) >= 2:
                filename = '/'.join(parts[-2:])
            else:
                filename = parts[-1] if parts else 'file'
            clean_path = f'/{media_type}/{filename}'
        
        proxy_path = f'/proxy{clean_path}'
        self.url_cache[proxy_path] = url
        return clean_path

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
        html_content = self.fetch_page(url)
        if html_content:
            games = self._extract_games_from_page(html_content)
            has_next = self._has_next_page(html_content, page)
        else:
            has_next = False
        return games, has_next

    def get_game_details(self, game_url):
        html_content = self.fetch_page(game_url)
        if not html_content:
            return None
        details = {}
        title_match = re.search(r'<h1 class="content_title"[^>]*>(.*?)</h1>', html_content, re.DOTALL)
        if title_match:
            details['title'] = html.unescape(re.sub(r'<[^>]*>', '', title_match.group(1)).strip())
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
        game_id = game_url.split('/')[-1]
        details['id'] = game_id
        details['download_url'] = f"/api/download/{game_id}"
        details['back'] = "/"
        return details

    def get_final_download_url(self, game_id):
        print(f"\n>>> get_final_download_url called for game_id: {game_id}")
        current_time = time.time()
        
        if game_id in self.last_download_request:
            time_since_last = current_time - self.last_download_request[game_id]
            if time_since_last < self.download_cooldown:
                wait_time = int(self.download_cooldown - time_since_last) + 1
                print(f">>> Cooldown active, wait: {wait_time}s")
                return {"status": "cooldown", "wait": wait_time}
        
        self.last_download_request[game_id] = current_time
        
        try:
            timestamp = str(int(time.time()))
            hash_input = timestamp + game_id + self.secret_key
            sign = hashlib.sha256(hash_input.encode()).hexdigest()
            
            print(f">>> Timestamp: {timestamp}")
            print(f">>> Hash input: {hash_input}")
            print(f">>> SHA256 Sign: {sign}")
            
            download_api_url = f"{self.base_url}/api/getGamesDownloadUrl"
            print(f">>> Target URL: {download_api_url}")
            
            post_data = {
                'id': game_id,
                'timestamp': timestamp,
                'secretKey': sign,
                'canvasId': '0'
            }
            print(f">>> POST data: {post_data}")
            
            encoded_data = urllib.parse.urlencode(post_data).encode('utf-8')
            req = urllib.request.Request(download_api_url, data=encoded_data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept', 'application/json, text/plain, */*')
            req.add_header('Referer', f'{self.base_url}/download/{game_id}')
            req.add_header('Cookie', 'site_auth=1; key=NBQEah#h@6qHr7T!k')
            
            print(f">>> Sending request...")
            response = urllib.request.urlopen(req, timeout=30)
            response_data = response.read().decode('utf-8')
            print(f">>> Response received: {response_data[:200]}")
            
            try:
                json_response = json.loads(response_data)
                print(f">>> Parsed JSON: {json_response}")
                
                if isinstance(json_response, str) and json_response.startswith('http'):
                    print(f">>> Response is direct URL: {json_response}")
                    return {"status": "success", "url": json_response}
                elif 'url' in json_response:
                    print(f">>> Found URL in response: {json_response['url']}")
                    return {"status": "success", "url": json_response['url']}
                elif 'data' in json_response and isinstance(json_response['data'], dict) and 'url' in json_response['data']:
                    print(f">>> Found URL in data: {json_response['data']['url']}")
                    return {"status": "success", "url": json_response['data']['url']}
                
                print(f">>> No URL found in JSON response")
                return {"status": "error", "message": "No download URL in API response"}
                
            except json.JSONDecodeError as je:
                print(f">>> JSON decode error: {je}")
                if response_data and response_data.startswith('http'):
                    print(f">>> Response is plain URL: {response_data}")
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
                        except:
                            continue
            except:
                error_body = 'Could not decode error response'
            
            print(f">>> HTTP Error {e.code}")
            print(f">>> Error body: {error_body[:500]}")
            
            if e.code == 429:
                try:
                    rate_limit_data = json.loads(error_body)
                    if 'downloadUrl' in rate_limit_data:
                        print(f">>> Found download URL in 429 response: {rate_limit_data['downloadUrl']}")
                        return {"status": "success", "url": rate_limit_data['downloadUrl']}
                except:
                    pass
                self.last_download_request[game_id] = current_time + 300
                return {"status": "rate_limited", "message": "Too many requests to upstream API"}
            elif e.code == 403:
                return {"status": "error", "message": "Access forbidden - check cookies or timestamp"}
            elif e.code == 404:
                return {"status": "error", "message": "Game download not available"}
            
            return {"status": "error", "message": f"Upstream API error: HTTP {e.code}"}
            
        except Exception as e:
            print(f">>> Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": f"Download service error: {str(e)}"}

scraper = VylaScraper()

def rate_limit_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'rate_limited' in request.cookies:
            return json.dumps({'error': 'Rate limited'}), 429, {'Content-Type': 'application/json'}
        return f(*args, **kwargs)
    return decorated_function

def json_response(data, status=200):
    return json.dumps(data, ensure_ascii=False, indent=2), status, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/download/<path:download_path>')
@app.route('/proxy/download/<path:download_path>')
def proxy_download(download_path):
    try:
        query_string = request.query_string.decode('utf-8')
        if query_string:
            full_path = f'/proxy/download/{download_path}?{query_string}'
        else:
            full_path = f'/proxy/download/{download_path}'
        
        print(f">>> Proxy download request: {full_path}")
        print(f">>> Cache keys available: {list(scraper.url_cache.keys())[:5]}")
        
        if full_path in scraper.url_cache:
            url = scraper.url_cache[full_path]
            print(f">>> Found in cache: {url}")
        else:
            print(f">>> Not in cache, trying without query...")
            base_path = f'/proxy/download/{download_path}'
            if base_path in scraper.url_cache:
                url = scraper.url_cache[base_path]
                if query_string:
                    url = f"{url}?{query_string}"
                print(f">>> Reconstructed URL: {url}")
            else:
                url = f"https://{download_path}"
                if query_string:
                    url = f"{url}?{query_string}"
                print(f">>> Fallback URL: {url}")
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Referer', 'https://koyso.com/')
        response = urllib.request.urlopen(req, timeout=30)
        file_data = response.read()
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        filename = download_path.split('/')[-1]
        return file_data, 200, {
            'Content-Type': content_type,
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Cache-Control': 'public, max-age=3600'
        }
    except Exception as e:
        print(f">>> Proxy download error: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({'error': 'Failed to download file'}, 404)

@app.route('/image/<path:image_path>')
@app.route('/proxy/image/<path:image_path>')
def proxy_image(image_path):
    try:
        proxy_key = f'/proxy/image/{image_path}'
        if proxy_key in scraper.url_cache:
            url = scraper.url_cache[proxy_key]
        else:
            url = f"https://{image_path}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Referer', 'https://koyso.com/')
        response = urllib.request.urlopen(req, timeout=30)
        image_data = response.read()
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        return image_data, 200, {'Content-Type': content_type, 'Cache-Control': 'public, max-age=86400'}
    except Exception as e:
        return json_response({'error': 'Failed to load image'}, 404)

@app.route('/video/<path:video_path>')
@app.route('/proxy/video/<path:video_path>')
def proxy_video(video_path):
    try:
        proxy_key = f'/proxy/video/{video_path}'
        if proxy_key in scraper.url_cache:
            url = scraper.url_cache[proxy_key]
        else:
            url = f"https://{video_path}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Referer', 'https://koyso.com/')
        response = urllib.request.urlopen(req, timeout=30)
        video_data = response.read()
        content_type = response.headers.get('Content-Type', 'video/mp4')
        return video_data, 200, {'Content-Type': content_type, 'Cache-Control': 'public, max-age=86400'}
    except Exception as e:
        return json_response({'error': 'Failed to load video'}, 404)

@app.route('/api/health')
def health_check():
    try:
        test_games, _ = scraper.get_games('1', None, 1)
        scraping_works = len(test_games) > 0
        test_url = f"{scraper.base_url}/"
        connectivity_works = bool(scraper.fetch_page(test_url))
        checks = {
            "scraping": scraping_works,
            "connectivity": connectivity_works,
            "api_responsive": True
        }
        overall_status = "success" if all(checks.values()) else "partial" if any(checks.values()) else "fail"
        return json_response({
            "status": overall_status,
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
    accept_header = request.headers.get('Accept', '')
    user_agent = request.headers.get('User-Agent', '').lower()
    is_browser = 'mozilla' in user_agent or 'chrome' in user_agent or 'safari' in user_agent
    wants_json = 'application/json' in accept_header
    if wants_json or not is_browser:
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
    return render_template('index.html')

@app.route('/search/<path:query>')
@rate_limit_check
def search_path(query):
    page = int(request.args.get('page', 1))
    decoded_query = urllib.parse.unquote(query)
    games, has_next = scraper.get_games(None, decoded_query, page)
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
    result['back'] = '/'
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
    result['back'] = '/'
    return json_response(result)

@app.route('/api/game/<game_id>')
@rate_limit_check
def get_game(game_id):
    game_url = f"https://koyso.com/game/{game_id}"
    details = scraper.get_game_details(game_url)
    if details:
        return json_response(details)
    return json_response({'error': 'Game not found'}, 404)

@app.route('/game/<game_id>')
@rate_limit_check
def game_details_path(game_id):
    game_url = f"https://koyso.com/game/{game_id}"
    details = scraper.get_game_details(game_url)
    if details:
        return json_response(details)
    return json_response({'error': 'Game not found'}, 404)

@app.route('/api/download/<game_id>')
@app.route('/game/<game_id>/download')
@rate_limit_check
def get_download_url_unified(game_id):
    print(f"\n=== DOWNLOAD REQUEST for game_id: {game_id} ===")
    result = scraper.get_final_download_url(game_id)
    print(f"Download result type: {type(result)}")
    print(f"Download result: {result}")
    
    if result is None:
        print("ERROR: Result is None")
        return json_response({'error': 'Failed to get download URL'}, 500)
    
    if isinstance(result, dict):
        print(f"Result status: {result.get('status')}")
        if result.get("status") == "cooldown":
            print(f"Cooldown: {result.get('wait')} seconds")
            return json_response({'error': 'cooldown', 'wait_seconds': result.get('wait', scraper.download_cooldown)}, 429)
        elif result.get("status") == "rate_limited":
            print("Rate limited by upstream")
            return json_response({'error': 'rate_limited', 'message': 'Too many requests'}, 429)
        elif result.get("status") == "success":
            original_url = result.get('url')
            print(f"Original download URL: {original_url}")
            return json_response({'status': 'success', 'download_url': original_url})
        elif result.get("status") == "error":
            error_msg = result.get('message', 'Unknown error')
            print(f"ERROR: {error_msg}")
            return json_response({'error': error_msg}, 500)
    
    print("ERROR: Unexpected result format")
    return json_response({'error': 'Failed to get download URL'}, 500)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/'):
        return json_response({'error': 'Endpoint not found'}, 404)
    game_match = re.match(r'game/(\d+)$', path)
    if game_match:
        return game_details_path(game_match.group(1))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)