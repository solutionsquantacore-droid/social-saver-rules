import json
import time
import subprocess
import os

CONFIG = [
    {
        "platform": "instagram",
        "urls": [
            "https://www.instagram.com/reels/",
        ],
        "limit": 10
    },
    {
        "platform": "tiktok",
        "urls": [
            "https://www.tiktok.com/@tiktok",
        ],
        "limit": 10
    }
]

def format_count(count):
    if not count:
        return "10K+"
    try:
        count = int(count)
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        if count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)
    except Exception:
        return "10K+"

def extract_reels():
    reels = []

    for entry in CONFIG:
        platform = entry["platform"]
        for target_url in entry["urls"]:
            print(f"Fetching from {platform}: {target_url}")
            try:
                cmd = [
                    "yt-dlp",
                    "--dump-json",
                    "--flat-playlist",
                    "--playlist-end", str(entry["limit"]),
                    target_url
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode != 0:
                    print(f"Notice: Flat playlist: {proc.stderr[:160]}")
                    continue

                for line in proc.stdout.strip().split("\n"):
                    if not line:
                        continue
                    try:
                        basic_data = json.loads(line)
                    except Exception:
                        continue

                    video_url = basic_data.get("url") or basic_data.get("webpage_url")
                    if not video_url:
                        continue

                    detail_cmd = ["yt-dlp", "-j", video_url]
                    detail_proc = subprocess.run(detail_cmd, capture_output=True, text=True)
                    if detail_proc.returncode != 0:
                        continue

                    data = json.loads(detail_proc.stdout)
                    stream_url = data.get("url")
                    if not stream_url:
                        formats = data.get("formats", [])
                        mp4_formats = [f for f in formats if f.get("ext") == "mp4" and f.get("url")]
                        if mp4_formats:
                            stream_url = mp4_formats[-1]["url"]

                    if not stream_url:
                        continue

                    reel = {
                        "id": f"{platform}_{data.get('id', str(int(time.time())))}",
                        "platform": platform,
                        "title": (data.get("title") or data.get("description") or "Trending Reel")[:120],
                        "author_name": data.get("uploader") or data.get("channel") or "Creator",
                        "author_avatar": data.get("uploader_avatar") or None,
                        "thumbnail_url": data.get("thumbnail") or "",
                        "video_url": stream_url,
                        "original_url": data.get("webpage_url") or video_url,
                        "views_count": format_count(data.get("view_count")),
                        "likes_count": format_count(data.get("like_count")),
                        "duration_seconds": int(data.get("duration") or 15)
                    }
                    reels.append(reel)

            except Exception as e:
                print(f"Error processing {target_url}: {e}")

    # Fallback to existing reels if dynamic extraction returned empty
    if not reels and os.path.exists("trending_reels.json"):
        print("Scraper produced 0 reels, preserving existing file.")
        return

    output = {
        "version": 1,
        "last_updated": int(time.time() * 1000),
        "reels": reels
    }

    with open("trending_reels.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Successfully updated trending_reels.json with {len(reels)} reels.")

if __name__ == "__main__":
    extract_reels()
