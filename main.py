import asyncio
import json
import os
import tempfile
import wave

from shazamio import Shazam
import webview

from typing import Any
from html.parser import HTMLParser
from urllib.request import quote, unquote, urlparse
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import xml.etree.ElementTree as ET


SYSTEM_AUDIO_RECORD_SECONDS = 12
SYSTEM_AUDIO_CHUNK_SIZE = 1024


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

    def recognizePlayingMusic(self):
        audio_path = None

        try:
            audio_path = record_system_audio(SYSTEM_AUDIO_RECORD_SECONDS)
            result = asyncio.run(analyzeMusic(audio_path))
            result["file"] = "再生中の音声"
            return [result]
        except Exception as error:
            return [{
                "recognized": False,
                "file": "再生中の音声",
                "message": f"録音または解析に失敗しました: {error}",
            }]
        finally:
            if audio_path:
                try:
                    os.remove(audio_path)
                except OSError:
                    pass


def record_system_audio(seconds=SYSTEM_AUDIO_RECORD_SECONDS):
    try:
        import pyaudiowpatch as pyaudio
    except ImportError as error:
        raise RuntimeError(
            "PyAudioWPatchがインストールされていません"
        ) from error

    audio = pyaudio.PyAudio()
    stream = None
    audio_path = None

    try:
        device = audio.get_default_wasapi_loopback()
        channels = int(device["maxInputChannels"])
        sample_rate = int(device["defaultSampleRate"])
        audio_format = pyaudio.paInt16

        if channels < 1:
            raise RuntimeError("既定のスピーカーを録音できません")

        stream = audio.open(
            format=audio_format,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=device["index"],
            frames_per_buffer=SYSTEM_AUDIO_CHUNK_SIZE,
        )

        frames = []
        frame_count = int(
            sample_rate / SYSTEM_AUDIO_CHUNK_SIZE * seconds
        )
        for _ in range(frame_count):
            frames.append(stream.read(
                SYSTEM_AUDIO_CHUNK_SIZE,
                exception_on_overflow=False,
            ))

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as temporary_file:
            audio_path = temporary_file.name

        with wave.open(audio_path, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(audio.get_sample_size(audio_format))
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"".join(frames))

        return audio_path
    except Exception:
        if audio_path:
            try:
                os.remove(audio_path)
            except OSError:
                pass
        raise
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        audio.terminate()


async def analyzeMusic(music_path):
    shazam = Shazam(language="ja-JP", endpoint_country="JP")
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

    # タイトルとアーティスト名で検索
    keyword = track.get("title", "") + " " + track.get("subtitle", "")
    songs = search_songle(keyword=keyword)
    print("検索: " + keyword)

    # 上の検索で見つからなければタイトルだけで検索
    if not songs:
        keyword = track.get("title", "")
        songs = search_songle(keyword=keyword)
        print("検索: " + keyword)

    if not songs:
        print("TextAliveに歌詞が登録されている楽曲は見つかりませんでした。")

    if not songs:
        return {
            "recognized": False,
            "file": music_path,
            "message": "TextAliveで歌詞が登録されている楽曲が見つかりませんでした",
        }

    for index, song in enumerate(songs, start=1):
        print(f"\n{index}. {song['title']}")
        print(f"   アーティスト: {song['artist']}")
        print(f"   配信元: {song['source']}")
        print(f"   楽曲URL: {song['source_url']}")
        print(f"   Songle: {song['songle_url']}")

    song = songs[0]
    songleurl = song['songle_url']
    images = track.get("images", {})
    return {
        "recognized": True,
        "file": music_path,
        "title": track.get("title", "不明"),
        "artist": track.get("subtitle", "不明"),
        "imageUrl": images.get("coverarthq") or images.get("coverart"),
        "shazamUrl": track.get("share", {}).get("href"),
        "sourceUrl": song["source_url"],
        "songlUrl": songleurl,
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
        if not isinstance(data, dict):
            return False

        props = data.get("props")
        if not isinstance(props, dict):
            return False

        page_props = props.get("pageProps")
        if not isinstance(page_props, dict):
            return False

        song = page_props.get("song")
        if not isinstance(song, dict):
            return False

        status = song.get("status")
        if not isinstance(status, dict):
            return False

        return bool(status.get("lyrics"))

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
