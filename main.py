import asyncio

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

    images = track.get("images", {})
    return {
        "recognized": True,
        "file": music_path,
        "title": track.get("title", "不明"),
        "artist": track.get("subtitle", "不明"),
        "imageUrl": images.get("coverarthq") or images.get("coverart"),
        "shazamUrl": track.get("share", {}).get("href"),
    }

api = Api()
window = webview.create_window(
    "RealTimeLyric", url="web/index.html", js_api=api)
webview.start(http_server=True, debug=True)
