const http = require("http");
const fs = require("fs");
const path = require("path");

const root = __dirname;
const port = Number(process.env.PORT) || 3000;
const mimeTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

function decodeXml(value) {
  return value
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, "\"")
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&#x([\da-f]+);/gi, (_, code) => String.fromCodePoint(parseInt(code, 16)));
}

function readXmlTag(xml, tag) {
  const match = xml.match(new RegExp(`<${tag}>(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?</${tag}>`));
  return match ? decodeXml(match[1].trim()) : "";
}

function getSourceUrl(songleUrl) {
  const marker = "/songs/";
  const index = songleUrl.indexOf(marker);
  if (index < 0) {
    return "";
  }

  const songPath = decodeURIComponent(songleUrl.slice(index + marker.length));
  return /^https?:\/\//i.test(songPath) ? songPath : `https://${songPath}`;
}

function getSourceName(sourceUrl) {
  try {
    const hostname = new URL(sourceUrl).hostname.replace(/^www\./, "");
    const names = {
      "youtube.com": "YouTube",
      "youtu.be": "YouTube",
      "nicovideo.jp": "ニコニコ動画",
      "piapro.jp": "Piapro",
      "soundcloud.com": "SoundCloud",
    };
    return names[hostname] || hostname;
  } catch {
    return "その他";
  }
}

async function searchSongle(query) {
  const endpoint = new URL("https://songle.jp/songs/search.rss");
  endpoint.searchParams.set("q", query);

  const upstream = await fetch(endpoint, {
    headers: {
      "Accept": "application/rss+xml, application/xml;q=0.9",
      "User-Agent": "TextAliveLyricsTest/1.0",
    },
  });
  if (!upstream.ok) {
    throw new Error(`Songle search returned HTTP ${upstream.status}`);
  }

  const xml = await upstream.text();
  return [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)]
    .slice(0, 30)
    .map((match) => {
      const itemXml = match[1];
      const songleUrl = readXmlTag(itemXml, "link");
      const sourceUrl = getSourceUrl(songleUrl);
      return {
        title: readXmlTag(itemXml, "title"),
        artist: readXmlTag(itemXml, "author"),
        songleUrl,
        sourceUrl,
        source: getSourceName(sourceUrl),
      };
    })
    .filter((item) => item.sourceUrl);
}

function sendJson(response, status, body) {
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  response.end(JSON.stringify(body));
}

const server = http.createServer(async (request, response) => {
  const requestUrl = new URL(request.url, "http://localhost");
  const pathname = decodeURIComponent(requestUrl.pathname);

  if (pathname === "/api/search") {
    const query = requestUrl.searchParams.get("q")?.trim();
    if (!query) {
      sendJson(response, 400, { error: "検索キーワードを入力してください。" });
      return;
    }

    try {
      const items = await searchSongle(query);
      sendJson(response, 200, { items });
    } catch (error) {
      console.error(error);
      sendJson(response, 502, { error: "Songleの検索に失敗しました。" });
    }
    return;
  }

  const relativePath = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
  const filePath = path.resolve(root, relativePath);

  if (filePath !== root && !filePath.startsWith(`${root}${path.sep}`)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  fs.stat(filePath, (statError, stats) => {
    if (statError || !stats.isFile()) {
      response.writeHead(404);
      response.end("Not Found");
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeTypes[path.extname(filePath)] || "application/octet-stream",
    });
    fs.createReadStream(filePath).pipe(response);
  });
});

server.listen(port, () => {
  console.log(`TextAlive lyrics app: http://localhost:${port}`);
});
