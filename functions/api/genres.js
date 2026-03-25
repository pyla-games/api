import { GENRES, jsonResponse, handleOptions } from '../_scraper.js';

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
        total_genres: genresList.length,
        genres: genresList,
    });
}