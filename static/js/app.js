let state = { page: 1, genre: '1', search: '', hasNext: false };
function nav(u, push = true) {
    if (u.startsWith('http')) {
        const url = new URL(u);
        const path = url.pathname;
        fetch(path, { headers: { 'Accept': 'application/json' } }).then(r => r.json()).then(d => {
            render(d);
            if (push) window.history.pushState({ url: path }, '', path);
        }).catch(e => render({ error: 'Failed to load', message: e.message }));
        return;
    }
    fetch(u, { headers: { 'Accept': 'application/json' } }).then(r => r.text()).then(text => {
        try {
            const d = JSON.parse(text);
            render(d);
            if (push) window.history.pushState({ url: u }, '', u);
        } catch (e) {
            render({ error: 'Failed to parse JSON', message: e.message });
        }
    }).catch(e => render({ error: 'Failed to load', message: e.message }));
}
function render(d) {
    const o = document.getElementById('output');
    const linked = JSON.stringify(d, null, 2).replace(/"(\/[^"]+)"/g, (m, p) => {
        if (p.match(/^\/(api\/|search\/|\?|game\/|image\/|video\/|download\/)/)) return `"<a href="${p}">${p}</a>"`;
        return m;
    }).replace(/"(https?:\/\/[^"]+)"/g, (m, u) => {
        try {
            const url = new URL(u);
            if (url.hostname === window.location.hostname && url.pathname === '/') return `"<a href="${u}">${u}</a>"`;
        } catch (e) { }
        return `"<a href="${u}" target="_blank">${u}</a>"`;
    });
    o.innerHTML = linked;
    if (d.page) state.page = d.page;
    if (d.has_next !== undefined) state.hasNext = d.has_next;
    attachLinks();
}
function attachLinks() {
    document.querySelectorAll('#output a').forEach(a => {
        const h = a.getAttribute('href');
        if (!h || h.startsWith('http')) return;
        a.onclick = e => {
            e.preventDefault();
            if (h.startsWith('/image/') || h.startsWith('/video/')) { window.open(h, '_blank'); return; }
            if (h.startsWith('/download/')) { window.open(h, '_blank'); return; }
            if (h.startsWith('/?')) parseQuery(h);
            else nav(h);
        };
    });
}
function parseQuery(p) {
    const u = new URLSearchParams(p.split('?')[1]);
    const g = u.get('genre') || '1';
    const pg = u.get('page') || '1';
    const s = u.get('search') || '';
    state.genre = g; state.page = parseInt(pg); state.search = s;
    nav(s ? `/api/games?search=${encodeURIComponent(s)}&page=${pg}` : `/api/games?genre=${g}&page=${pg}`);
}
function init() {
    const p = new URLSearchParams(window.location.search);
    const path = window.location.pathname;
    const g = p.get('genre'), s = p.get('search'), pg = p.get('page');
    const gm = path.match(/^\/game\/(\d+)$/);
    const dl = path.match(/^\/game\/(\d+)\/download$/);
    const sr = path.match(/^\/search\/(.+)$/);
    const api_game = path.match(/^\/api\/game\/(\d+)$/);
    const api_games = path.match(/^\/api\/games$/);
    if (api_game) nav(`/api/game/${api_game[1]}`, false);
    else if (api_games) nav(`/api/games${window.location.search}`, false);
    else if (gm) nav(`/api/game/${gm[1]}`, false);
    else if (dl) nav(`/game/${dl[1]}/download`, false);
    else if (sr) nav(`/search/${decodeURIComponent(sr[1])}?page=${pg || 1}`, false);
    else if (g || s || pg) parseQuery(window.location.search);
    else if (path !== '/') nav('/api/genres', false);
}
window.onpopstate = e => { if (e.state && e.state.url) nav(e.state.url, false); else init(); };
window.onload = init;