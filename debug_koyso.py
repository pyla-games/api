import urllib.request
import re

url = "https://koyso.com/game/1927"
req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

try:
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    
    with open('koyso_1927_full.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Saved full HTML ({len(html)} chars) to koyso_1927_full.html")
    
    print("\n" + "="*80)
    print("SEARCHING FOR ALL MEDIA PATTERNS")
    print("="*80)
    
    print("\n1. All URLs ending in video/image extensions:")
    all_media = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|webm|gif|jpg|png|jpeg|avif|webp)', html, re.IGNORECASE)
    extensions = {}
    for url in all_media:
        ext = url.split('.')[-1].lower()
        if ext not in extensions:
            extensions[ext] = []
        extensions[ext].append(url)
    
    for ext, urls in sorted(extensions.items()):
        print(f"\n{ext.upper()} ({len(urls)} found):")
        for url in sorted(set(urls))[:5]:
            print(f"  {url}")
        if len(set(urls)) > 5:
            print(f"  ... and {len(set(urls)) - 5} more")
    
    print("\n2. Checking for autoplay/loop attributes (animated content):")
    autoplay = re.findall(r'<[^>]*(?:autoplay|loop)[^>]*>', html, re.IGNORECASE)
    print(f"  Found {len(autoplay)} elements with autoplay/loop")
    for tag in autoplay[:3]:
        print(f"  {tag[:100]}")
    
    print("\n3. Checking for data-* attributes with media:")
    data_attrs = re.findall(r'data-[a-z-]+=["\']([^"\']+\.(?:mp4|webm|gif))["\']', html, re.IGNORECASE)
    print(f"  Found {len(data_attrs)} data-* attributes with video/gif")
    for attr in data_attrs[:5]:
        print(f"  {attr}")
    
    print("\n4. Looking for Steam CDN extras/ with all extensions:")
    extras = re.findall(r'(https://[^/]+/store_item_assets/steam/apps/\d+/extras/[^\s"\'<>]+)', html, re.IGNORECASE)
    print(f"  Found {len(set(extras))} unique extras/ URLs:")
    for url in sorted(set(extras)):
        ext = url.split('.')[-1] if '.' in url else 'NO_EXT'
        print(f"  [{ext.upper()}] {url}")
    
    print("\n5. All content inside content_body div:")
    content_body = re.search(r'<div class="content_body">(.*?)</div>', html, re.DOTALL)
    if content_body:
        body_text = content_body.group(1)
        print(f"  Length: {len(body_text)} chars")
        
        body_media = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|webm|gif)', body_text, re.IGNORECASE)
        print(f"  Videos/GIFs in content_body: {len(body_media)}")
        
        body_tags = re.findall(r'<(video|source|img|picture)[^>]*>', body_text, re.IGNORECASE)
        print(f"  Media tags in content_body: {len(body_tags)}")
        for tag in body_tags[:10]:
            print(f"    <{tag}...>")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()