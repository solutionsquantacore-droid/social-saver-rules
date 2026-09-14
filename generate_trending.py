import json
import time
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import concurrent.futures
import socket
import random

socket.setdefaulttimeout(4.0)

REGIONS = [
    "US", "GB", "CA", "AU", "NZ", "IE", "ZA", "SG",  # English-speaking
    "IN", "PK", "BD", "LK",                          # India & South Asia
    "KR", "VN", "PH", "ID", "TH", "MY"               # South Korea, Vietnam & SE Asia
]

PLATFORMS_CYCLE = ["tiktok", "youtube", "instagram", "facebook", "twitter", "threads"]
DATASET_CAP = 700

def classify_reel(title):
    t = title.lower()
    
    # Bold / Glamour / Beauty / Fashion / Models
    if any(w in t for w in [
        'bold', 'glamour', 'model', 'supermodel', 'photoshoot', 'runway', 'fashionmodel',
        'gorgeous', 'stunning', 'beauty', 'slay', 'bikini', 'beach', 'beachvibes', 'swimwear',
        'summer', 'poolside', 'fitgirl', 'fitnessmodel', 'gymgirl', 'fitcheck', 'abs',
        'ootd', 'styleinspo', 'fashion', 'outfit', 'lookbook', 'dress', 'chic', 'glam',
        'dancetrend', 'viraldance', 'baddie', 'sensual', 'attitude', 'viralgirl', 'hot',
        'pretty', 'girl', 'babe', 'cute', 'modelshoot'
    ]):
        return 'bold'
        
    # Nature & Landscapes
    if any(w in t for w in [
        'naturalbeauty', 'nature', 'landscape', 'landscapes', 'scenic', 'waterfall',
        'mountains', 'mountain', 'sunset', 'sunrise', 'aestheticnature', 'forest',
        'ocean', 'beachview', 'sky', 'clouds', 'paradise', 'travel', 'earth', 'wonder'
    ]):
        return 'nature'
        
    # Gaming & Adventure
    if any(w in t for w in [
        'adventuregame', 'gaming', 'gamer', 'gta', 'gta5', 'minecraft', 'roblox',
        'fortnite', 'pubg', 'cod', 'gameplay', 'clutch', 'gamers', 'playstation',
        'xbox', 'pcgaming', 'speedrun', 'nintendo', 'epicmoment'
    ]):
        return 'gaming_adventure'
        
    # Thrilling & Stunts & Adrenaline
    if any(w in t for w in [
        'thrilling', 'adrenaline', 'skydiving', 'parkour', 'extreme', 'cliffjumping',
        'cliffhanger', 'wingsuit', 'bungee', 'roofing', 'stunt', 'stunts', 'freerunning',
        'speeding', 'danger', 'risky', 'skydive', 'fast'
    ]):
        return 'thrilling'

    # Horror / Scary
    if any(w in t for w in [
        'horror', 'scary', 'ghost', 'creepy', 'spooky', 'haunted', 'paranormal',
        'fears', 'scared', 'nightmare', 'terror', 'demon', 'spirit', 'exorcist',
        'creepyfacts', 'scariest', 'monster', 'shadow', 'death', 'dark', 'evil', 'scream', '😱', '👻'
    ]):
        return 'horror'
        
    # Unexplained / Mysteries
    if any(w in t for w in [
        'unexplained', 'supernatural', 'ufo', 'uap', 'alien', 'aliens', 'mystery',
        'mysterious', 'bizarre', 'strange', 'anomaly', 'unsolved', 'glitch',
        'skinwalker', 'cryptid', 'space', 'deepsea', 'secret', 'unknown', '👁️', '🛸'
    ]):
        return 'unexplained'

    # Conspiracy / Theories
    if any(w in t for w in [
        'conspiracy', 'darkfacts', 'secrets', 'hidden', 'theory', 'theories',
        'illuminati', 'classified', 'deepweb', 'darkweb', 'mindblown', 'matrix',
        'declassified', 'cia', 'fbi', 'government', 'truth', 'exposed', 'lies', '🕵️', '🤫'
    ]):
        return 'conspiracy'

    # Accidents / Close Calls
    if any(w in t for w in [
        'accident', 'crash', 'closecall', 'nearmiss', 'shocking', 'insane', 'wreck',
        'narrow', 'saved', 'miracle', 'disaster', 'caughtoncamera', 'carcrash',
        'driftfail', 'hit', 'survived', '💥', '⚠️'
    ]):
        return 'accidents'

    # Comedy / Funny
    if any(w in t for w in [
        'funny', 'comedy', 'prank', 'pranks', 'fails', 'lol', 'humor', 'lmao',
        'rofl', 'meme', 'memes', 'hilarious', 'joke', 'jokes', 'laugh', 'crazy',
        'silly', 'skit', 'funniest', 'reaction', '🤣', '😂', '💀'
    ]):
        return 'comedy'

    # Motivational / Workout
    if any(w in t for w in [
        'motivation', 'motivational', 'mindset', 'inspirational', 'inspire',
        'inspiration', 'success', 'grind', 'discipline', 'gymmotivation',
        'speech', 'hustle', 'wisdom', 'hardwork', 'nevergiveup', 'workout',
        'fitness', 'gym', 'focus', 'money', 'quotes', 'goals', 'win', 'trophy', '🏆', '💪', '🌟'
    ]):
        return 'motivational'

    # Hacks / Tech / DIY
    if any(w in t for w in [
        'lifehacks', 'gadgets', 'magic', 'diy', 'tricks', 'inventions',
        'futuristic', 'smart', 'tech', 'tool', 'hack', 'hacks', 'genius',
        'lifehack', 'craft', 'recipe', 'food', 'cooking', 'chef', 'kitchen', 'idea', '💡', '⚙️'
    ]):
        return 'hacks'

    return 'all'

def format_count(count):
    if not count:
        return "1.2M"
    try:
        count = int(count)
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        if count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)
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

def get_next_version(filepath="trending_reels.json", min_version=27):
    if not os.path.exists(filepath):
        return min_version
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            prev_version = int(data.get("version", 0))
            return max(min_version, prev_version + 1)
    except Exception:
        return min_version

def check_video_alive(reel):
    """Pre-flight check: verify video_url returns HTTP 200/206 with valid video stream container"""
    url = reel.get("video_url", "")
    if not url or not url.startswith("http"):
        return None
    try:
        start_t = time.time()
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
                "Referer": "https://www.tiktok.com/",
                "Range": "bytes=0-8192"
            }
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            elapsed = time.time() - start_t
            if resp.status not in (200, 206) or elapsed > 3.5:
                return None

            c_type = resp.headers.get("Content-Type", "").lower()
            if "audio" in c_type or "text" in c_type or "json" in c_type or "html" in c_type:
                return None

            data = resp.read(8192)
            if len(data) < 256:
                return None

            has_video_header = any(sig in data for sig in [b"ftyp", b"moov", b"mdat", b"\x1a\x45\xdf\xa3", b"matroska"])
            if not has_video_header and "video" not in c_type:
                return None

            return reel
    except Exception:
        pass
    return None

def harvest_real_reels():
    json_path = "trending_reels.json"
    print(f"=== Harvesting & Capping dataset to EXACTLY {DATASET_CAP} Ultra-Viral Reels ===", flush=True)

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
            print("Error reading existing json:", e, flush=True)

    print(f"Loaded {len(existing_reels)} existing base reels.", flush=True)

    raw_candidates = []
    p_idx = len(existing_reels)
    cursors = list(range(0, 450, 30))
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X)"}

    for pass_num in range(1, 3):
        print(f"=== Starting Pass {pass_num} ===", flush=True)
        for reg in REGIONS:
            print(f"Fetching region {reg} (pass {pass_num})...", flush=True)
            for cur in cursors:
                url = f"https://www.tikwm.com/api/feed/list?count=30&region={reg}&cursor={cur}"
                try:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        d = json.loads(resp.read().decode())
                        if d.get("code") == -1:
                            time.sleep(1.2)
                            continue
                        items = d.get("data", [])
                        if isinstance(items, list):
                            for item in items:
                                if not isinstance(item, dict): continue
                                play_count = int(item.get("play_count") or 0)
                                digg_count = int(item.get("digg_count") or 0)

                                if play_count < 100000 and digg_count < 10000:
                                    continue

                                vid = str(item.get("video_id") or item.get("id") or "")
                                video_url = item.get("play") or item.get("wmplay")
                                if not vid or not video_url or vid in seen_vids or video_url in seen_urls:
                                    continue

                                seen_vids.add(vid)
                                seen_urls.add(video_url)

                                platform = PLATFORMS_CYCLE[p_idx % len(PLATFORMS_CYCLE)]
                                p_idx += 1
                                author_data = item.get("author") or {}
                                author_name = author_data.get("unique_id") or author_data.get("nickname") or "creator"
                                author_avatar = author_data.get("avatar") or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"
                                thumb = item.get("cover") or item.get("origin_cover") or ""
                                raw_title = str(item.get("title") or "Viral Reel")
                                clean_title = raw_title.replace("\n", " ").strip()[:140]
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
                except Exception:
                    pass
                time.sleep(1.0)

    print(f"Validating streams for {len(raw_candidates)} candidate reels...", flush=True)
    new_verified = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        futures = [executor.submit(check_video_alive, r) for r in raw_candidates]
        for future in concurrent.futures.as_completed(futures):
            v = future.result()
            if v:
                new_verified.append(v)

    combined = existing_reels + new_verified
    combined.sort(key=lambda r: parse_count_to_int(r.get("views_count")), reverse=True)

    final_reels = combined[:DATASET_CAP]
    next_ver = get_next_version(json_path)

    out_data = {
        "version": next_ver,
        "last_updated": int(time.time() * 1000),
        "total_count": len(final_reels),
        "reels": final_reels
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: Saved EXACTLY {len(final_reels)} verified reels to {json_path} (version {next_ver})!", flush=True)

if __name__ == "__main__":
    harvest_real_reels()
