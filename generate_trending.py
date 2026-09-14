import json
import time
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import concurrent.futures
import socket

socket.setdefaulttimeout(3.5)

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

def get_next_version(filepath="trending_reels.json", min_version=34):
    if not os.path.exists(filepath):
        return min_version
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            prev_version = int(data.get("version", 0))
            return max(min_version, prev_version + 1)
    except Exception:
        return min_version

def verify_url_stream(url):
    if not url or not url.startswith("http"): return False
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
                "Referer": "https://www.tiktok.com/"
            }
        )
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status in (200, 206):
                c_type = resp.headers.get("Content-Type", "").lower()
                if "video" in c_type or "octet-stream" in c_type or resp.headers.get("Content-Length"):
                    return True
    except Exception:
        pass
    return False

def check_video_alive(reel):
    primary_url = reel.get("video_url", "")
    backup_url = reel.get("backup_video_url", "")
    
    # 1. Test primary URL
    if primary_url and verify_url_stream(primary_url):
        return reel
        
    # 2. Test backup URL
    if backup_url and verify_url_stream(backup_url):
        reel["video_url"] = backup_url
        return reel
        
    # 3. Test constructed TikWM media URL
    vid_raw = reel.get("id", "").replace("reel_", "")
    if vid_raw.isdigit():
        tikwm_url = f"https://www.tikwm.com/video/media/play/{vid_raw}.mp4"
        if verify_url_stream(tikwm_url):
            reel["video_url"] = tikwm_url
            reel["backup_video_url"] = tikwm_url
            return reel
            
    return None

def fetch_region_staggered(idx_reg):
    idx, reg = idx_reg
    time.sleep(idx * 0.35) # Stagger worker start to prevent rate limits
    items = []
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X)"}
    cursors = [0, 30, 60, 90, 120, 150, 180, 210]
    for cur in cursors:
        url = f"https://www.tikwm.com/api/feed/list?count=30&region={reg}&cursor={cur}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                d = json.loads(resp.read().decode())
                if d.get("code") == 0 and isinstance(d.get("data"), list):
                    items.extend(d.get("data"))
        except Exception:
            pass
        time.sleep(0.5)
    return items

def harvest_real_reels():
    start_t = time.time()
    json_path = "trending_reels.json"
    print(f"=== Fast 700-Reel Harvester & Refresher Starting (Cap={DATASET_CAP}) ===", flush=True)

    existing_reels = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                d = json.load(f)
                existing_reels = d.get("reels", [])
        except Exception:
            pass

    seen_vids = set()
    seen_urls = set()
    raw_candidates = []
    p_idx = 0

    # 1. Add existing reels as base candidates with refreshed backup stream URLs
    for r in existing_reels:
        vid_raw = r.get("id", "").replace("reel_", "")
        if not vid_raw or vid_raw in seen_vids: continue
        seen_vids.add(vid_raw)
        
        # Ensure fresh backup URL
        if vid_raw.isdigit():
            r["backup_video_url"] = f"https://www.tikwm.com/video/media/play/{vid_raw}.mp4"
            r["video_url"] = r.get("video_url") or r["backup_video_url"]
        seen_urls.add(r.get("video_url"))
        raw_candidates.append(r)

    # 2. Parallel 6-worker region fetch for fresh harvest
    raw_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        results = executor.map(fetch_region_staggered, enumerate(REGIONS))
        for res in results:
            raw_items.extend(res)

    print(f"Fetched {len(raw_items)} fresh region items in {time.time() - start_t:.2f}s.", flush=True)

    for item in raw_items:
        if not isinstance(item, dict): continue
        play_count = int(item.get("play_count") or 0)
        digg_count = int(item.get("digg_count") or 0)
        if play_count < 20000 and digg_count < 2000: continue

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

    print(f"Validating streams for {len(raw_candidates)} total candidates...", flush=True)

    # Fast 32-worker stream validation
    verified = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        futures = [executor.submit(check_video_alive, r) for r in raw_candidates]
        for future in concurrent.futures.as_completed(futures):
            v = future.result()
            if v: verified.append(v)

    verified.sort(key=lambda r: parse_count_to_int(r.get("views_count")), reverse=True)
    final_reels = verified[:DATASET_CAP]
    next_ver = get_next_version(json_path)

    out_data = {
        "version": next_ver,
        "last_updated": int(time.time() * 1000),
        "total_count": len(final_reels),
        "reels": final_reels
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: Preserved & updated dataset to {len(final_reels)} verified reels in {time.time() - start_t:.1f}s (version {next_ver})!", flush=True)

if __name__ == "__main__":
    harvest_real_reels()
