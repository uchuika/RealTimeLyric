import asyncio
from shazamio import Shazam


async def main():
    shazam = Shazam()
    result = await shazam.recognize("Assets/melty.mp3")

    if result.get("matches") and "track" in result:
        track = result["track"]
        print(f"曲名: {track.get('title', '不明')}")
        print(f"アーティスト: {track.get('subtitle', '不明')}")
        print(f"Shazam URL: {track.get('share', {}).get('href', 'なし')}")
    else:
        print("曲を特定できませんでした")


if __name__ == "__main__":
    asyncio.run(main())
