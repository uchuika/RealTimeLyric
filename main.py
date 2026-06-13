import asyncio
import json

from shazamio import Shazam
import webview

from html.parser import HTMLParser
from urllib.request import quote, unquote, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


class NextDataParser(HTMLParser):
    """TextAliveページに埋め込まれたNext.jsのJSONを取り出す。"""

    def __init__(self):
        super().__init__()
        self.in_next_data = False
        self.next_data = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and attributes.get("id") == "__NEXT_DATA__":
            self.in_next_data = True

    def handle_data(self, data):
        if self.in_next_data:
            self.next_data.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_next_data:
            self.in_next_data = False


class Api:
    def add(self, a, b):
        print("python")
        return a + b

    def pyprint(self, data):
        print(data)

    def selectMusic(self):
        file_types = ('Audio Files (*.mp3)', 'All files (*.*)')
        music_paths = window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True, file_types=file_types)

        if not music_paths:
            return []

        return [
            asyncio.run(analyzeMusic(music_path))
            for music_path in music_paths
        ]


async def analyzeMusic(music_path):
    shazam = Shazam()
    try:
        result = await shazam.recognize(music_path)
    except Exception as error:
        return {
            "recognized": False,
            "file": music_path,
            "message": f"解析に失敗しました: {error}",
        }

    track = result.get("track")
    if not result.get("matches") or not track:
        return {
            "recognized": False,
            "file": music_path,
            "message": "曲を特定できませんでした",
        }

    #
    keyword = track.get("title", "") + " " + track.get("subtitle", "")
    songs = search_songle(keyword=keyword)
    print("検索: " + keyword)

    if not songs:
        print("TextAliveに歌詞が登録されている楽曲は見つかりませんでした。")

    for index, song in enumerate(songs, start=1):
        print(f"\n{index}. {song['title']}")
        print(f"   アーティスト: {song['artist']}")
        print(f"   配信元: {song['source']}")
        print(f"   楽曲URL: {song['source_url']}")
        print(f"   Songle: {song['songle_url']}")

    images = track.get("images", {})
    return {
        "recognized": True,
        "file": music_path,
        "title": track.get("title", "不明"),
        "artist": track.get("subtitle", "不明"),
        "imageUrl": images.get("coverarthq") or images.get("coverart"),
        "shazamUrl": track.get("share", {}).get("href"),
    }


def has_textalive_lyrics(songle_url):
    # TexAliveでの対象楽曲の歌詞解析が利用可能かどうか確認する
    song_path = songle_url.split("/songs/", 1)[-1]
    textalive_url = f"https://textalive.jp/songs/{song_path}"
    request = Request(textalive_url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urlopen(request, timeout=10) as response:
            html = response.read().decode("utf-8")

        parser = NextDataParser()
        parser.feed(html)
        if not parser.next_data:
            return False

        data = json.loads("".join(parser.next_data))

        return bool(
            data.get("props", {})
            .get("pageProps", {})
            .get("song", {})
            .get("status", {})
            .get("lyrics")
        )

    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False


def search_songle(keyword, limit=20):
    # songle内のデータベースをキーワードで検索
    url = f"https://songle.jp/songs/search.rss?q={quote(keyword)}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(request, timeout=10) as response:
        root = ET.fromstring(response.read())

    results = []

    # レスポンス解析
    for item in root.findall("./channel/item"):
        songle_url = item.findtext("link", "")
        if not songle_url or not has_textalive_lyrics(songle_url):
            continue

        songle_path = unquote(songle_url.split("/songs/", 1)[-1])
        source_url = (
            songle_path
            if songle_path.startswith(("http://", "https://"))
            else f"https://{songle_path}"
        )

        results.append({
            "title": item.findtext("title", ""),
            "artist": item.findtext("author", ""),
            "source": urlparse(source_url).hostname,
            "source_url": source_url,
            "songle_url": songle_url,
        })

        if len(results) >= limit:
            break
    return results


api = Api()
window = webview.create_window(
    "RealTimeLyric", url="web/index.html", js_api=api)
webview.start(http_server=True, debug=True)
