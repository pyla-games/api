export function onRequestOptions() {
    return new Response(null, {
        status: 204,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Accept',
        },
    });
}

export function onRequest({ request }) {
    const url = new URL(request.url);

    if (url.pathname === '/') {
        return new Response(JSON.stringify({
            status: "online",
            message: "Vyla-Games API is running",
            endpoints: {
                health: { method: "GET", path: "/api/health", desc: "Health check" },
                genres: { method: "GET", path: "/api/genres", desc: "All genres" },
                games: { method: "GET", path: "/api/games?genre={id}&page={n}", desc: "Game list" },
                search: { method: "GET", path: "/api/search?q={query}&page={n}", desc: "Search games" },
                game: { method: "GET", path: "/api/game/{id}", desc: "Game details" },
                download: { method: "GET", path: "/api/download/{id}", desc: "Download URL" }
            }
        }, null, 2), {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        });
    }

    if (url.pathname === '/favicon.ico') {
        return new Response(null, { status: 204 });
    }

    return new Response(JSON.stringify({ error: "Not found" }), {
        status: 404,
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    });
}