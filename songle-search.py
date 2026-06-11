from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


def search_songle(keyword, limit=10):
    url = f"https://songle.jp/songs/search.rss?q={quote(keyword)}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(request, timeout=10) as response:
        root = ET.fromstring(response.read())

    results = []

    for item in root.findall("./channel/item")[:limit]:
        songle_url = item.findtext("link", "")
        song_path = unquote(songle_url.split("/songs/", 1)[-1])
        source_url = (
            song_path
            if song_path.startswith(("http://", "https://"))
            else f"https://{song_path}"
        )

        results.append({
            "title": item.findtext("title", ""),
            "artist": item.findtext("author", ""),
            "source": urlparse(source_url).hostname,
            "source_url": source_url,
            "songle_url": songle_url,
        })

    return results


if __name__ == "__main__":
    keyword = input("曲名・アーティスト名: ")

    for index, song in enumerate(search_songle(keyword), start=1):
        print(f"\n{index}. {song['title']}")
        print(f"   アーティスト: {song['artist']}")
        print(f"   配信元: {song['source']}")
        print(f"   楽曲URL: {song['source_url']}")
        print(f"   Songle: {song['songle_url']}")
