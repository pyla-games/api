import { getGames, jsonResponse, handleOptions } from '../_scraper.js';

export async function onRequestOptions() {
    return handleOptions();
}

export async function onRequestGet({ request }) {
    const url = new URL(request.url);
    const query = url.searchParams.get('q') || '';
    const page = parseInt(url.searchParams.get('page') || '1', 10);

    if (!query) {
        return jsonResponse({ error: 'Query required' }, 400);
    }

    const [games, hasNext] = await getGames(null, query, page);

    return jsonResponse({
        status: 'success',
        search_query: query,
        total_results: games.length,
        page,
        has_next: hasNext,
        games,
        previous: page > 1 ? `/api/search?q=${encodeURIComponent(query)}&page=${page - 1}` : null,
        next: hasNext ? `/api/search?q=${encodeURIComponent(query)}&page=${page + 1}` : null,
    });
}