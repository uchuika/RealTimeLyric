import asyncio
import json
import os
import sys
import tempfile
import wave
import time
from pathlib import Path

from shazamio import Shazam
import webview

from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


SYSTEM_AUDIO_RECORD_SECONDS = 5
SYSTEM_AUDIO_CHUNK_SIZE = 1024
LRCLIB_API_URL = "https://lrclib.net/api/get"

latest_song = None

# キャッシュデータベース用
engine = create_engine("sqlite:///lyrics_cache.db")

Base = declarative_base()
# データベースモデルクラス

# ToDo データベースによるキャッシュを実装
# class LyricsCache(Base):
#    __tablename__ = "lyrics_cache"
#
#    cache_key = Mapped[str] = mapped_column(String(255), primary_key=True)


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
            # 録音開始時刻
            record_started_at = time.monotonic()
            audio_path = record_system_audio(SYSTEM_AUDIO_RECORD_SECONDS)

            # 録音終了位置
            record_end_at = time.monotonic()
            # 録音期間の時刻を取得
            capture_anchor = record_end_at - record_started_at

            result = asyncio.run(analyzeMusic(audio_path, capture_anchor))

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


async def analyzeMusic(music_path, capture_anchor=None):
    global latest_song

    analyzeMusic_start_at = time.monotonic()

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
    matches = result.get("matches")

    if not matches or not track:
        print("曲を特定できませんでした")
        return {
            "recognized": False,
            "file": music_path,
            "message": "曲を特定できませんでした",
        }

    offset = float(matches[0].get("offset"))
    print(f"offset:{offset}")

    # 推定再生位置
    estimated_position = None

    if offset is not None and capture_anchor is not None:
        estimated_position = (
            float(offset) + capture_anchor)
    print(f"estimatedOffset:{estimated_position}")

    # タイトルとアーティスト名で検索
    keyword = track.get("title", "") + " " + track.get("subtitle", "")
    print("検索: " + keyword)

    # 同じ曲の場合歌詞取得をスキップ
    if latest_song == keyword:
        print("同じ曲なので再生位置を更新")
        return {
            "recognized": True,
            "file": music_path,
            "message": "同じ曲なので再生位置を更新",
            "title": track.get("title", "不明"),
            "artist": track.get("subtitle", "不明"),
            "lyricsProvider": "LRCLIB",
            "estimatedPosition": estimated_position,
        }

    analyzeMusic_end_at = time.monotonic()
    if estimated_position is not None:
        estimated_position += analyzeMusic_end_at - analyzeMusic_start_at
    print(f"estimatedOffset:{estimated_position}")

    lyrics_data = search_lrclib_lyrics(
        track_name=track.get("title", ""),
        artist_name=track.get("subtitle", ""),
    )
    if lyrics_data:
        lyrics_text = lyrics_data.get(
            "syncedLyrics") or lyrics_data.get("plainLyrics")
        images = track.get("images", {})
        latest_song = keyword
        return {
            "recognized": True,
            "file": music_path,
            "title": track.get("title", "不明"),
            "artist": track.get("subtitle", "不明"),
            "imageUrl": images.get("coverarthq") or images.get("coverart"),
            "shazamUrl": track.get("share", {}).get("href"),
            "lyricsProvider": "LRCLIB",
            "lyricsText": lyrics_text,
            "lyricsTrackName": lyrics_data.get("trackName"),
            "lyricsArtistName": lyrics_data.get("artistName"),
            "lyricsAlbumName": lyrics_data.get("albumName"),
            "estimatedPosition": estimated_position,
        }
    else:
        return {
            "recognized": False,
            "file": music_path,
            "message": "LRCLIBに歌詞が見つかりませんでした",
        }


def search_lrclib_lyrics(
    track_name: str,
    artist_name: Optional[str] = None,
    album_name: Optional[str] = None,
    duration: Optional[int] = None,
):
    params = {"track_name": track_name}

    if artist_name:
        params["artist_name"] = artist_name
    if album_name:
        params["album_name"] = album_name
    if duration:
        params["duration"] = str(duration)

    url = f"{LRCLIB_API_URL}?{urlencode(params)}"
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "RealTimeLyric/1.0",
    })

    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("LRCLIBで歌詞がみつかりました")
    except HTTPError as error:
        if error.code != 404:
            print(f"LRCLIB APIエラー: HTTP {error.code}")
        return None
    except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f"LRCLIB APIへの接続に失敗しました: {error}")
        return None

    if not isinstance(data, dict):
        return None

    if not data.get("syncedLyrics") and not data.get("plainLyrics"):
        return None

    return data


# def get_cached_lyrics(track):
#    #ToDo データベースによるキャッシュを実装

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

api = Api()
window = webview.create_window(
    "RealTimeLyric", url=str(BASE_DIR / "web" / "index.html"), js_api=api)
webview.start(http_server=True, debug=True)
