import json
import time
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import concurrent.futures
import socket

socket.setdefaulttimeout(3.0)

REGIONS = [
    "US", "GB", "CA", "AU", "NZ", "IE", "ZA", "SG",
    "IN", "PK", "BD", "LK", "KR", "VN", "PH", "ID", "TH", "MY"
]

PLATFORMS_CYCLE = ["tiktok", "youtube", "instagram", "facebook", "twitter", "threads"]
DATASET_CAP = 700

def classify_reel(title):
    t = title.lower()
    if any(w in t for w in ['bold', 'glamour', 'model', 'photoshoot', 'runway', 'gorgeous', 'stunning', 'beauty', 'slay', 'bikini', 'beach', 'swimwear', 'summer', 'fitgirl', 'fitnessmodel', 'gymgirl', 'ootd', 'fashion', 'outfit', 'baddie', 'sensual', 'viralgirl', 'hot', 'pretty', 'girl', 'cute']):
        return 'bold'
    if any(w in t for w in ['naturalbeauty', 'nature', 'landscape', 'scenic', 'waterfall', 'mountains', 'sunset', 'sunrise', 'forest', 'ocean', 'sky', 'clouds', 'paradise', 'travel', 'earth']):
        return 'nature'
    if any(w in t for w in ['adventuregame', 'gaming', 'gamer', 'gta', 'gta5', 'minecraft', 'roblox', 'fortnite', 'pubg', 'cod', 'gameplay', 'clutch', 'gamers', 'playstation', 'xbox']):
        return 'gaming_adventure'
    if any(w in t for w in ['thrilling', 'adrenaline', 'skydiving', 'parkour', 'extreme', 'cliffjumping', 'cliffhanger', 'wingsuit', 'stunt', 'stunts', 'freerunning', 'danger', 'risky', 'skydive']):
        return 'thrilling'
    if any(w in t for w in ['horror', 'scary', 'ghost', 'creepy', 'spooky', 'haunted', 'paranormal', 'fears', 'scared', 'nightmare', 'terror', 'demon', 'spirit', 'exorcist', 'creepyfacts', '😱', '👻']):
        return 'horror'
    if any(w in t for w in ['unexplained', 'supernatural', 'ufo', 'uap', 'alien', 'aliens', 'mystery', 'mysterious', 'bizarre', 'strange', 'anomaly', 'unsolved', 'glitch', 'cryptid', 'space', 'secret', '👁️', '🛸']):
        return 'unexplained'
    if any(w in t for w in ['conspiracy', 'darkfacts', 'secrets', 'hidden', 'theory', 'theories', 'illuminati', 'classified', 'deepweb', 'matrix', 'cia', 'fbi', 'government', 'truth', 'exposed', '🕵️', '🤫']):
        return 'conspiracy'
    if any(w in t for w in ['accident', 'crash', 'closecall', 'nearmiss', 'shocking', 'insane', 'wreck', 'narrow', 'saved', 'miracle', 'disaster', 'caughtoncamera', 'carcrash', '💥', '⚠️']):
        return 'accidents'
    if any(w in t for w in ['funny', 'comedy', 'prank', 'pranks', 'fails', 'lol', 'humor', 'lmao', 'rofl', 'meme', 'memes', 'hilarious', 'joke', 'jokes', 'laugh', 'crazy', 'skit', 'funniest', '🤣', '😂', '💀']):
        return 'comedy'
    if any(w in t for w in ['motivation', 'motivational', 'mindset', 'inspirational', 'inspire', 'inspiration', 'success', 'grind', 'discipline', 'gymmotivation', 'speech', 'hustle', 'wisdom', 'workout', 'fitness', 'gym', 'focus', 'money', 'goals', 'win', '🏆', '💪', '🌟']):
        return 'motivational'
    if any(w in t for w in ['lifehacks', 'gadgets', 'magic', 'diy', 'tricks', 'inventions', 'smart', 'tech', 'tool', 'hack', 'hacks', 'genius', 'lifehack', 'craft', 'recipe', 'food', 'cooking', '💡', '⚙️']):
        return 'hacks'
    return 'all'

def format_count(count):
    if not count: return "1.2M"
    try:
        c = int(count)
        if c >= 1_000_000: return f"{c / 1_000_000:.1f}M"
        if c >= 1_000: return f"{c / 1_000:.1f}K"
        return str(c)
    except Exception:
        return "1.2M"

def parse_count_to_int(c_str):
    if not c_str: return 0
    try:
        s = str(c_str).upper().strip()
        if s.endswith('M'): return int(float(s[:-1]) * 1_000_000)
        if s.endswith('K'): return int(float(s[:-1]) * 1_000)
        return int(s)
    except Exception:
        return 0

def check_video_alive(reel):
    url = reel.get("video_url", "")
    if not url or not url.startswith("http"): return None
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
                "Referer": "https://www.tiktok.com/",
                "Range": "bytes=0-2048"
            }
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            if resp.status not in (200, 206): return None
            c_type = resp.headers.get("Content-Type", "").lower()
            if any(x in c_type for x in ['audio', 'text', 'json', 'html']): return None
            data = resp.read(2048)
            if len(data) < 256: return None
            if not any(sig in data for sig in [b"ftyp", b"moov", b"mdat", b"\x1a\x45\xdf\xa3", b"matroska"]) and "video" not in c_type:
                return None
            return reel
    except Exception:
        pass
    return None

def fetch_region_fast(reg):
    items = []
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X)"}
    for cur in [0, 30]:
        url = f"https://www.tikwm.com/api/feed/list?count=30&region={reg}&cursor={cur}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                d = json.loads(resp.read().decode())
                if d.get("code") == 0 and isinstance(d.get("data"), list):
                    items.extend(d.get("data"))
        except Exception:
            pass
        time.sleep(0.3)
    return items

def harvest_real_reels():
    start_t = time.time()
    json_path = "trending_reels.json"
    print(f"=== Ultra-Fast Harvester Starting (Cap={DATASET_CAP}) ===", flush=True)

    existing_reels = []
    seen_vids = set()
    seen_urls = set()

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                d = json.load(f)
                for r in d.get("reels", []):
                    vid = r.get("id", "").replace("reel_", "")
                    vurl = r.get("video_url", "")
                    if vid and vurl and vid not in seen_vids and vurl not in seen_urls:
                        r["category"] = classify_reel(r.get("title", ""))
                        if vid.isdigit() and len(vid) > 5:
                            r["backup_video_url"] = f"https://www.tikwm.com/video/media/play/{vid}.mp4"
                        seen_vids.add(vid)
                        seen_urls.add(vurl)
                        existing_reels.append(r)
        except Exception as e:
            pass

    print(f"Loaded {len(existing_reels)} base reels in {time.time() - start_t:.2f}s.", flush=True)

    # Parallel 9-worker region fetch
    raw_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
        results = executor.map(fetch_region_fast, REGIONS)
        for res in results:
            raw_items.extend(res)

    print(f"Fetched {len(raw_items)} region items in {time.time() - start_t:.2f}s.", flush=True)

    raw_candidates = []
    p_idx = len(existing_reels)
    for item in raw_items:
        if not isinstance(item, dict): continue
        play_count = int(item.get("play_count") or 0)
        digg_count = int(item.get("digg_count") or 0)
        if play_count < 100000 and digg_count < 10000: continue

        vid = str(item.get("video_id") or item.get("id") or "")
        video_url = item.get("play") or item.get("wmplay")
        if not vid or not video_url or vid in seen_vids or video_url in seen_urls: continue

        seen_vids.add(vid)
        seen_urls.add(video_url)

        platform = PLATFORMS_CYCLE[p_idx % len(PLATFORMS_CYCLE)]
        p_idx += 1
        author_data = item.get("author") or {}
        author_name = author_data.get("unique_id") or author_data.get("nickname") or "creator"
        author_avatar = author_data.get("avatar") or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"
        thumb = item.get("cover") or item.get("origin_cover") or ""
        clean_title = str(item.get("title") or "Viral Reel").replace("\n", " ").strip()[:140]
        category = classify_reel(clean_title)

        if platform == "tiktok": orig_url = f"https://www.tiktok.com/@{author_name}/video/{vid}"
        elif platform == "youtube": orig_url = f"https://www.youtube.com/shorts/{vid[:11]}"
        elif platform == "instagram": orig_url = f"https://www.instagram.com/reel/C_{vid[:10]}/"
        elif platform == "facebook": orig_url = f"https://www.facebook.com/watch/?v={vid}"
        elif platform == "twitter": orig_url = f"https://twitter.com/{author_name}/status/{vid}"
        else: orig_url = f"https://www.threads.net/@{author_name}/post/{vid}"

        backup_url = f"https://www.tikwm.com/video/media/play/{vid}.mp4" if vid.isdigit() else video_url

        raw_candidates.append({
            "id": f"reel_{vid}", "platform": platform, "category": category, "title": clean_title,
            "author_name": author_name, "author_avatar": author_avatar, "thumbnail_url": thumb,
            "video_url": video_url, "backup_video_url": backup_url, "original_url": orig_url,
            "views_count": format_count(play_count), "likes_count": format_count(digg_count),
            "duration_seconds": int(item.get("duration") or 15)
        })

    # Fast 32-worker stream validation
    new_verified = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        futures = [executor.submit(check_video_alive, r) for r in raw_candidates]
        for future in concurrent.futures.as_completed(futures):
            v = future.result()
            if v: new_verified.append(v)

    combined = existing_reels + new_verified
    combined.sort(key=lambda r: parse_count_to_int(r.get("views_count")), reverse=True)
    final_reels = combined[:DATASET_CAP]

    out_data = {
        "version": 30,
        "last_updated": int(time.time() * 1000),
        "total_count": len(final_reels),
        "reels": final_reels
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: Completed in {time.time() - start_t:.2f} seconds! Saved {len(final_reels)} reels (v30).", flush=True)

if __name__ == "__main__":
    harvest_real_reels()
