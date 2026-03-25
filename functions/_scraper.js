const BASE_URL = "https://koyso.com";
const SECRET_KEY = "f6i6@m29r3fwi^yqd";

const GENRES = {
    '1': ['All Games', '/'],
    '2': ['Action Games', '/category/action'],
    '3': ['Adventure Games', '/category/adventure'],
    '4': ['Shooting Games', '/category/shooting'],
    '5': ['Casual Games', '/category/casual'],
    '6': ['Sports Racing', '/category/sports_racing'],
    '7': ['Simulation Business', '/category/simulation'],
    '8': ['Role Playing', '/category/rpg'],
    '9': ['Strategy Games', '/category/strategy'],
    '10': ['Fighting Games', '/category/fighting'],
    '11': ['Horror Games', '/category/horror'],
    '12': ['Real-time strategy', '/category/rts'],
    '13': ['Card Game', '/category/card'],
    '14': ['Indie Games', '/category/indie'],
    '15': ['LAN connection', '/category/lan'],
};

const HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
};

function createProxyUrl(originalUrl) {
    if (!originalUrl || !originalUrl.startsWith('http')) return '';
    const encoded = btoa(originalUrl).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    return `/proxy/${encoded}`;
}

function unescapeHtml(str) {
    return str
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&nbsp;/g, ' ');
}

async function fetchPage(url, timeout = 15000) {
    try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeout);
        const res = await fetch(url, { headers: HEADERS, signal: controller.signal });
        clearTimeout(timer);
        if (!res.ok) return null;
        return await res.text();
    } catch {
        return null;
    }
}

function extractGamesFromPage(htmlContent) {
    if (!htmlContent) return [];
    const games = [];
    const pattern = /<a class="game_item"[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)<\/span>/gs;
    let match;
    while ((match = pattern.exec(htmlContent)) !== null) {
        const [, gameUrl, imageUrl, gameTitle] = match;
        if (!gameUrl || !gameTitle.trim()) continue;
        const gameId = gameUrl.trim().split('/').pop();
        if (!gameId || !/^\d+$/.test(gameId)) continue;
        games.push({
            title: unescapeHtml(gameTitle.trim()),
            id: gameId,
            image_url: createProxyUrl(imageUrl),
            view: `/api/game/${gameId}`,
        });
    }
    return games;
}

function hasNextPage(htmlContent, currentPage) {
    if (!htmlContent) return false;
    const nextPattern = new RegExp(`<a[^>]*href="[^"]*\\?page=${currentPage + 1}"[^>]*>`);
    if (nextPattern.test(htmlContent)) return true;
    const pagMatch = htmlContent.match(/<a>(\d+)\/(\d+)<\/a>/);
    if (pagMatch && parseInt(pagMatch[1]) < parseInt(pagMatch[2])) return true;
    return false;
}

export async function getGames(genreId = '1', searchQuery = null, page = 1) {
    if (searchQuery) {
        const encoded = encodeURIComponent(searchQuery);
        const url = `${BASE_URL}/?keywords=${encoded}${page > 1 ? `&page=${page}` : ''}`;
        const html = await fetchPage(url);
        if (!html) return [[], false];
        return [extractGamesFromPage(html), hasNextPage(html, page)];
    }

    const safeGenres = Object.entries(GENRES).filter(([gid, [, path]]) => gid !== '1' && !path.includes('r18'));

    if (genreId === '1' || !GENRES[genreId]) {
        const seenIds = new Set();
        const combined = [];
        for (const [, [, genrePath]] of safeGenres) {
            const url = `${BASE_URL}${genrePath}`;
            const html = await fetchPage(url);
            if (!html) continue;
            for (const g of extractGamesFromPage(html)) {
                if (!seenIds.has(g.id)) {
                    seenIds.add(g.id);
                    combined.push(g);
                }
            }
        }
        const pageSize = 30;
        const start = (page - 1) * pageSize;
        const end = start + pageSize;
        return [combined.slice(start, end), end < combined.length];
    }

    const [, genrePath] = GENRES[genreId];
    const url = `${BASE_URL}${genrePath}${page > 1 ? `?page=${page}` : ''}`;
    const html = await fetchPage(url);
    if (!html) return [[], false];
    return [extractGamesFromPage(html), hasNextPage(html, page)];
}

export async function getGameDetails(gameId) {
    const url = `${BASE_URL}/game/${gameId}`;
    const htmlContent = await fetchPage(url);
    if (!htmlContent) return null;

    const details = {};

    const titlePatterns = [
        /<h1 class="content_title"[^>]*>(.*?)<\/h1>/s,
        /<h1[^>]*>(.*?)<\/h1>/s,
        /<title>([^<]+)<\/title>/,
    ];

    for (const pattern of titlePatterns) {
        const m = htmlContent.match(pattern);
        if (m) {
            let title = unescapeHtml(m[1].replace(/<[^>]*>/g, '').trim());
            title = title.replace(/\s*Free\s+Download\s*$/i, '').trim();
            details.title = title;
            break;
        }
    }
    if (!details.title) details.title = 'Unknown Game';

    const contentPatterns = [
        /<div class="content_body">(.*?)<\/div>/s,
        /<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)<\/div>/s,
    ];

    for (const pattern of contentPatterns) {
        const m = htmlContent.match(pattern);
        if (m) {
            const paragraphs = m[1].split(/<\/p>|<p[^>]*>/)
                .map(p => p.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim())
                .filter(Boolean);
            details.full_description = unescapeHtml(paragraphs.join('|||'));
            break;
        }
    }
    if (!details.full_description) details.full_description = 'No description available';

    const recSplit = htmlContent.split(/class="recommendations/);
    const mainContent = recSplit.length > 1 ? recSplit[0] : htmlContent;

    const imgPattern = /https?:\/\/[^\s"'<>]+\.(?:jpg|png|gif|webp|avif|jpeg)/gi;
    const vidPattern = /https?:\/\/[^\s"'<>]+\.(?:mp4|webm)/gi;

    const allImages = [...new Set(mainContent.match(imgPattern) || [])].slice(0, 30);
    const allVideos = mainContent.match(vidPattern) || [];
    const seenStems = new Set();
    const dedupedVideos = [];
    for (const v of allVideos) {
        const stem = v.replace(/\.(webm|mp4)$/i, '');
        if (!seenStems.has(stem)) {
            seenStems.add(stem);
            dedupedVideos.push(v);
        }
    }

    details.media = {
        images: allImages.map(createProxyUrl),
        videos: dedupedVideos.slice(0, 10).map(createProxyUrl),
    };

    const sizeMatch = htmlContent.match(/<li>\s*<span>Size<\/span>\s*<span>([^<]+)<\/span>/s);
    details.size = sizeMatch ? sizeMatch[1].trim() : 'Unknown';

    const versionMatch = htmlContent.match(/<li>\s*<span>Version<\/span>\s*<span[^>]*>([^<]+)<\/span>/s);
    details.version = versionMatch ? versionMatch[1].trim() : 'Unknown';

    const recommendations = [];
    const recPattern = /<a class="recommendations_item" href="https:\/\/koyso\.com\/game\/(\d+)"[^>]*title="([^"]*)"/g;
    let recMatch;
    while ((recMatch = recPattern.exec(htmlContent)) !== null && recommendations.length < 6) {
        const [, recId, recTitle] = recMatch;
        const imgPat = new RegExp(`<a class="recommendations_item" href="https://koyso\\.com/game/${recId}".*?<img[^>]*src="([^"]+)"`, 's');
        const imgM = htmlContent.match(imgPat);
        recommendations.push({
            id: recId,
            title: unescapeHtml(recTitle),
            image_url: imgM ? createProxyUrl(imgM[1]) : '',
            view: `/api/game/${recId}`,
        });
    }

    if (recommendations.length) details.recommendations = recommendations;
    details.id = gameId;
    details.download_url = `/api/download/${gameId}`;

    return details;
}

export async function getFinalDownloadUrl(gameId) {
    try {
        const timestamp = String(Math.floor(Date.now() / 1000));
        const hashInput = timestamp + gameId + SECRET_KEY;

        const encoder = new TextEncoder();
        const data = encoder.encode(hashInput);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const sign = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

        const canvasId = String(Math.floor(Math.random() * 900000000) + 100000000);

        const body = new URLSearchParams({
            id: gameId,
            timestamp,
            secretKey: sign,
            canvasId: canvasId,
        });

        const targetUrl = `${BASE_URL}/api/getGamesDownloadUrl`;
        const refererUrl = `${BASE_URL}/download/${gameId}`;

        const proxies = [
            `https://corsproxy.io/?${encodeURIComponent(targetUrl)}`,
            `https://api.allorigins.win/raw?url=${encodeURIComponent(targetUrl)}`,
            `https://thingproxy.freeboard.io/fetch/${targetUrl}`,
        ];

        let res = null;
        let lastError = '';

        for (const proxyUrl of proxies) {
            try {
                res = await fetch(proxyUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Referer': refererUrl,
                        'Origin': BASE_URL,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                        'Sec-Ch-Ua-Mobile': '?0',
                        'Sec-Ch-Ua-Platform': '"Windows"',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-origin',
                    },
                    body: body.toString(),
                });

                if (res.ok) break;
                lastError = `proxy ${proxyUrl} returned ${res.status}`;
            } catch (e) {
                lastError = `proxy ${proxyUrl} threw: ${e.message}`;
                res = null;
            }
        }

        if (!res || !res.ok) {
            return { status: 'error', message: `All proxies failed. Last: ${lastError}` };
        }

        const text = await res.text();
        const cleanText = text.trim().replace(/^"|"$/g, '');

        if (cleanText.startsWith('http')) {
            return { status: 'success', url: cleanText };
        }

        try {
            const json = JSON.parse(text);
            const url = json.url || json.download_url || (json.data && json.data.url) || (typeof json.data === 'string' ? json.data : null);

            if (url && typeof url === 'string' && url.startsWith('http')) {
                return { status: 'success', url };
            }

            return { status: 'error', message: json.msg || json.message || 'No URL found in response' };
        } catch (e) {
            return {
                status: 'error',
                message: 'Firewall block after proxy. Response: ' + cleanText.substring(0, 150),
                debug: {
                    status: res.status,
                    fullBody: cleanText.substring(0, 2000),
                }
            };
        }

    } catch (err) {
        return { status: 'error', message: err.message || 'Download service unavailable' };
    }
}

export { GENRES };

export function jsonResponse(data, status = 200) {
    return new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Accept',
        },
    });
}

export function handleOptions() {
    return new Response(null, {
        status: 204,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Accept',
        },
    });
}