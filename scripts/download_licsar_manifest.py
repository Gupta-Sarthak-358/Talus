import os
import sys
import time
import json
import re
import urllib.request
import subprocess

MANIFEST_PATH = r"runs/phase_v/vi2/download_manifest.json"
TARGET_DIR = r"c:/Users/satvi/Desktop/Talus"
LOG_FILE = r"runs/phase_v/vi2/download_progress.log"

def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def get_page_links(page_url):
    req = urllib.request.Request(page_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    # Matches href='...' or href="..."
    matches = re.findall(r"<a\s+[^>]*href=['\"]([^'\"]+)['\"][^>]*>([^<]+)</a>", html, re.IGNORECASE)
    link_map = {}
    for href, text in matches:
        link_map[text.strip()] = href.strip()
    return link_map

def download_file(url, out_path):
    # Use curl.exe directly with -L to follow redirects (handles CEDA 302 -> dap.ceda.ac.uk)
    cmd = ["curl.exe", "-L", "-s", "-S", "--connect-timeout", "30", "--max-time", "600", "-o", out_path, url]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return False, res.stderr
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 1000:
        return False, f"File missing or too small ({os.path.getsize(out_path) if os.path.exists(out_path) else 0} bytes)"
    return True, None

def run():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    events = manifest["events"]
    
    # Priority order:
    # 1. NEWS-MANTAM-20160813
    # 2. Chronological by T
    event_keys = []
    if "NEWS-MANTAM-20160813" in events:
        event_keys.append("NEWS-MANTAM-20160813")
    
    other_events = sorted([k for k in events.keys() if k != "NEWS-MANTAM-20160813"], key=lambda k: events[k]["T"])
    event_keys.extend(other_events)

    log(f"Starting downloader. Total events: {len(event_keys)}")

    total_downloaded = 0
    total_skipped = 0
    failures = {}

    for ev_key in event_keys:
        ev = events[ev_key]
        t_date = ev["T"]
        pairs = ev["pairs"]
        log(f"--- Event: {ev_key} (T = {t_date}) [{len(pairs)} pairs] ---")

        for p_idx, p in enumerate(pairs):
            frame = p["frame"]
            slot = p["slot"]
            pair_name = p["pair"]
            page_url = p["page"]
            target_files = p["files"]

            # Invariant check: pair dates must not be >= T
            sec_date = pair_name.split("_")[1]
            # t_date string format YYYY-MM-DD vs YYYYMMDD
            t_compact = t_date.replace("-", "")
            if sec_date >= t_compact:
                log(f"INVARIANT VIOLATION: {pair_name} secondary >= {t_compact}! Skipping.")
                continue

            # Check if all files for this pair already exist in root
            needed_files = [f for f in target_files if not os.path.exists(os.path.join(TARGET_DIR, f))]
            if not needed_files:
                log(f"  [Pair {p_idx+1}/{len(pairs)}] {pair_name} ({slot}) already present in Talus root. Skipping.")
                continue

            log(f"  [Pair {p_idx+1}/{len(pairs)}] {pair_name} ({slot}) - Visiting page: {page_url}")
            
            # Fetch links from page (with 3 retries)
            link_map = None
            for page_try in range(1, 4):
                try:
                    link_map = get_page_links(page_url)
                    break
                except Exception as e:
                    log(f"    Page fetch attempt {page_try} failed: {e}")
                    time.sleep(5)

            if not link_map:
                log(f"    ERROR: Failed to load page {page_url} after 3 attempts. Skipping pair.")
                failures[pair_name] = "Page load failed"
                continue

            for fname in target_files:
                out_path = os.path.join(TARGET_DIR, fname)
                if os.path.exists(out_path):
                    log(f"    {fname} already exists ({os.path.getsize(out_path)} bytes). Skipping.")
                    total_skipped += 1
                    continue

                if fname not in link_map:
                    log(f"    WARNING: {fname} not found in page links! Available: {list(link_map.keys())}")
                    failures[fname] = "Not in page"
                    continue

                direct_url = link_map[fname]
                log(f"    Downloading {fname} from {direct_url}...")

                success = False
                for attempt in range(1, 4):
                    ok, err = download_file(direct_url, out_path)
                    if ok:
                        size_mb = os.path.getsize(out_path) / (1024 * 1024)
                        log(f"    SUCCESS: {fname} ({size_mb:.2f} MB) landed in Talus root.")
                        success = True
                        total_downloaded += 1
                        break
                    else:
                        log(f"    Attempt {attempt} failed for {fname}: {err}")
                        if os.path.exists(out_path):
                            try:
                                os.remove(out_path)
                            except:
                                pass
                        time.sleep(5)

                if not success:
                    log(f"    FAILED: {fname} after 3 attempts. Recorded as missing.")
                    failures[fname] = "Download failed 3x"

                # Polite single client: wait >= 5s between file downloads
                time.sleep(5)

    log(f"Downloader complete! Total downloaded: {total_downloaded}, Total skipped: {total_skipped}, Failures: {len(failures)}")
    if failures:
        log("Failures summary:")
        for k, v in failures.items():
            log(f"  {k}: {v}")

if __name__ == "__main__":
    run()
