export async function onRequestOptions() {
    return new Response(null, {
        status: 204,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        },
    });
}

export async function onRequestGet({ params }) {
    const encoded = Array.isArray(params.path) ? params.path[0] : params.path;

    if (!encoded) {
        return new Response('Not found', { status: 404 });
    }

    try {
        const base64 = encoded;

        const regularBase64 = base64.replace(/-/g, '+').replace(/_/g, '/');

        const paddingLength = (4 - (regularBase64.length % 4)) % 4;
        const padded = regularBase64 + '='.repeat(paddingLength);

        const originalUrl = atob(padded);

        if (!originalUrl.startsWith('http')) {
            return new Response('Invalid URL', { status: 400 });
        }

        const res = await fetch(originalUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://koyso.com/',
                'Accept': 'image/webp,image/*,*/*',
            },
        });

        if (!res.ok) {
            return new Response('Media not available', { status: 404 });
        }

        const contentType = res.headers.get('Content-Type') || 'application/octet-stream';
        const body = await res.arrayBuffer();

        return new Response(body, {
            status: 200,
            headers: {
                'Content-Type': contentType,
                'Cache-Control': 'public, max-age=31536000',
                'Access-Control-Allow-Origin': '*',
            },
        });
    } catch {
        return new Response('Media not available', { status: 404 });
    }
}