import asyncio
from pathlib import Path

import aiohttp
from shazamio import Shazam
import webview


class Api:
    def add(self, a, b):
        print("python")
        return a + b

    def pyprint(self, data):
        print(data)

    def selectMusic(self):
        file_types = ('Audio Files (*.mp3)', 'All files (*.*)')
        result = window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True, file_types=file_types)
        print(result)
        for music_path in result:
            asyncio.run(analyzeMusic(music_path))
        return result


async def analyzeMusic(music_path):
    shazam = Shazam()
    result = await shazam.recognize(music_path)

    if result.get("matches") and "track" in result:
        track = result["track"]
        print(f"曲名: {track.get('title', '不明')}")
        print(f"アーティスト: {track.get('subtitle', '不明')}")
        print(f"Shazam URL: {track.get('share', {}).get('href', 'なし')}")

        images = track.get("images", {})
        image_url = images.get("coverarthq") or images.get("converart")

        if not image_url:
            print("ジャケット画像がありません")
            return

        print(f"曲名: {track.get('title')}")
        print(f"画像URL: {image_url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                response.raise_for_status()
                Path("cover.jpg").write_bytes(await response.read())

        print("cover.jpg に保存しました")
    else:
        print("曲を特定できませんでした")

'''
if __name__ == "__main__":
    asyncio.run(analyzeMusic())
'''

api = Api()
window = webview.create_window(
    "RealTimeLyric", url="web/index.html", js_api=api)
webview.start(http_server=True, debug=True)
