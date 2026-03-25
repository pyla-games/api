import { GENRES, jsonResponse, handleOptions } from './_scraper.js';

export async function onRequestOptions() {
    return handleOptions();
}

export async function onRequestGet() {
    const genresList = Object.entries(GENRES).map(([gid, [gname]]) => ({
        id: gid,
        name: gname,
        url: `/api/games?genre=${gid}&page=1`,
    }));

    return jsonResponse({
        api_version: '2.0',
        endpoints: {
            health: '/api/health',
            genres: '/api/genres',
            games: '/api/games?genre={genre_id}&page={page}',
            search: '/api/search?q={query}&page={page}',
            game_details: '/api/game/{game_id}',
            download: '/api/download/{game_id}',
            proxy_media: '/proxy/{base64_encoded_url}',
        },
        search: {
            usage: 'GET /api/search?q={query}&page={page}',
            example: '/api/search?q=minecraft&page=1',
            note: 'Returns paginated results with has_next and next/previous links',
        },
        available_genres: genresList,
    });
}