import argparse
import json
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


LRCLIB_API_URL = "https://lrclib.net/api/get"


def get_lrclib_lyrics(
    track_name: str,
    artist_name: Optional[str] = None,
    album_name: Optional[str] = None,
    duration: Optional[int] = None,
) -> dict:
    """Fetch lyrics from LRCLIB. Duration is seconds."""
    params = {"track_name": track_name}

    if artist_name:
        params["artist_name"] = artist_name
    if album_name:
        params["album_name"] = album_name
    if duration:
        params["duration"] = str(duration)

    url = f"{LRCLIB_API_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "RealTimeLyric/1.0"})

    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def print_lyrics(data: dict) -> None:
    print(f"Track: {data.get('trackName', 'Unknown')}")
    print(f"Artist: {data.get('artistName', 'Unknown')}")
    print(f"Album: {data.get('albumName', 'Unknown')}")
    print(f"Duration: {data.get('duration', 'Unknown')} sec")

    synced_lyrics = data.get("syncedLyrics")
    plain_lyrics = data.get("plainLyrics")

    if synced_lyrics:
        print("\n--- Synced lyrics (LRC) ---")
        print(synced_lyrics)
    elif plain_lyrics:
        print("\n--- Plain lyrics ---")
        print(plain_lyrics)
    else:
        print("\nLyrics metadata was found, but the lyrics text is empty.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch lyrics from LRCLIB API.")
    parser.add_argument("track", nargs="?",
                        default="Tell Your World", help="Track name")
    parser.add_argument(
        "-a",
        "--artist",
        default="livetune feat. Hatsune Miku",
        help="Artist name",
    )
    parser.add_argument("--album", help="Album name")
    parser.add_argument("-d", "--duration", type=int,
                        help="Duration in seconds")
    args = parser.parse_args()

    try:
        lyrics = get_lrclib_lyrics(
            track_name=args.track,
            artist_name=args.artist,
            album_name=args.album,
            duration=args.duration,
        )
    except HTTPError as error:
        if error.code == 404:
            print("Lyrics were not found in LRCLIB.")
        else:
            print(f"LRCLIB API returned HTTP {error.code}.")
        return
    except URLError as error:
        print(f"Failed to connect to LRCLIB API: {error.reason}")
        return
    except TimeoutError:
        print("LRCLIB API request timed out.")
        main()
        return

    print_lyrics(lyrics)


if __name__ == "__main__":
    main()
