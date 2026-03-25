import { getGameDetails, jsonResponse, handleOptions } from '../../_scraper.js';

export async function onRequestOptions() {
    return handleOptions();
}

export async function onRequestGet({ params }) {
    const { id } = params;

    if (!/^\d+$/.test(id)) {
        return jsonResponse({ error: 'Invalid game ID' }, 400);
    }

    const details = await getGameDetails(id);

    if (details) {
        return jsonResponse(details);
    }

    return jsonResponse({ error: 'Game not found' }, 404);
}