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
            game = {
                'title': html.unescape(game_title.strip()),
                'url': urllib.parse.urljoin(self.base_url, game_url.strip()),
                'id': game_url.strip().split('/')[-1],
                'image_url': image_url
            }
            games.append(game)
        return games

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
                    unique_images.append(img)
                else:
                    for existing_img in unique_images:
                        if existing_img.split('/')[-1].split('.')[0] == basename:
                            current_ext = '.' + existing_img.split('.')[-1]
                            new_ext = '.' + img.split('.')[-1]
                            if image_preference.index(new_ext) < image_preference.index(current_ext):
                                unique_images.remove(existing_img)
                                unique_images.append(img)
                            break
            
            filtered_images = []
            for img in unique_images:
                if 'capsule_616x353.jpg' not in img and 'extras/' in img:
                    filtered_images.append(img)
            
            details['content_images'] = filtered_images[:10]
            details['videos'] = unique_videos[:5]

        recommendations_pattern = r'<a class="recommendations_item" href="([^"]+)"[^>]*title="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]+)"'
        recommendations = []
        recommendation_matches = re.findall(recommendations_pattern, html_content, re.DOTALL)
        
        for rec_url, rec_title, rec_image in recommendation_matches:
            rec_id = rec_url.split('/')[-1]
            recommendations.append({
                'id': rec_id,
                'title': html.unescape(rec_title),
                'url': rec_url,
                'image': rec_image
            })
        
        if recommendations:
            details['recommendations'] = recommendations

        capsule_match = re.search(r'<div class="capsule_div">.*?<img[^>]*src="([^"]*)"', html_content, re.DOTALL)
        if capsule_match:
            details['capsule_image'] = capsule_match.group(1)

        size_match = re.search(r'<span>Size</span>\s*<span>([^<]+)</span>', html_content)
        if size_match:
            details['file_size'] = size_match.group(1).strip()

        version_match = re.search(r'<span>Version</span>\s*<span[^>]*>([^<]+)</span>', html_content)
        if version_match:
            details['version'] = version_match.group(1).strip()

        download_match = re.search(r'onclick="download\(\)".*?href="/download/(\d+)"', html_content, re.DOTALL)
        if download_match:
            details['game_id'] = download_match.group(1)
            details['download_page'] = f"{self.base_url}/download/{download_match.group(1)}"
        else:
            download_match = re.search(r'<button[^>]*onclick="[^"]*/download/(\d+)[^"]*"', html_content)
            if download_match:
                details['game_id'] = download_match.group(1)
                details['download_page'] = f"{self.base_url}/download/{download_match.group(1)}"

        return details

    def generate_hash(self, timestamp, game_id):
        data = timestamp + game_id + self.secret_key
        return hashlib.sha256(data.encode()).hexdigest()

    def get_canvas_fingerprint(self):
        import random
        return random.randint(100000000, 999999999)

    def get_final_download_url(self, game_id):
        current_time = time.time()
        if game_id in self.last_download_request:
            time_since_last = current_time - self.last_download_request[game_id]
            if time_since_last < self.download_cooldown:
                wait_time = self.download_cooldown - time_since_last
                return {"status": "cooldown", "wait": int(wait_time)}
        
        download_page_url = f"{self.base_url}/download/{game_id}"
        print(f"Fetching download page: {download_page_url}")
        html_content = self.fetch_page(download_page_url)
        if not html_content:
            print("Failed to fetch download page")
            return {"status": "error", "message": "Could not fetch download page"}

        timestamp = str(int(time.time()))
        secret_hash = self.generate_hash(timestamp, game_id)
        canvas_id = str(self.get_canvas_fingerprint())

        api_url = f"{self.base_url}/api/getGamesDownloadUrl"
        print(f"Requesting download URL from: {api_url}")
        print(f"Request data - id: {game_id}, timestamp: {timestamp}, canvasId: {canvas_id}")
        
        post_data = urllib.parse.urlencode({
            'id': game_id,
            'timestamp': timestamp,
            'secretKey': secret_hash,
            'canvasId': canvas_id
        }).encode('utf-8')

        cookie_jar = http.cookiejar.CookieJar()
        cookie_processor = urllib.request.HTTPCookieProcessor(cookie_jar)
        opener = urllib.request.build_opener(cookie_processor)
        
        from http.cookiejar import Cookie
        cookie = Cookie(
            version=0, name='site_auth', value='1',
            port=None, port_specified=False,
            domain='.koyso.com', domain_specified=True, domain_initial_dot=True,
            path='/', path_specified=True,
            secure=False, expires=None, discard=True,
            comment=None, comment_url=None, rest={}, rfc2109=False
        )
        cookie_jar.set_cookie(cookie)
        
        cookie2 = Cookie(
            version=0, name='key', value='NBQEah#h@6qHr7T!k',
            port=None, port_specified=False,
            domain='.koyso.com', domain_specified=True, domain_initial_dot=True,
            path='/', path_specified=True,
            secure=False, expires=None, discard=True,
            comment=None, comment_url=None, rest={}, rfc2109=False
        )
        cookie_jar.set_cookie(cookie2)

        request = urllib.request.Request(
            api_url,
            data=post_data,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': self.base_url,
                'Referer': download_page_url,
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            })

        try:
            response = opener.open(request, timeout=30)
            
            import gzip
            raw_data = response.read()
            
            if raw_data[:2] == b'\x1f\x8b':
                response_data = gzip.decompress(raw_data).decode('utf-8')
            else:
                try:
                    response_data = raw_data.decode('utf-8')
                except UnicodeDecodeError:
                    for encoding in ['latin-1', 'iso-8859-1', 'cp1252']:
                        try:
                            response_data = raw_data.decode(encoding)
                            break
                        except:
                            continue
                    else:
                        response_data = raw_data.decode('utf-8', errors='replace')
            
            print(f"Response received: {response_data[:200]}")
            
            self.last_download_request[game_id] = current_time
            
            response_data = response_data.strip().strip('"')
            
            if response_data.startswith('http'):
                print(f"Direct URL found: {response_data}")
                return {"status": "success", "url": response_data}

            try:
                json_data = json.loads(response_data)
                if isinstance(json_data, str) and json_data.startswith('http'):
                    return {"status": "success", "url": json_data}
                elif isinstance(json_data, dict) and 'url' in json_data:
                    return {"status": "success", "url": json_data['url']}
                elif isinstance(json_data, dict) and 'downloadUrl' in json_data:
                    return {"status": "success", "url": json_data['downloadUrl']}
            except json.JSONDecodeError:
                if response_data:
                    return {"status": "success", "url": response_data}

            return {"status": "error", "message": "Invalid response format"}

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
            
            print(f"HTTP Error {e.code}: {error_body[:200]}")
            
            if e.code == 429:
                self.last_download_request[game_id] = current_time + 60
                return {"status": "rate_limited"}
            elif e.code == 403:
                return {"status": "error", "message": "Access forbidden - clock sync issue or blocked"}
            elif e.code == 404:
                return {"status": "error", "message": "Download API endpoint not found - API may have changed"}
            return {"status": "error", "message": f"HTTP {e.code}"}
        except Exception as e:
            print(f"Exception in get_final_download_url: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

scraper = VylaScraper()

def rate_limit_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'rate_limited' in request.cookies:
            return json.dumps({'error': 'Rate limited. Try again later.'}), 429, {'Content-Type': 'application/json'}
        return f(*args, **kwargs)
    return decorated_function

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
        
        return json.dumps({
            "status": overall_status,
            "checks": checks,
            "timestamp": int(time.time())
        }, ensure_ascii=False), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        return json.dumps({
            "status": "fail",
            "error": str(e),
            "checks": {
                "scraping": False,
                "connectivity": False,
                "api_responsive": False
            },
            "timestamp": int(time.time())
        }, ensure_ascii=False), 500, {'Content-Type': 'application/json'}

@app.route('/')
def index():
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
        'total_games': len(games),
        'page': page,
        'has_next': has_next,
        'games': games
    }
    
    if page > 1:
        result['previous'] = f'/search/{urllib.parse.quote(decoded_query)}?page={page-1}'
    
    if has_next:
        result['next'] = f'/search/{urllib.parse.quote(decoded_query)}?page={page+1}'
    
    result['back'] = '/'
    
    return json.dumps(result, ensure_ascii=False), 200, {'Content-Type': 'application/json'}

@app.route('/api/games')
@rate_limit_check
def get_games():
    genre_id = request.args.get('genre', '1')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    
    games, has_next = scraper.get_games(genre_id, search, page)
    return json.dumps({
        'games': games,
        'has_next': has_next,
        'page': page
    }, ensure_ascii=False), 200, {'Content-Type': 'application/json'}

@app.route('/api/game/<game_id>')
@rate_limit_check
def get_game(game_id):
    game_url = f"https://koyso.com/game/{game_id}"
    details = scraper.get_game_details(game_url)
    if details:
        return json.dumps(details, ensure_ascii=False), 200, {'Content-Type': 'application/json'}
    return json.dumps({'error': 'Game not found'}, ensure_ascii=False), 404, {'Content-Type': 'application/json'}

@app.route('/game/<game_id>/download')
@rate_limit_check
def get_download_url(game_id):
    result = scraper.get_final_download_url(game_id)
    
    if result is None:
        return json.dumps({'error': 'Failed to get download URL'}, ensure_ascii=False), 500, {'Content-Type': 'application/json'}
    
    if isinstance(result, dict):
        if result.get("status") == "cooldown":
            return json.dumps({'error': 'cooldown', 'wait': result.get('wait', scraper.download_cooldown)}, ensure_ascii=False), 429, {'Content-Type': 'application/json'}
        elif result.get("status") == "rate_limited":
            return json.dumps({'error': 'rate_limited'}, ensure_ascii=False), 429, {'Content-Type': 'application/json'}
        elif result.get("status") == "success":
            return json.dumps({'url': result.get('url')}, ensure_ascii=False), 200, {'Content-Type': 'application/json'}
        elif result.get("status") == "error":
            return json.dumps({'error': result.get('message', 'Unknown error')}, ensure_ascii=False), 500, {'Content-Type': 'application/json'}
    
    return json.dumps({'error': 'Failed to get download URL'}, ensure_ascii=False), 500, {'Content-Type': 'application/json'}

@app.route('/api/download/<game_id>')
@rate_limit_check
def get_download_url_api(game_id):
    result = scraper.get_final_download_url(game_id)
    
    if result is None:
        return json.dumps({'error': 'Failed to get download URL'}, ensure_ascii=False), 500, {'Content-Type': 'application/json'}
    
    if isinstance(result, dict):
        if result.get("status") == "cooldown":
            return json.dumps({'error': 'cooldown', 'wait': result.get('wait', scraper.download_cooldown)}, ensure_ascii=False), 429, {'Content-Type': 'application/json'}
        elif result.get("status") == "rate_limited":
            return json.dumps({'error': 'rate_limited'}, ensure_ascii=False), 429, {'Content-Type': 'application/json'}
        elif result.get("status") == "success":
            return json.dumps({'url': result.get('url')}, ensure_ascii=False), 200, {'Content-Type': 'application/json'}
        elif result.get("status") == "error":
            return json.dumps({'error': result.get('message', 'Unknown error')}, ensure_ascii=False), 500, {'Content-Type': 'application/json'}
    
    return json.dumps({'error': 'Failed to get download URL'}, ensure_ascii=False), 500, {'Content-Type': 'application/json'}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/'):
        return json.dumps({'error': 'Not found'}, ensure_ascii=False), 404, {'Content-Type': 'application/json'}
    
    game_download_match = re.match(r'game/(\d+)/download', path)
    if game_download_match:
        game_id = game_download_match.group(1)
        return get_download_url(game_id)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)