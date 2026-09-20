import json
import time
import os

LIGHTWEIGHT_YOUTUBE_SHORTS = [
    {
        "id": "L_LUpnjgPso",
        "title": "Mind-Blowing Floating Water Trick! 💡 #Shorts #Tech",
        "author_name": "tech_experiments",
        "author_avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "thumbnail_url": "https://img.youtube.com/vi/L_LUpnjgPso/hqdefault.jpg",
        "category": "tech_hacks",
        "likes_count": "1.3M"
    },
    {
        "id": "5qap5aO4i9A",
        "title": "Oddly Satisfying Kinetic Sand ASMR 🎨✨ #Shorts #Satisfying",
        "author_name": "asmr_relax",
        "author_avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
        "thumbnail_url": "https://img.youtube.com/vi/5qap5aO4i9A/hqdefault.jpg",
        "category": "satisfying",
        "likes_count": "950K"
    },
    {
        "id": "k9rVlIqT6-k",
        "title": "Unbelievable Life Hack You Need to Try! ⚙️ #Shorts #Hacks",
        "author_name": "smart_hacks",
        "author_avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
        "thumbnail_url": "https://img.youtube.com/vi/k9rVlIqT6-k/hqdefault.jpg",
        "category": "tech_hacks",
        "likes_count": "1.8M"
    },
    {
        "id": "_8xR5Z_4E8o",
        "title": "Hilarious Cat vs Flying Laser 🐱😂 #Shorts #Comedy",
        "author_name": "funny_pets",
        "author_avatar": "https://images.unsplash.com/photo-1574158622682-e40e69881006?w=150",
        "thumbnail_url": "https://img.youtube.com/vi/_8xR5Z_4E8o/hqdefault.jpg",
        "category": "comedy",
        "likes_count": "2.4M"
    },
    {
        "id": "tVlcKp3bWH8",
        "title": "Epic 1v4 Gaming Clutch! 🎮🔥 #Shorts #Gaming",
        "author_name": "gaming_highlights",
        "author_avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
        "thumbnail_url": "https://img.youtube.com/vi/tVlcKp3bWH8/hqdefault.jpg",
        "category": "gaming",
        "likes_count": "720K"
    },
    {
        "id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up #Shorts #Viral",
        "author_name": "RickAstley",
        "author_avatar": "https://img.youtube.com/vi/dQw4w9WgXcQ/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        "category": "viral",
        "likes_count": "16M"
    },
    {
        "id": "kJQP7kiw5Fk",
        "title": "Luis Fonsi - Despacito ft. Daddy Yankee #Shorts #Music",
        "author_name": "LuisFonsiVEVO",
        "author_avatar": "https://img.youtube.com/vi/kJQP7kiw5Fk/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/kJQP7kiw5Fk/hqdefault.jpg",
        "category": "music",
        "likes_count": "52M"
    }
]

def generate():
    json_path = "/Users/gouravsinghal/AndroidStudioProjects/social-saver-rules/youtube_trending.json"
    data = {
        "version": 2.0,
        "last_updated": int(time.time() * 1000),
        "reels": LIGHTWEIGHT_YOUTUBE_SHORTS
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"SUCCESS: Generated lightweight youtube_trending.json with {len(LIGHTWEIGHT_YOUTUBE_SHORTS)} entries (version 2.0).")

if __name__ == "__main__":
    generate()
