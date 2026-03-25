import { GENRES, getGames, jsonResponse, handleOptions } from '../_scraper.js';

export async function onRequestOptions() {
    return handleOptions();
}

export async function onRequestGet({ request }) {
    const url = new URL(request.url);
    const genreId = url.searchParams.get('genre') || '1';
    const page = parseInt(url.searchParams.get('page') || '1', 10);

    const [games, hasNext] = await getGames(genreId, null, page);

    return jsonResponse({
        status: 'success',
        genre: (GENRES[genreId] || ['Unknown'])[0],
        genre_id: genreId,
        total_results: games.length,
        page,
        has_next: hasNext,
        games,
        previous: page > 1 ? `/api/games?genre=${genreId}&page=${page - 1}` : null,
        next: hasNext ? `/api/games?genre=${genreId}&page=${page + 1}` : null,
    });
}