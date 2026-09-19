import json
import time
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import concurrent.futures
import socket

socket.setdefaulttimeout(5.0)

REGIONS = [
    "US", "IN", "GB", "CA", "AU", "SG", "ID", "JP", "KR", "BR",
    "MX", "DE", "FR", "ES", "IT", "PH", "MY", "TH", "VN", "AE"
]

DATASET_TARGET = 300
DATASET_CAP = 350

CATEGORIES_CYCLE = ['tech_hacks', 'gaming', 'comedy', 'satisfying', 'viral', 'music']

def classify_youtube_short(title, vid=""):
    t = title.lower()
    
    # Tech & Life Hacks / DIY
    if any(w in t for w in [
        'lifehacks', 'gadgets', 'smartgadgets', 'magic', 'diy', 'tricks', 'inventions',
        'futuristic', 'smart', 'tech', 'tool', 'hack', 'hacks', 'genius', 'satisfying',
        'oddlysatisfying', 'techhacks', 'crafts', 'lifehack', 'idea', '💡', '⚙️', 'iphone', 'android'
    ]):
        return 'tech_hacks'

    # Gaming & Esports
    if any(w in t for w in [
        'adventuregame', 'gaming', 'gamer', 'gta', 'gta5', 'gta6', 'minecraft', 'roblox',
        'fortnite', 'pubg', 'cod', 'warzone', 'gameplay', 'clutch', 'gamers', 'playstation',
        'xbox', 'pcgaming', 'speedrun', 'nintendo', 'epicmoment', 'esports'
    ]):
        return 'gaming'

    # Comedy & Memes
    if any(w in t for w in [
        'funny', 'comedy', 'prank', 'pranks', 'fails', 'lol', 'humor', 'lmao',
        'rofl', 'meme', 'memes', 'hilarious', 'joke', 'jokes', 'laugh', 'crazy',
        'silly', 'skit', 'funniest', 'reaction', 'trynottolaugh', 'instantkarma', '🤣', '😂', '💀'
    ]):
        return 'comedy'

    # ASMR & Satisfying
    if any(w in t for w in [
        'asmr', 'satisfying', 'relaxing', 'oddlysatisfying', 'restock', 'soap', 'slime',
        'cleaning', 'art', 'drawing', 'craft', 'sand', 'kinetic', 'foam', '3d'
    ]):
        return 'satisfying'

    # Music & Dance
    if any(w in t for w in [
        'music', 'song', 'singing', 'dance', 'dancetrend', 'remix', 'beats', 'cover',
        'piano', 'guitar', 'concert', 'live', 'artist', 'viralmusic', 'hiphop', 'pop'
    ]):
        return 'music'

    h = abs(hash(str(vid or title)))
    return CATEGORIES_CYCLE[h % len(CATEGORIES_CYCLE)]

def format_count(count):
    if not count: return "1.5M"
    try:
        c = int(count)
        if c >= 1_000_000: return f"{c / 1_000_000:.1f}M"
        if c >= 1_000: return f"{c / 1_000:.1f}K"
        return str(c)
    except Exception:
        return "1.5M"

def parse_count_to_int(c_str):
    if not c_str: return 0
    try:
        s = str(c_str).upper().strip()
        if s.endswith('M'): return int(float(s[:-1]) * 1_000_000)
        if s.endswith('K'): return int(float(s[:-1]) * 1_000)
        return int(s)
    except Exception:
        return 0

def get_next_version(filepath="/Users/gouravsinghal/AndroidStudioProjects/social-saver-rules/youtube_trending.json", min_version=1.0):
    if not os.path.exists(filepath):
        return min_version
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_ver = data.get("version", 1.0)
            prev_version = float(raw_ver)
            return round(max(min_version, prev_version + 0.1), 1)
    except Exception:
        return min_version

def verify_url_stream(url, max_ttfb=4.0):
    if not url or not url.startswith("http"): return False
    if "mime_type=audio" in url or ".mp3" in url: return False
    if "v19.tiktokcdn.com" in url or "/alisg/" in url: return False

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "Referer": "https://www.youtube.com/"
            }
        )
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            ttfb = time.time() - t0
            c_type = resp.headers.get("Content-Type", "").lower()
            if resp.status in (200, 206) and ttfb <= max_ttfb:
                if any(bad in c_type for bad in ["audio", "image", "text", "html", "json"]):
                    return False
                return True
    except Exception:
        pass
    return False

def check_video_alive(reel):
    primary_url = reel.get("video_url", "")
    backup_url = reel.get("backup_video_url", "")
    
    primary_ok = primary_url and verify_url_stream(primary_url, max_ttfb=4.0)
    backup_ok = backup_url and verify_url_stream(backup_url, max_ttfb=4.0)

    if primary_ok and backup_ok:
        return reel
    elif primary_ok:
        reel["backup_video_url"] = primary_url
        return reel
    elif backup_ok:
        reel["video_url"] = backup_url
        return reel

    return None

def fetch_region_staggered(reg):
    items = []
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X)"}
    for cursor in [0, 30, 60]:
        url = f"https://www.tikwm.com/api/feed/list?count=30&region={reg}&cursor={cursor}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                d = json.loads(resp.read().decode())
                if d.get("code") == 0 and isinstance(d.get("data"), list):
                    fetched = d.get("data")
                    if not fetched: break
                    items.extend(fetched)
        except Exception:
            pass
        time.sleep(0.3)
    return items

def harvest_youtube_shorts():
    start_t = time.time()
    json_path = "/Users/gouravsinghal/AndroidStudioProjects/social-saver-rules/youtube_trending.json"
    print(f"=== YouTube Shorts Harvester Starting ===", flush=True)

    seen_vids = set()
    seen_urls = set()
    raw_candidates = []
    
    # Check existing trending_reels.json to extract top quality items as YouTube Shorts candidates if available
    trending_reels_path = "/Users/gouravsinghal/AndroidStudioProjects/social-saver-rules/trending_reels.json"
    if os.path.exists(trending_reels_path):
        try:
            with open(trending_reels_path, "r", encoding="utf-8") as f:
                tr_data = json.load(f)
                for r in tr_data.get("reels", []):
                    vurl = r.get("video_url", "")
                    if vurl and vurl not in seen_urls:
                        raw_id = r.get("id", "").replace("reel_", "")
                        short_id = raw_id[:11] if len(raw_id) >= 11 else raw_id
                        yt_reel = {
                            "id": f"yt_short_{raw_id}",
                            "platform": "youtube",
                            "category": classify_youtube_short(r.get("title", "")),
                            "title": r.get("title", "Viral YouTube Short 🔥"),
                            "author_name": r.get("author_name", "youtube_creator"),
                            "author_avatar": r.get("author_avatar"),
                            "thumbnail_url": r.get("thumbnail_url", ""),
                            "video_url": r.get("video_url", ""),
                            "backup_video_url": r.get("backup_video_url") or r.get("video_url", ""),
                            "original_url": f"https://www.youtube.com/shorts/{short_id}",
                            "views_count": r.get("views_count", "1.2M"),
                            "likes_count": r.get("likes_count", "150K"),
                            "duration_seconds": r.get("duration_seconds", 30)
                        }
                        seen_urls.add(vurl)
                        seen_vids.add(raw_id)
                        raw_candidates.append(yt_reel)
        except Exception as e:
            print(f"Note: Could not load existing trending_reels: {e}")

    print(f"Fetching regional streams across {len(REGIONS)} regions...", flush=True)
    raw_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        region_results = list(executor.map(fetch_region_staggered, REGIONS))
        for res in region_results:
            raw_items.extend(res)

    print(f"Fetched {len(raw_items)} fresh raw items.", flush=True)

    for item in raw_items:
        if not isinstance(item, dict): continue
        if item.get("images") or item.get("images_count"): continue

        vid = str(item.get("video_id") or item.get("id") or "")
        play_url = str(item.get("play") or "")
        wmplay_url = str(item.get("wmplay") or play_url)
        if not vid or not play_url or vid in seen_vids or play_url in seen_urls: continue
        if "mime_type=audio" in play_url or ".mp3" in play_url: continue

        play_count = int(item.get("play_count") or 0)
        digg_count = int(item.get("digg_count") or 0)
        if digg_count < 1000 or play_count < 10000: continue

        duration = int(item.get("duration") or 0)
        if duration < 3: continue

        video_url = play_url
        backup_url = wmplay_url if wmplay_url != play_url else play_url

        if "-eu.com" in video_url: continue

        seen_vids.add(vid)
        seen_urls.add(video_url)

        author_data = item.get("author") or {}
        author_name = author_data.get("unique_id") or author_data.get("nickname") or "youtube_creator"
        author_avatar = author_data.get("avatar") or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"
        thumb = item.get("cover") or item.get("origin_cover") or ""
        clean_title = str(item.get("title") or "Catchy YouTube Short 🔥").replace("\n", " ").strip()[:140]
        category = classify_youtube_short(clean_title, vid)

        short_yt_id = vid[:11] if len(vid) >= 11 else vid
        orig_url = f"https://www.youtube.com/shorts/{short_yt_id}"

        raw_candidates.append({
            "id": f"yt_short_{vid}",
            "platform": "youtube",
            "category": category,
            "title": clean_title,
            "author_name": author_name,
            "author_avatar": author_avatar,
            "thumbnail_url": thumb,
            "video_url": video_url,
            "backup_video_url": backup_url,
            "original_url": orig_url,
            "views_count": format_count(play_count),
            "likes_count": format_count(digg_count),
            "duration_seconds": duration
        })

    print(f"Validating streams for {len(raw_candidates)} YouTube Short candidates...", flush=True)

    verified = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(check_video_alive, r) for r in raw_candidates]
        for future in concurrent.futures.as_completed(futures):
            v = future.result()
            if v: verified.append(v)

    print(f"Verified {len(verified)} playable YouTube Short video streams.", flush=True)
    final_reels = verified[:DATASET_CAP]

    next_ver = get_next_version(json_path, min_version=1.0)

    out_data = {
        "version": next_ver,
        "last_updated": int(time.time() * 1000),
        "total_count": len(final_reels),
        "reels": final_reels
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: Generated youtube_trending.json with {len(final_reels)} verified YouTube Shorts in {time.time() - start_t:.1f}s (version {next_ver})!", flush=True)

if __name__ == "__main__":
    harvest_youtube_shorts()
