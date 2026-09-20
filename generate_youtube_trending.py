import json
import time
import os

LIGHTWEIGHT_YOUTUBE_SHORTS = [
    {
        "id": "PuJmd5TOAGU",
        "title": "आपका प्रारब्ध नष्ट हो जाएगा ! || Shri Hit Premanand Govind Sharan Ji Maharaj || #Shorts",
        "author_name": "SadhanPath",
        "author_avatar": "https://img.youtube.com/vi/PuJmd5TOAGU/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/PuJmd5TOAGU/hqdefault.jpg",
        "category": "spiritual",
        "likes_count": "1.5M"
    },
    {
        "id": "N5e8TFTQ3kc",
        "title": "मन को शांत करने का महामंत्र || Shri Premanand Ji Maharaj #Shorts",
        "author_name": "SadhanPath",
        "author_avatar": "https://img.youtube.com/vi/N5e8TFTQ3kc/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/N5e8TFTQ3kc/hqdefault.jpg",
        "category": "spiritual",
        "likes_count": "980K"
    },
    {
        "id": "KieM0Pcxdpg",
        "title": "जीवन बदलने वाली सीख | Divine Motivation #Shorts",
        "author_name": "SadhanPath",
        "author_avatar": "https://img.youtube.com/vi/KieM0Pcxdpg/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/KieM0Pcxdpg/hqdefault.jpg",
        "category": "motivation",
        "likes_count": "2.1M"
    },
    {
        "id": "4d2L-l4Rl44",
        "title": "भगवान का नाम ही सर्वश्रेष्ठ मार्ग है #Shorts",
        "author_name": "SadhanPath",
        "author_avatar": "https://img.youtube.com/vi/4d2L-l4Rl44/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/4d2L-l4Rl44/hqdefault.jpg",
        "category": "spiritual",
        "likes_count": "1.2M"
    },
    {
        "id": "7vz6EGg7B6g",
        "title": "सच्चा सुख कहां मिलता है? || Premanand Maharaj #Shorts",
        "author_name": "SadhanPath",
        "author_avatar": "https://img.youtube.com/vi/7vz6EGg7B6g/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/7vz6EGg7B6g/hqdefault.jpg",
        "category": "spiritual",
        "likes_count": "840K"
    },
    {
        "id": "DcD8ymKvEqc",
        "title": "अपनी सोच बदलो, दुनिया बदलेगी ✨ #Shorts #Wisdom",
        "author_name": "SadhanPath",
        "author_avatar": "https://img.youtube.com/vi/DcD8ymKvEqc/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/DcD8ymKvEqc/hqdefault.jpg",
        "category": "wisdom",
        "likes_count": "1.9M"
    },
    {
        "id": "yTFfgsRZYP0",
        "title": "शांति और शक्ति का गुप्त रहस्य 🔥 #Shorts",
        "author_name": "SadhanPath",
        "author_avatar": "https://img.youtube.com/vi/yTFfgsRZYP0/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/yTFfgsRZYP0/hqdefault.jpg",
        "category": "motivation",
        "likes_count": "1.1M"
    },
    {
        "id": "NjKdUid7uZQ",
        "title": "ईश्वर पर अटूट विश्वास की शक्ति 🌸 #Shorts",
        "author_name": "SadhanPath",
        "author_avatar": "https://img.youtube.com/vi/NjKdUid7uZQ/default.jpg",
        "thumbnail_url": "https://img.youtube.com/vi/NjKdUid7uZQ/hqdefault.jpg",
        "category": "spiritual",
        "likes_count": "2.4M"
    }
]

def generate():
    json_path = "/Users/gouravsinghal/AndroidStudioProjects/social-saver-rules/youtube_trending.json"
    data = {
        "version": 3.0,
        "last_updated": int(time.time() * 1000),
        "reels": LIGHTWEIGHT_YOUTUBE_SHORTS
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"SUCCESS: Generated lightweight youtube_trending.json with {len(LIGHTWEIGHT_YOUTUBE_SHORTS)} entries (version 3.0).")

if __name__ == "__main__":
    generate()

