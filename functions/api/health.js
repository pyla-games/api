import { getGames, jsonResponse, handleOptions } from '../_scraper.js';

export async function onRequestOptions() {
    return handleOptions();
}

export async function onRequestGet() {
    try {
        const [games] = await getGames('2', null, 1);
        return jsonResponse({
            status: games.length > 0 ? 'healthy' : 'degraded',
            timestamp: Math.floor(Date.now() / 1000),
        });
    } catch (e) {
        return jsonResponse({ status: 'fail', error: String(e) }, 500);
    }
}