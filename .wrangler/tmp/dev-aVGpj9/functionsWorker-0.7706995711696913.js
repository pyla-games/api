var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// ../../.wrangler/tmp/pages-w1CYqb/functionsWorker-0.7706995711696913.mjs
var __defProp2 = Object.defineProperty;
var __name2 = /* @__PURE__ */ __name((target, value) => __defProp2(target, "name", { value, configurable: true }), "__name");
var BASE_URL = "https://koyso.com";
var SECRET_KEY = "f6i6@m29r3fwi^yqd";
var GENRES = {
  "1": ["All Games", "/"],
  "2": ["Action Games", "/category/action"],
  "3": ["Adventure Games", "/category/adventure"],
  "4": ["Shooting Games", "/category/shooting"],
  "5": ["Casual Games", "/category/casual"],
  "6": ["Sports Racing", "/category/sports_racing"],
  "7": ["Simulation Business", "/category/simulation"],
  "8": ["Role Playing", "/category/rpg"],
  "9": ["Strategy Games", "/category/strategy"],
  "10": ["Fighting Games", "/category/fighting"],
  "11": ["Horror Games", "/category/horror"],
  "12": ["Real-time strategy", "/category/rts"],
  "13": ["Card Game", "/category/card"],
  "14": ["Indie Games", "/category/indie"],
  "15": ["LAN connection", "/category/lan"]
};
var HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language": "en-US,en;q=0.5",
  "Connection": "keep-alive"
};
function createProxyUrl(originalUrl) {
  if (!originalUrl || !originalUrl.startsWith("http")) return "";
  const encoded = btoa(originalUrl).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
  return `/proxy/${encoded}`;
}
__name(createProxyUrl, "createProxyUrl");
__name2(createProxyUrl, "createProxyUrl");
function unescapeHtml(str) {
  return str.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, " ");
}
__name(unescapeHtml, "unescapeHtml");
__name2(unescapeHtml, "unescapeHtml");
async function fetchPage(url, timeout = 15e3) {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    const res = await fetch(url, { headers: HEADERS, signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) return null;
    return await res.text();
  } catch {
    return null;
  }
}
__name(fetchPage, "fetchPage");
__name2(fetchPage, "fetchPage");
function extractGamesFromPage(htmlContent) {
  if (!htmlContent) return [];
  const games = [];
  const pattern = /<a class="game_item"[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*(?:data-src|src)="([^"]*)"[^>]*>.*?<span[^>]*>([^<]*)<\/span>/gs;
  let match2;
  while ((match2 = pattern.exec(htmlContent)) !== null) {
    const [, gameUrl, imageUrl, gameTitle] = match2;
    if (!gameUrl || !gameTitle.trim()) continue;
    const gameId = gameUrl.trim().split("/").pop();
    if (!gameId || !/^\d+$/.test(gameId)) continue;
    games.push({
      title: unescapeHtml(gameTitle.trim()),
      id: gameId,
      image_url: createProxyUrl(imageUrl),
      view: `/api/game/${gameId}`
    });
  }
  return games;
}
__name(extractGamesFromPage, "extractGamesFromPage");
__name2(extractGamesFromPage, "extractGamesFromPage");
function hasNextPage(htmlContent, currentPage) {
  if (!htmlContent) return false;
  const nextPattern = new RegExp(`<a[^>]*href="[^"]*\\?page=${currentPage + 1}"[^>]*>`);
  if (nextPattern.test(htmlContent)) return true;
  const pagMatch = htmlContent.match(/<a>(\d+)\/(\d+)<\/a>/);
  if (pagMatch && parseInt(pagMatch[1]) < parseInt(pagMatch[2])) return true;
  return false;
}
__name(hasNextPage, "hasNextPage");
__name2(hasNextPage, "hasNextPage");
async function getGames(genreId = "1", searchQuery = null, page = 1) {
  if (searchQuery) {
    const encoded = encodeURIComponent(searchQuery);
    const url2 = `${BASE_URL}/?keywords=${encoded}${page > 1 ? `&page=${page}` : ""}`;
    const html2 = await fetchPage(url2);
    if (!html2) return [[], false];
    return [extractGamesFromPage(html2), hasNextPage(html2, page)];
  }
  const safeGenres = Object.entries(GENRES).filter(([gid, [, path]]) => gid !== "1" && !path.includes("r18"));
  if (genreId === "1" || !GENRES[genreId]) {
    const seenIds = /* @__PURE__ */ new Set();
    const combined = [];
    for (const [, [, genrePath2]] of safeGenres) {
      const url2 = `${BASE_URL}${genrePath2}`;
      const html2 = await fetchPage(url2);
      if (!html2) continue;
      for (const g of extractGamesFromPage(html2)) {
        if (!seenIds.has(g.id)) {
          seenIds.add(g.id);
          combined.push(g);
        }
      }
    }
    const pageSize = 30;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return [combined.slice(start, end), end < combined.length];
  }
  const [, genrePath] = GENRES[genreId];
  const url = `${BASE_URL}${genrePath}${page > 1 ? `?page=${page}` : ""}`;
  const html = await fetchPage(url);
  if (!html) return [[], false];
  return [extractGamesFromPage(html), hasNextPage(html, page)];
}
__name(getGames, "getGames");
__name2(getGames, "getGames");
async function getGameDetails(gameId) {
  const url = `${BASE_URL}/game/${gameId}`;
  const htmlContent = await fetchPage(url);
  if (!htmlContent) return null;
  const details = {};
  const titlePatterns = [
    /<h1 class="content_title"[^>]*>(.*?)<\/h1>/s,
    /<h1[^>]*>(.*?)<\/h1>/s,
    /<title>([^<]+)<\/title>/
  ];
  for (const pattern of titlePatterns) {
    const m = htmlContent.match(pattern);
    if (m) {
      let title = unescapeHtml(m[1].replace(/<[^>]*>/g, "").trim());
      title = title.replace(/\s*Free\s+Download\s*$/i, "").trim();
      details.title = title;
      break;
    }
  }
  if (!details.title) details.title = "Unknown Game";
  const contentPatterns = [
    /<div class="content_body">(.*?)<\/div>/s,
    /<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)<\/div>/s
  ];
  for (const pattern of contentPatterns) {
    const m = htmlContent.match(pattern);
    if (m) {
      const paragraphs = m[1].split(/<\/p>|<p[^>]*>/).map((p) => p.replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim()).filter(Boolean);
      details.full_description = unescapeHtml(paragraphs.join("|||"));
      break;
    }
  }
  if (!details.full_description) details.full_description = "No description available";
  const recSplit = htmlContent.split(/class="recommendations/);
  const mainContent = recSplit.length > 1 ? recSplit[0] : htmlContent;
  const imgPattern = /https?:\/\/[^\s"'<>]+\.(?:jpg|png|gif|webp|avif|jpeg)/gi;
  const vidPattern = /https?:\/\/[^\s"'<>]+\.(?:mp4|webm)/gi;
  const allImages = [...new Set(mainContent.match(imgPattern) || [])].slice(0, 30);
  const allVideos = mainContent.match(vidPattern) || [];
  const seenStems = /* @__PURE__ */ new Set();
  const dedupedVideos = [];
  for (const v of allVideos) {
    const stem = v.replace(/\.(webm|mp4)$/i, "");
    if (!seenStems.has(stem)) {
      seenStems.add(stem);
      dedupedVideos.push(v);
    }
  }
  details.media = {
    images: allImages.map(createProxyUrl),
    videos: dedupedVideos.slice(0, 10).map(createProxyUrl)
  };
  const sizeMatch = htmlContent.match(/<li>\s*<span>Size<\/span>\s*<span>([^<]+)<\/span>/s);
  details.size = sizeMatch ? sizeMatch[1].trim() : "Unknown";
  const versionMatch = htmlContent.match(/<li>\s*<span>Version<\/span>\s*<span[^>]*>([^<]+)<\/span>/s);
  details.version = versionMatch ? versionMatch[1].trim() : "Unknown";
  const recommendations = [];
  const recPattern = /<a class="recommendations_item" href="https:\/\/koyso\.com\/game\/(\d+)"[^>]*title="([^"]*)"/g;
  let recMatch;
  while ((recMatch = recPattern.exec(htmlContent)) !== null && recommendations.length < 6) {
    const [, recId, recTitle] = recMatch;
    const imgPat = new RegExp(`<a class="recommendations_item" href="https://koyso\\.com/game/${recId}".*?<img[^>]*src="([^"]+)"`, "s");
    const imgM = htmlContent.match(imgPat);
    recommendations.push({
      id: recId,
      title: unescapeHtml(recTitle),
      image_url: imgM ? createProxyUrl(imgM[1]) : "",
      view: `/api/game/${recId}`
    });
  }
  if (recommendations.length) details.recommendations = recommendations;
  details.id = gameId;
  details.download_url = `/api/download/${gameId}`;
  return details;
}
__name(getGameDetails, "getGameDetails");
__name2(getGameDetails, "getGameDetails");
async function getFinalDownloadUrl(gameId) {
  try {
    const timestamp = String(Math.floor(Date.now() / 1e3));
    const hashInput = timestamp + gameId + SECRET_KEY;
    const encoder = new TextEncoder();
    const data = encoder.encode(hashInput);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const sign = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
    const canvasId = String(Math.floor(Math.random() * 9e8) + 1e8);
    const body = new URLSearchParams({
      id: gameId,
      timestamp,
      secretKey: sign,
      canvasId
    });
    const refererUrl = `${BASE_URL}/download/${gameId}`;
    let cookieHeader = "";
    try {
      const primeRes = await fetch(refererUrl, {
        method: "GET",
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.9",
          "Accept-Encoding": "gzip, deflate, br",
          "Connection": "keep-alive",
          "Upgrade-Insecure-Requests": "1"
        },
        redirect: "follow"
      });
      console.log("[preflight] status:", primeRes.status);
      console.log("[preflight] headers:", Object.fromEntries(primeRes.headers.entries()));
      const rawCookies = primeRes.headers.get("set-cookie");
      console.log("[preflight] raw set-cookie:", rawCookies);
      if (rawCookies) {
        cookieHeader = rawCookies.split(",").map((c) => c.split(";")[0].trim()).join("; ");
      }
      console.log("[preflight] cookieHeader built:", cookieHeader || "NONE");
    } catch (primeErr) {
      console.log("[preflight] failed:", primeErr.message);
    }
    const headers = {
      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      "Accept": "application/json, text/javascript, */*; q=0.01",
      "Accept-Language": "en-US,en;q=0.9",
      "Accept-Encoding": "gzip, deflate, br",
      "Referer": refererUrl,
      "Origin": BASE_URL,
      "X-Requested-With": "XMLHttpRequest",
      "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
      "Sec-Ch-Ua-Mobile": "?0",
      "Sec-Ch-Ua-Platform": '"Windows"',
      "Sec-Fetch-Dest": "empty",
      "Sec-Fetch-Mode": "cors",
      "Sec-Fetch-Site": "same-origin",
      "Priority": "u=1, i",
      "Connection": "keep-alive",
      ...cookieHeader && { "Cookie": cookieHeader }
    };
    console.log("[post] sending to:", `${BASE_URL}/api/getGamesDownloadUrl`);
    console.log("[post] headers:", JSON.stringify(headers, null, 2));
    console.log("[post] body:", body.toString());
    const res = await fetch(`${BASE_URL}/api/getGamesDownloadUrl`, {
      method: "POST",
      headers,
      body: body.toString()
    });
    console.log("[post] response status:", res.status, res.statusText);
    console.log("[post] response headers:", Object.fromEntries(res.headers.entries()));
    if (res.status === 429) return { status: "rate_limited", message: "Too many requests" };
    if (!res.ok) return { status: "error", message: `Target returned HTTP ${res.status}` };
    const text = await res.text();
    console.log("[post] raw body (first 1000):", text.substring(0, 1e3));
    const cleanText = text.trim().replace(/^"|"$/g, "");
    if (cleanText.startsWith("http")) {
      return { status: "success", url: cleanText };
    }
    try {
      const json = JSON.parse(text);
      const url = json.url || json.download_url || json.data && json.data.url || (typeof json.data === "string" ? json.data : null);
      if (url && typeof url === "string" && url.startsWith("http")) {
        return { status: "success", url };
      }
      return { status: "error", message: json.msg || json.message || "No URL found in target response" };
    } catch (e) {
      return {
        status: "error",
        message: "Blocked by target firewall. Target response: " + cleanText.substring(0, 150),
        debug: {
          postStatus: res.status,
          postStatusText: res.statusText,
          postResponseHeaders: Object.fromEntries(res.headers.entries()),
          cookiesSent: cookieHeader || "none",
          fullBody: cleanText.substring(0, 2e3),
          isCloudflare: res.headers.get("server")?.toLowerCase().includes("cloudflare") ?? false,
          cfMitigated: res.headers.get("cf-mitigated") || "none"
        }
      };
    }
  } catch (err) {
    console.log("[getFinalDownloadUrl] outer catch:", err.message);
    return { status: "error", message: err.message || "Download service unavailable" };
  }
}
__name(getFinalDownloadUrl, "getFinalDownloadUrl");
__name2(getFinalDownloadUrl, "getFinalDownloadUrl");
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Accept"
    }
  });
}
__name(jsonResponse, "jsonResponse");
__name2(jsonResponse, "jsonResponse");
function handleOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Accept"
    }
  });
}
__name(handleOptions, "handleOptions");
__name2(handleOptions, "handleOptions");
async function onRequestOptions() {
  return handleOptions();
}
__name(onRequestOptions, "onRequestOptions");
__name2(onRequestOptions, "onRequestOptions");
async function onRequestGet({ params }) {
  const { id } = params;
  if (!/^\d+$/.test(id)) {
    return jsonResponse({ error: "Invalid game ID" }, 400);
  }
  const result = await getFinalDownloadUrl(id);
  if (!result) {
    return jsonResponse({ error: "Download service error" }, 500);
  }
  if (result.status === "success") {
    return jsonResponse({ status: "success", download_url: result.url });
  }
  return jsonResponse({ error: result.message || "Download failed" }, 500);
}
__name(onRequestGet, "onRequestGet");
__name2(onRequestGet, "onRequestGet");
async function onRequestOptions2() {
  return handleOptions();
}
__name(onRequestOptions2, "onRequestOptions2");
__name2(onRequestOptions2, "onRequestOptions");
async function onRequestGet2({ params }) {
  const { id } = params;
  if (!/^\d+$/.test(id)) {
    return jsonResponse({ error: "Invalid game ID" }, 400);
  }
  const details = await getGameDetails(id);
  if (details) {
    return jsonResponse(details);
  }
  return jsonResponse({ error: "Game not found" }, 404);
}
__name(onRequestGet2, "onRequestGet2");
__name2(onRequestGet2, "onRequestGet");
async function onRequestOptions3() {
  return handleOptions();
}
__name(onRequestOptions3, "onRequestOptions3");
__name2(onRequestOptions3, "onRequestOptions");
async function onRequestGet3({ request }) {
  const url = new URL(request.url);
  const genreId = url.searchParams.get("genre") || "1";
  const page = parseInt(url.searchParams.get("page") || "1", 10);
  const [games, hasNext] = await getGames(genreId, null, page);
  return jsonResponse({
    status: "success",
    genre: (GENRES[genreId] || ["Unknown"])[0],
    genre_id: genreId,
    total_results: games.length,
    page,
    has_next: hasNext,
    games,
    previous: page > 1 ? `/api/games?genre=${genreId}&page=${page - 1}` : null,
    next: hasNext ? `/api/games?genre=${genreId}&page=${page + 1}` : null
  });
}
__name(onRequestGet3, "onRequestGet3");
__name2(onRequestGet3, "onRequestGet");
async function onRequestOptions4() {
  return handleOptions();
}
__name(onRequestOptions4, "onRequestOptions4");
__name2(onRequestOptions4, "onRequestOptions");
async function onRequestGet4() {
  const genresList = Object.entries(GENRES).map(([gid, [gname]]) => ({
    id: gid,
    name: gname,
    url: `/api/games?genre=${gid}&page=1`
  }));
  return jsonResponse({
    api_version: "2.0",
    total_genres: genresList.length,
    genres: genresList
  });
}
__name(onRequestGet4, "onRequestGet4");
__name2(onRequestGet4, "onRequestGet");
async function onRequestOptions5() {
  return handleOptions();
}
__name(onRequestOptions5, "onRequestOptions5");
__name2(onRequestOptions5, "onRequestOptions");
async function onRequestGet5() {
  try {
    const [games] = await getGames("2", null, 1);
    return jsonResponse({
      status: games.length > 0 ? "healthy" : "degraded",
      timestamp: Math.floor(Date.now() / 1e3)
    });
  } catch (e) {
    return jsonResponse({ status: "fail", error: String(e) }, 500);
  }
}
__name(onRequestGet5, "onRequestGet5");
__name2(onRequestGet5, "onRequestGet");
async function onRequestOptions6() {
  return handleOptions();
}
__name(onRequestOptions6, "onRequestOptions6");
__name2(onRequestOptions6, "onRequestOptions");
async function onRequestGet6({ request }) {
  const url = new URL(request.url);
  const query = url.searchParams.get("q") || "";
  const page = parseInt(url.searchParams.get("page") || "1", 10);
  if (!query) {
    return jsonResponse({ error: "Query required" }, 400);
  }
  const [games, hasNext] = await getGames(null, query, page);
  return jsonResponse({
    status: "success",
    search_query: query,
    total_results: games.length,
    page,
    has_next: hasNext,
    games,
    previous: page > 1 ? `/api/search?q=${encodeURIComponent(query)}&page=${page - 1}` : null,
    next: hasNext ? `/api/search?q=${encodeURIComponent(query)}&page=${page + 1}` : null
  });
}
__name(onRequestGet6, "onRequestGet6");
__name2(onRequestGet6, "onRequestGet");
async function onRequestOptions7() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    }
  });
}
__name(onRequestOptions7, "onRequestOptions7");
__name2(onRequestOptions7, "onRequestOptions");
async function onRequestGet7({ params }) {
  const encoded = Array.isArray(params.path) ? params.path[0] : params.path;
  if (!encoded) {
    return new Response("Not found", { status: 404 });
  }
  try {
    const base64 = encoded;
    const regularBase64 = base64.replace(/-/g, "+").replace(/_/g, "/");
    const paddingLength = (4 - regularBase64.length % 4) % 4;
    const padded = regularBase64 + "=".repeat(paddingLength);
    const originalUrl = atob(padded);
    if (!originalUrl.startsWith("http")) {
      return new Response("Invalid URL", { status: 400 });
    }
    const res = await fetch(originalUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://koyso.com/",
        "Accept": "image/webp,image/*,*/*"
      }
    });
    if (!res.ok) {
      return new Response("Media not available", { status: 404 });
    }
    const contentType = res.headers.get("Content-Type") || "application/octet-stream";
    const body = await res.arrayBuffer();
    return new Response(body, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=31536000",
        "Access-Control-Allow-Origin": "*"
      }
    });
  } catch {
    return new Response("Media not available", { status: 404 });
  }
}
__name(onRequestGet7, "onRequestGet7");
__name2(onRequestGet7, "onRequestGet");
function onRequestGet8() {
  console.log("ROOT PATH HIT!");
  return new Response("Root path works!", {
    status: 200,
    headers: { "Content-Type": "text/plain" }
  });
}
__name(onRequestGet8, "onRequestGet8");
__name2(onRequestGet8, "onRequestGet");
function onRequestOptions8() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Accept"
    }
  });
}
__name(onRequestOptions8, "onRequestOptions8");
__name2(onRequestOptions8, "onRequestOptions");
function onRequest({ request }) {
  const url = new URL(request.url);
  if (url.pathname === "/") {
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
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });
  }
  if (url.pathname === "/favicon.ico") {
    return new Response(null, { status: 204 });
  }
  return new Response(JSON.stringify({ error: "Not found" }), {
    status: 404,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"
    }
  });
}
__name(onRequest, "onRequest");
__name2(onRequest, "onRequest");
var routes = [
  {
    routePath: "/api/download/:id",
    mountPath: "/api/download",
    method: "GET",
    middlewares: [],
    modules: [onRequestGet]
  },
  {
    routePath: "/api/download/:id",
    mountPath: "/api/download",
    method: "OPTIONS",
    middlewares: [],
    modules: [onRequestOptions]
  },
  {
    routePath: "/api/game/:id",
    mountPath: "/api/game",
    method: "GET",
    middlewares: [],
    modules: [onRequestGet2]
  },
  {
    routePath: "/api/game/:id",
    mountPath: "/api/game",
    method: "OPTIONS",
    middlewares: [],
    modules: [onRequestOptions2]
  },
  {
    routePath: "/api/games",
    mountPath: "/api",
    method: "GET",
    middlewares: [],
    modules: [onRequestGet3]
  },
  {
    routePath: "/api/games",
    mountPath: "/api",
    method: "OPTIONS",
    middlewares: [],
    modules: [onRequestOptions3]
  },
  {
    routePath: "/api/genres",
    mountPath: "/api",
    method: "GET",
    middlewares: [],
    modules: [onRequestGet4]
  },
  {
    routePath: "/api/genres",
    mountPath: "/api",
    method: "OPTIONS",
    middlewares: [],
    modules: [onRequestOptions4]
  },
  {
    routePath: "/api/health",
    mountPath: "/api",
    method: "GET",
    middlewares: [],
    modules: [onRequestGet5]
  },
  {
    routePath: "/api/health",
    mountPath: "/api",
    method: "OPTIONS",
    middlewares: [],
    modules: [onRequestOptions5]
  },
  {
    routePath: "/api/search",
    mountPath: "/api",
    method: "GET",
    middlewares: [],
    modules: [onRequestGet6]
  },
  {
    routePath: "/api/search",
    mountPath: "/api",
    method: "OPTIONS",
    middlewares: [],
    modules: [onRequestOptions6]
  },
  {
    routePath: "/proxy/:path*",
    mountPath: "/proxy",
    method: "GET",
    middlewares: [],
    modules: [onRequestGet7]
  },
  {
    routePath: "/proxy/:path*",
    mountPath: "/proxy",
    method: "OPTIONS",
    middlewares: [],
    modules: [onRequestOptions7]
  },
  {
    routePath: "/_index",
    mountPath: "/",
    method: "GET",
    middlewares: [],
    modules: [onRequestGet8]
  },
  {
    routePath: "/:path*",
    mountPath: "/",
    method: "OPTIONS",
    middlewares: [],
    modules: [onRequestOptions8]
  },
  {
    routePath: "/:path*",
    mountPath: "/",
    method: "",
    middlewares: [],
    modules: [onRequest]
  }
];
function lexer(str) {
  var tokens = [];
  var i = 0;
  while (i < str.length) {
    var char = str[i];
    if (char === "*" || char === "+" || char === "?") {
      tokens.push({ type: "MODIFIER", index: i, value: str[i++] });
      continue;
    }
    if (char === "\\") {
      tokens.push({ type: "ESCAPED_CHAR", index: i++, value: str[i++] });
      continue;
    }
    if (char === "{") {
      tokens.push({ type: "OPEN", index: i, value: str[i++] });
      continue;
    }
    if (char === "}") {
      tokens.push({ type: "CLOSE", index: i, value: str[i++] });
      continue;
    }
    if (char === ":") {
      var name = "";
      var j = i + 1;
      while (j < str.length) {
        var code = str.charCodeAt(j);
        if (
          // `0-9`
          code >= 48 && code <= 57 || // `A-Z`
          code >= 65 && code <= 90 || // `a-z`
          code >= 97 && code <= 122 || // `_`
          code === 95
        ) {
          name += str[j++];
          continue;
        }
        break;
      }
      if (!name)
        throw new TypeError("Missing parameter name at ".concat(i));
      tokens.push({ type: "NAME", index: i, value: name });
      i = j;
      continue;
    }
    if (char === "(") {
      var count = 1;
      var pattern = "";
      var j = i + 1;
      if (str[j] === "?") {
        throw new TypeError('Pattern cannot start with "?" at '.concat(j));
      }
      while (j < str.length) {
        if (str[j] === "\\") {
          pattern += str[j++] + str[j++];
          continue;
        }
        if (str[j] === ")") {
          count--;
          if (count === 0) {
            j++;
            break;
          }
        } else if (str[j] === "(") {
          count++;
          if (str[j + 1] !== "?") {
            throw new TypeError("Capturing groups are not allowed at ".concat(j));
          }
        }
        pattern += str[j++];
      }
      if (count)
        throw new TypeError("Unbalanced pattern at ".concat(i));
      if (!pattern)
        throw new TypeError("Missing pattern at ".concat(i));
      tokens.push({ type: "PATTERN", index: i, value: pattern });
      i = j;
      continue;
    }
    tokens.push({ type: "CHAR", index: i, value: str[i++] });
  }
  tokens.push({ type: "END", index: i, value: "" });
  return tokens;
}
__name(lexer, "lexer");
__name2(lexer, "lexer");
function parse(str, options) {
  if (options === void 0) {
    options = {};
  }
  var tokens = lexer(str);
  var _a = options.prefixes, prefixes = _a === void 0 ? "./" : _a, _b = options.delimiter, delimiter = _b === void 0 ? "/#?" : _b;
  var result = [];
  var key = 0;
  var i = 0;
  var path = "";
  var tryConsume = /* @__PURE__ */ __name2(function(type) {
    if (i < tokens.length && tokens[i].type === type)
      return tokens[i++].value;
  }, "tryConsume");
  var mustConsume = /* @__PURE__ */ __name2(function(type) {
    var value2 = tryConsume(type);
    if (value2 !== void 0)
      return value2;
    var _a2 = tokens[i], nextType = _a2.type, index = _a2.index;
    throw new TypeError("Unexpected ".concat(nextType, " at ").concat(index, ", expected ").concat(type));
  }, "mustConsume");
  var consumeText = /* @__PURE__ */ __name2(function() {
    var result2 = "";
    var value2;
    while (value2 = tryConsume("CHAR") || tryConsume("ESCAPED_CHAR")) {
      result2 += value2;
    }
    return result2;
  }, "consumeText");
  var isSafe = /* @__PURE__ */ __name2(function(value2) {
    for (var _i = 0, delimiter_1 = delimiter; _i < delimiter_1.length; _i++) {
      var char2 = delimiter_1[_i];
      if (value2.indexOf(char2) > -1)
        return true;
    }
    return false;
  }, "isSafe");
  var safePattern = /* @__PURE__ */ __name2(function(prefix2) {
    var prev = result[result.length - 1];
    var prevText = prefix2 || (prev && typeof prev === "string" ? prev : "");
    if (prev && !prevText) {
      throw new TypeError('Must have text between two parameters, missing text after "'.concat(prev.name, '"'));
    }
    if (!prevText || isSafe(prevText))
      return "[^".concat(escapeString(delimiter), "]+?");
    return "(?:(?!".concat(escapeString(prevText), ")[^").concat(escapeString(delimiter), "])+?");
  }, "safePattern");
  while (i < tokens.length) {
    var char = tryConsume("CHAR");
    var name = tryConsume("NAME");
    var pattern = tryConsume("PATTERN");
    if (name || pattern) {
      var prefix = char || "";
      if (prefixes.indexOf(prefix) === -1) {
        path += prefix;
        prefix = "";
      }
      if (path) {
        result.push(path);
        path = "";
      }
      result.push({
        name: name || key++,
        prefix,
        suffix: "",
        pattern: pattern || safePattern(prefix),
        modifier: tryConsume("MODIFIER") || ""
      });
      continue;
    }
    var value = char || tryConsume("ESCAPED_CHAR");
    if (value) {
      path += value;
      continue;
    }
    if (path) {
      result.push(path);
      path = "";
    }
    var open = tryConsume("OPEN");
    if (open) {
      var prefix = consumeText();
      var name_1 = tryConsume("NAME") || "";
      var pattern_1 = tryConsume("PATTERN") || "";
      var suffix = consumeText();
      mustConsume("CLOSE");
      result.push({
        name: name_1 || (pattern_1 ? key++ : ""),
        pattern: name_1 && !pattern_1 ? safePattern(prefix) : pattern_1,
        prefix,
        suffix,
        modifier: tryConsume("MODIFIER") || ""
      });
      continue;
    }
    mustConsume("END");
  }
  return result;
}
__name(parse, "parse");
__name2(parse, "parse");
function match(str, options) {
  var keys = [];
  var re = pathToRegexp(str, keys, options);
  return regexpToFunction(re, keys, options);
}
__name(match, "match");
__name2(match, "match");
function regexpToFunction(re, keys, options) {
  if (options === void 0) {
    options = {};
  }
  var _a = options.decode, decode = _a === void 0 ? function(x) {
    return x;
  } : _a;
  return function(pathname) {
    var m = re.exec(pathname);
    if (!m)
      return false;
    var path = m[0], index = m.index;
    var params = /* @__PURE__ */ Object.create(null);
    var _loop_1 = /* @__PURE__ */ __name2(function(i2) {
      if (m[i2] === void 0)
        return "continue";
      var key = keys[i2 - 1];
      if (key.modifier === "*" || key.modifier === "+") {
        params[key.name] = m[i2].split(key.prefix + key.suffix).map(function(value) {
          return decode(value, key);
        });
      } else {
        params[key.name] = decode(m[i2], key);
      }
    }, "_loop_1");
    for (var i = 1; i < m.length; i++) {
      _loop_1(i);
    }
    return { path, index, params };
  };
}
__name(regexpToFunction, "regexpToFunction");
__name2(regexpToFunction, "regexpToFunction");
function escapeString(str) {
  return str.replace(/([.+*?=^!:${}()[\]|/\\])/g, "\\$1");
}
__name(escapeString, "escapeString");
__name2(escapeString, "escapeString");
function flags(options) {
  return options && options.sensitive ? "" : "i";
}
__name(flags, "flags");
__name2(flags, "flags");
function regexpToRegexp(path, keys) {
  if (!keys)
    return path;
  var groupsRegex = /\((?:\?<(.*?)>)?(?!\?)/g;
  var index = 0;
  var execResult = groupsRegex.exec(path.source);
  while (execResult) {
    keys.push({
      // Use parenthesized substring match if available, index otherwise
      name: execResult[1] || index++,
      prefix: "",
      suffix: "",
      modifier: "",
      pattern: ""
    });
    execResult = groupsRegex.exec(path.source);
  }
  return path;
}
__name(regexpToRegexp, "regexpToRegexp");
__name2(regexpToRegexp, "regexpToRegexp");
function arrayToRegexp(paths, keys, options) {
  var parts = paths.map(function(path) {
    return pathToRegexp(path, keys, options).source;
  });
  return new RegExp("(?:".concat(parts.join("|"), ")"), flags(options));
}
__name(arrayToRegexp, "arrayToRegexp");
__name2(arrayToRegexp, "arrayToRegexp");
function stringToRegexp(path, keys, options) {
  return tokensToRegexp(parse(path, options), keys, options);
}
__name(stringToRegexp, "stringToRegexp");
__name2(stringToRegexp, "stringToRegexp");
function tokensToRegexp(tokens, keys, options) {
  if (options === void 0) {
    options = {};
  }
  var _a = options.strict, strict = _a === void 0 ? false : _a, _b = options.start, start = _b === void 0 ? true : _b, _c = options.end, end = _c === void 0 ? true : _c, _d = options.encode, encode = _d === void 0 ? function(x) {
    return x;
  } : _d, _e = options.delimiter, delimiter = _e === void 0 ? "/#?" : _e, _f = options.endsWith, endsWith = _f === void 0 ? "" : _f;
  var endsWithRe = "[".concat(escapeString(endsWith), "]|$");
  var delimiterRe = "[".concat(escapeString(delimiter), "]");
  var route = start ? "^" : "";
  for (var _i = 0, tokens_1 = tokens; _i < tokens_1.length; _i++) {
    var token = tokens_1[_i];
    if (typeof token === "string") {
      route += escapeString(encode(token));
    } else {
      var prefix = escapeString(encode(token.prefix));
      var suffix = escapeString(encode(token.suffix));
      if (token.pattern) {
        if (keys)
          keys.push(token);
        if (prefix || suffix) {
          if (token.modifier === "+" || token.modifier === "*") {
            var mod = token.modifier === "*" ? "?" : "";
            route += "(?:".concat(prefix, "((?:").concat(token.pattern, ")(?:").concat(suffix).concat(prefix, "(?:").concat(token.pattern, "))*)").concat(suffix, ")").concat(mod);
          } else {
            route += "(?:".concat(prefix, "(").concat(token.pattern, ")").concat(suffix, ")").concat(token.modifier);
          }
        } else {
          if (token.modifier === "+" || token.modifier === "*") {
            throw new TypeError('Can not repeat "'.concat(token.name, '" without a prefix and suffix'));
          }
          route += "(".concat(token.pattern, ")").concat(token.modifier);
        }
      } else {
        route += "(?:".concat(prefix).concat(suffix, ")").concat(token.modifier);
      }
    }
  }
  if (end) {
    if (!strict)
      route += "".concat(delimiterRe, "?");
    route += !options.endsWith ? "$" : "(?=".concat(endsWithRe, ")");
  } else {
    var endToken = tokens[tokens.length - 1];
    var isEndDelimited = typeof endToken === "string" ? delimiterRe.indexOf(endToken[endToken.length - 1]) > -1 : endToken === void 0;
    if (!strict) {
      route += "(?:".concat(delimiterRe, "(?=").concat(endsWithRe, "))?");
    }
    if (!isEndDelimited) {
      route += "(?=".concat(delimiterRe, "|").concat(endsWithRe, ")");
    }
  }
  return new RegExp(route, flags(options));
}
__name(tokensToRegexp, "tokensToRegexp");
__name2(tokensToRegexp, "tokensToRegexp");
function pathToRegexp(path, keys, options) {
  if (path instanceof RegExp)
    return regexpToRegexp(path, keys);
  if (Array.isArray(path))
    return arrayToRegexp(path, keys, options);
  return stringToRegexp(path, keys, options);
}
__name(pathToRegexp, "pathToRegexp");
__name2(pathToRegexp, "pathToRegexp");
var escapeRegex = /[.+?^${}()|[\]\\]/g;
function* executeRequest(request) {
  const requestPath = new URL(request.url).pathname;
  for (const route of [...routes].reverse()) {
    if (route.method && route.method !== request.method) {
      continue;
    }
    const routeMatcher = match(route.routePath.replace(escapeRegex, "\\$&"), {
      end: false
    });
    const mountMatcher = match(route.mountPath.replace(escapeRegex, "\\$&"), {
      end: false
    });
    const matchResult = routeMatcher(requestPath);
    const mountMatchResult = mountMatcher(requestPath);
    if (matchResult && mountMatchResult) {
      for (const handler of route.middlewares.flat()) {
        yield {
          handler,
          params: matchResult.params,
          path: mountMatchResult.path
        };
      }
    }
  }
  for (const route of routes) {
    if (route.method && route.method !== request.method) {
      continue;
    }
    const routeMatcher = match(route.routePath.replace(escapeRegex, "\\$&"), {
      end: true
    });
    const mountMatcher = match(route.mountPath.replace(escapeRegex, "\\$&"), {
      end: false
    });
    const matchResult = routeMatcher(requestPath);
    const mountMatchResult = mountMatcher(requestPath);
    if (matchResult && mountMatchResult && route.modules.length) {
      for (const handler of route.modules.flat()) {
        yield {
          handler,
          params: matchResult.params,
          path: matchResult.path
        };
      }
      break;
    }
  }
}
__name(executeRequest, "executeRequest");
__name2(executeRequest, "executeRequest");
var pages_template_worker_default = {
  async fetch(originalRequest, env, workerContext) {
    let request = originalRequest;
    const handlerIterator = executeRequest(request);
    let data = {};
    let isFailOpen = false;
    const next = /* @__PURE__ */ __name2(async (input, init) => {
      if (input !== void 0) {
        let url = input;
        if (typeof input === "string") {
          url = new URL(input, request.url).toString();
        }
        request = new Request(url, init);
      }
      const result = handlerIterator.next();
      if (result.done === false) {
        const { handler, params, path } = result.value;
        const context = {
          request: new Request(request.clone()),
          functionPath: path,
          next,
          params,
          get data() {
            return data;
          },
          set data(value) {
            if (typeof value !== "object" || value === null) {
              throw new Error("context.data must be an object");
            }
            data = value;
          },
          env,
          waitUntil: workerContext.waitUntil.bind(workerContext),
          passThroughOnException: /* @__PURE__ */ __name2(() => {
            isFailOpen = true;
          }, "passThroughOnException")
        };
        const response = await handler(context);
        if (!(response instanceof Response)) {
          throw new Error("Your Pages function should return a Response");
        }
        return cloneResponse(response);
      } else if ("ASSETS") {
        const response = await env["ASSETS"].fetch(request);
        return cloneResponse(response);
      } else {
        const response = await fetch(request);
        return cloneResponse(response);
      }
    }, "next");
    try {
      return await next();
    } catch (error) {
      if (isFailOpen) {
        const response = await env["ASSETS"].fetch(request);
        return cloneResponse(response);
      }
      throw error;
    }
  }
};
var cloneResponse = /* @__PURE__ */ __name2((response) => (
  // https://fetch.spec.whatwg.org/#null-body-status
  new Response(
    [101, 204, 205, 304].includes(response.status) ? null : response.body,
    response
  )
), "cloneResponse");
var drainBody = /* @__PURE__ */ __name2(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
__name2(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name2(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError(e);
    return Response.json(error, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = pages_template_worker_default;
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
__name2(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
__name2(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");
__name2(__facade_invoke__, "__facade_invoke__");
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  static {
    __name(this, "___Facade_ScheduledController__");
  }
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  static {
    __name2(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name2(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name2(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
__name2(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name2((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name2((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
__name2(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;

// ../../AppData/Local/nvm/v22.22.2/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
var drainBody2 = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default2 = drainBody2;

// ../../AppData/Local/nvm/v22.22.2/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
function reduceError2(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError2(e.cause)
  };
}
__name(reduceError2, "reduceError");
var jsonError2 = /* @__PURE__ */ __name(async (request, env, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env);
  } catch (e) {
    const error = reduceError2(e);
    return Response.json(error, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default2 = jsonError2;

// .wrangler/tmp/bundle-nIICd7/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__2 = [
  middleware_ensure_req_body_drained_default2,
  middleware_miniflare3_json_error_default2
];
var middleware_insertion_facade_default2 = middleware_loader_entry_default;

// ../../AppData/Local/nvm/v22.22.2/node_modules/wrangler/templates/middleware/common.ts
var __facade_middleware__2 = [];
function __facade_register__2(...args) {
  __facade_middleware__2.push(...args.flat());
}
__name(__facade_register__2, "__facade_register__");
function __facade_invokeChain__2(request, env, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__2(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env, ctx, middlewareCtx);
}
__name(__facade_invokeChain__2, "__facade_invokeChain__");
function __facade_invoke__2(request, env, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__2(request, env, ctx, dispatch, [
    ...__facade_middleware__2,
    finalMiddleware
  ]);
}
__name(__facade_invoke__2, "__facade_invoke__");

// .wrangler/tmp/bundle-nIICd7/middleware-loader.entry.ts
var __Facade_ScheduledController__2 = class ___Facade_ScheduledController__2 {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__2)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler2(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__2 === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__2.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__2) {
    __facade_register__2(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__2(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__2(request, env, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler2, "wrapExportedHandler");
function wrapWorkerEntrypoint2(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__2 === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__2.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__2) {
    __facade_register__2(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env, ctx) => {
      this.env = env;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__2(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__2(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint2, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY2;
if (typeof middleware_insertion_facade_default2 === "object") {
  WRAPPED_ENTRY2 = wrapExportedHandler2(middleware_insertion_facade_default2);
} else if (typeof middleware_insertion_facade_default2 === "function") {
  WRAPPED_ENTRY2 = wrapWorkerEntrypoint2(middleware_insertion_facade_default2);
}
var middleware_loader_entry_default2 = WRAPPED_ENTRY2;
export {
  __INTERNAL_WRANGLER_MIDDLEWARE__2 as __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default2 as default
};
//# sourceMappingURL=functionsWorker-0.7706995711696913.js.map
