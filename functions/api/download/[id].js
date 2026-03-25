import { getFinalDownloadUrl, jsonResponse, handleOptions } from '../../_scraper.js';

export async function onRequestOptions() {
    return handleOptions();
}

export async function onRequestGet({ params }) {
    const { id } = params;

    if (!/^\d+$/.test(id)) {
        return jsonResponse({ error: 'Invalid game ID' }, 400);
    }

    const result = await getFinalDownloadUrl(id);

    if (!result) {
        return jsonResponse({ error: 'Download service error' }, 500);
    }

    if (result.status === 'success') {
        return jsonResponse({ status: 'success', download_url: result.url });
    }

    return jsonResponse({ error: result.message || 'Download failed' }, 500);
}