import json
import time
import urllib.request
import urllib.parse
import os
import sys
import re
import random
import concurrent.futures

# Paths
RULES_REPO_DIR = "/Users/gouravsinghal/AndroidStudioProjects/social-saver-rules"
RULES_JSON_PATH = os.path.join(RULES_REPO_DIR, "youtube_trending.json")
LOCAL_ASSET_PATH = "/Users/gouravsinghal/AndroidStudioProjects/Social-All-Video-Downloader/app/src/main/assets/youtube_trending_default.json"

DATASET_TARGET = 150
DATASET_CAP = 250

SEARCH_CATEGORIES = [
    {
        "category": "viral",
        "queries": ["%23shorts+viral", "%23shorts+trending", "%23shorts+famous"]
    },
    {
        "category": "comedy",
        "queries": ["%23shorts+funny", "%23shorts+comedy", "%23shorts+prank", "%23shorts+memes"]
    },
    {
        "category": "tech_hacks",
        "queries": ["%23shorts+gadgets", "%23shorts+lifehacks", "%23shorts+smartgadgets", "%23shorts+diy"]
    },
    {
        "category": "gaming",
        "queries": ["%23shorts+gaming", "%23shorts+gta5", "%23shorts+minecraft", "%23shorts+gamer"]
    },
    {
        "category": "satisfying",
        "queries": ["%23shorts+satisfying", "%23shorts+asmr", "%23shorts+oddlysatisfying"]
    },
    {
        "category": "music",
        "queries": ["%23shorts+music", "%23shorts+dance", "%23shorts+song"]
    }
]

def format_views(view_str):
    if not view_str:
        return "1.2M"
    cleaned = view_str.replace("views", "").strip()
    return cleaned if cleaned else "1.2M"

def get_next_version(filepath=RULES_JSON_PATH, min_version=4.0):
    if not os.path.exists(filepath):
        return min_version
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            prev_version = float(data.get("version", min_version))
            return round(max(min_version, prev_version + 0.1), 1)
    except Exception:
        return min_version

def fetch_shorts_for_query(query, category):
    url = f"https://www.youtube.com/results?search_query={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    extracted = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            m = re.search(r'var ytInitialData = ({.*?});</script>', html)
            if not m:
                return extracted
            data = json.loads(m.group(1))

            def search_nodes(obj):
                if isinstance(obj, dict):
                    # 1. Modern YouTube Shorts Lockup
                    if "shortsLockupViewModel" in obj:
                        slv = obj["shortsLockupViewModel"]
                        entity_id = slv.get("entityId", "")
                        vid = entity_id.replace("shorts-shelf-item-", "").strip()
                        if len(vid) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', vid):
                            title = slv.get("overlayMetadata", {}).get("primaryText", {}).get("content", "").strip()
                            views_raw = slv.get("overlayMetadata", {}).get("secondaryText", {}).get("content", "").strip()
                            if title:
                                extracted.append({
                                    "id": vid,
                                    "title": title,
                                    "author_name": "youtube_creator",
                                    "author_avatar": f"https://img.youtube.com/vi/{vid}/default.jpg",
                                    "thumbnail_url": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
                                    "category": category,
                                    "likes_count": format_views(views_raw)
                                })
                    # 2. Classic Reel Item Renderer
                    elif "reelItemRenderer" in obj:
                        rir = obj["reelItemRenderer"]
                        vid = rir.get("videoId", "").strip()
                        if len(vid) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', vid):
                            headline = rir.get("headline", {}).get("simpleText", "")
                            views_raw = rir.get("viewCountText", {}).get("simpleText", "")
                            if headline:
                                extracted.append({
                                    "id": vid,
                                    "title": headline,
                                    "author_name": "youtube_creator",
                                    "author_avatar": f"https://img.youtube.com/vi/{vid}/default.jpg",
                                    "thumbnail_url": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
                                    "category": category,
                                    "likes_count": format_views(views_raw)
                                })
                    for v in obj.values():
                        search_nodes(v)
                elif isinstance(obj, list):
                    for item in obj:
                        search_nodes(item)

            search_nodes(data)
    except Exception as e:
        print(f"Error querying {query}: {e}", file=sys.stderr)
    return extracted

def harvest_catchy_shorts():
    print("=== Scraping Fresh Catchy YouTube Shorts ===", flush=True)
    all_reels = []
    seen_ids = set()

    tasks = []
    for cat_info in SEARCH_CATEGORIES:
        c_name = cat_info["category"]
        for q in cat_info["queries"]:
            tasks.append((q, c_name))

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_to_task = {executor.submit(fetch_shorts_for_query, q, c): (q, c) for q, c in tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            q, c = future_to_task[future]
            try:
                items = future.result()
                print(f"Fetched {len(items)} Shorts for query: '{q}' ({c})", flush=True)
                for item in items:
                    vid = item["id"]
                    if vid not in seen_ids:
                        seen_ids.add(vid)
                        all_reels.append(item)
            except Exception as exc:
                print(f"Task generated exception for {q}: {exc}", file=sys.stderr)

    print(f"\nTotal unique Shorts harvested: {len(all_reels)}", flush=True)
    if len(all_reels) < 20:
        print("WARNING: Insufficient videos scraped. Keeping existing feed.")
        return

    # Shuffle for natural category mix and variety
    random.seed(int(time.time()))
    random.shuffle(all_reels)

    final_reels = all_reels[:DATASET_CAP] if len(all_reels) > DATASET_CAP else all_reels
    next_ver = get_next_version(RULES_JSON_PATH, min_version=4.0)

    out_data = {
        "version": next_ver,
        "last_updated": int(time.time() * 1000),
        "total_count": len(final_reels),
        "reels": final_reels
    }

    # 1. Write to social-saver-rules repo
    if os.path.exists(RULES_REPO_DIR):
        with open(RULES_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2, ensure_ascii=False)
        print(f"SUCCESS: Written {len(final_reels)} catchy YouTube Shorts to {RULES_JSON_PATH} (v{next_ver})!", flush=True)

        # Copy generator script to social-saver-rules as well
        rules_script_path = os.path.join(RULES_REPO_DIR, "generate_youtube_trending.py")
        with open(__file__, "r", encoding="utf-8") as src, open(rules_script_path, "w", encoding="utf-8") as dst:
            dst.write(src.read())

        push_to_github(RULES_REPO_DIR, RULES_JSON_PATH, next_ver)

    # 2. Also write directly to local app assets so offline works instantly
    if os.path.exists(os.path.dirname(LOCAL_ASSET_PATH)):
        with open(LOCAL_ASSET_PATH, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2, ensure_ascii=False)
        print(f"SUCCESS: Synced {len(final_reels)} catchy Shorts to app assets: {LOCAL_ASSET_PATH}!", flush=True)

def push_to_github(repo_dir, filepath, version):
    print(f"=== Committing & Pushing {filepath} (v{version}) to Git main branch ===", flush=True)
    try:
        import subprocess
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
        commit_msg = f"Update YouTube Shorts feed v{version} with catchy viral Shorts"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_dir, check=False)
        subprocess.run(["git", "push", "origin", "main"], cwd=repo_dir, check=False)
        print(f"Git push executed for v{version}.", flush=True)
    except Exception as e:
        print(f"Git push warning: {e}", flush=True)

if __name__ == "__main__":
    harvest_catchy_shorts()
