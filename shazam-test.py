import asyncio
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from shazamio import Shazam


def lookup_japanese_metadata(adam_id: str) -> dict[str, Any] | None:
    """Apple Musicの日本向けカタログから楽曲情報を取得する。"""
    query = urlencode(
        {
            "id": adam_id,
            "country": "JP",
            "lang": "ja_jp",
            "entity": "song",
        }
    )
    url = f"https://itunes.apple.com/lookup?{query}"

    with urlopen(url, timeout=10) as response:
        data = json.load(response)

    songs = [
        item
        for item in data.get("results", [])
        if item.get("wrapperType") == "track"
    ]
    return songs[0] if songs else None


async def main() -> None:
    shazam = Shazam(language="ja-JP", endpoint_country="JP")
    result = await shazam.recognize("Assets/makein.mp3")

    if not result.get("matches") or "track" not in result:
        print("曲を特定できませんでした")
        return

    track = result["track"]
    title = track.get("title", "不明")
    artist = track.get("subtitle", "不明")

    adam_id = track.get("adamid")
    if adam_id:
        try:
            japanese_track = await asyncio.to_thread(
                lookup_japanese_metadata,
                str(adam_id),
            )
            if japanese_track:
                title = japanese_track.get("trackName", title)
                artist = japanese_track.get("artistName", artist)
        except Exception as error:
            print(f"日本語の楽曲情報を取得できませんでした: {error}")

    print(f"曲名: {title}")
    print(f"作者名: {artist}")
    print(f"Shazam URL: {track.get('share', {}).get('href', 'なし')}")


if __name__ == "__main__":
    asyncio.run(main())
