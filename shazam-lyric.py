import argparse
import asyncio
from pathlib import Path
from typing import Any

from shazamio import Shazam


def extract_lyrics(track_details: dict[str, Any]) -> str | None:
    """トラック詳細から歌詞を取り出す。"""
    for section in track_details.get("sections", []):
        if section.get("type") != "LYRICS":
            continue

        lines = section.get("text", [])
        if lines:
            return "\n".join(lines)

    return None


async def recognize_and_display_lyrics(audio_path: Path) -> None:
    shazam = Shazam(language="ja-JP", endpoint_country="JP")
    result = await shazam.recognize(str(audio_path))

    track = result.get("track")
    if not result.get("matches") or not track:
        print("楽曲を認識できませんでした。")
        return

    title = track.get("title", "不明")
    artist = track.get("subtitle", "不明")
    print(f"曲名: {title}")
    print(f"アーティスト: {artist}")

    track_id = track.get("key")
    if not track_id:
        print("\nトラックIDを取得できないため、歌詞を検索できませんでした。")
        return

    details = await shazam.track_about(track_id=int(track_id))
    lyrics = extract_lyrics(details)

    if lyrics:
        print("\n--- 歌詞 ---")
        print(lyrics)
    else:
        print("\nこの楽曲の歌詞はShazamに登録されていません。")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="音声ファイルをShazamで認識して歌詞を表示します。"
    )
    parser.add_argument(
        "audio",
        nargs="?",
        type=Path,
        default=Path("Assets/dinner.mp3"),
        help="認識する音声ファイル（既定値: Assets/dinner.mp3）",
    )
    args = parser.parse_args()

    if not args.audio.is_file():
        parser.error(f"音声ファイルが見つかりません: {args.audio}")

    try:
        await recognize_and_display_lyrics(args.audio)
    except Exception as error:
        print(f"Shazamへの問い合わせに失敗しました: {error}")


if __name__ == "__main__":
    asyncio.run(main())
