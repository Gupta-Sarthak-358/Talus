import os
import sys
import time
import json
import re
import urllib.request
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

MANIFEST_PATH = r"runs/phase_v/vi2/download_manifest.json"
TARGET_DIR = r"c:/Users/satvi/Desktop/Talus"
LOG_FILE = r"runs/phase_v/vi2/download_progress.log"
NUM_WORKERS = 3

log_lock = threading.Lock()
def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    formatted = f"[{ts}] {msg}"
    print(formatted, flush=True)
    with log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")

def get_page_links(page_url):
    req = urllib.request.Request(page_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    matches = re.findall(r"<a\s+[^>]*href=['\"]([^'\"]+)['\"][^>]*>([^<]+)</a>", html, re.IGNORECASE)
    link_map = {}
    for href, text in matches:
        link_map[text.strip()] = href.strip()
    return link_map

def download_file(url, out_path):
    thread_id = threading.get_ident()
    temp_path = f"{out_path}.{thread_id}.part"
    cmd = ["curl.exe", "-L", "-s", "-S", "--connect-timeout", "30", "--max-time", "600", "-o", temp_path, url]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass
        return False, res.stderr
    if not os.path.exists(temp_path) or os.path.getsize(temp_path) < 1000:
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass
        return False, "File missing or too small"
    
    # Retry rename loop for Windows file lock release
    renamed = False
    for r_try in range(10):
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
            os.replace(temp_path, out_path)
            renamed = True
            break
        except PermissionError:
            time.sleep(0.5)
        except Exception as ex:
            time.sleep(0.5)
            
    if not renamed:
        return False, f"Could not rename {temp_path} to {out_path} due to Windows file lock"
    return True, None

def process_item(item):
    ev_key = item["event"]
    fname = item["file"]
    page_url = item["page"]
    out_path = os.path.join(TARGET_DIR, fname)

    if os.path.exists(out_path) and os.path.getsize(out_path) >= 1000:
        log(f"  [SKIPPED] {fname} already exists ({os.path.getsize(out_path)} bytes).")
        return "skipped"

    # Fetch page link
    link_map = None
    for page_try in range(1, 4):
        try:
            link_map = get_page_links(page_url)
            break
        except Exception:
            time.sleep(2)

    if not link_map or fname not in link_map:
        log(f"  [FAILED] Could not get direct link for {fname} from {page_url}")
        return "failed"

    direct_url = link_map[fname]
    log(f"  [DOWNLOADING] {fname} ({ev_key}) ...")

    success = False
    for attempt in range(1, 4):
        ok, err = download_file(direct_url, out_path)
        if ok:
            size_mb = os.path.getsize(out_path) / (1024 * 1024)
            log(f"  [SUCCESS] {fname} ({size_mb:.2f} MB landed in Talus root).")
            success = True
            break
        else:
            log(f"  [RETRY] Attempt {attempt} failed for {fname}: {err}")
            time.sleep(3)

    if not success:
        log(f"  [FAILED 3x] {fname} recorded as missing.")
        return "failed"

    time.sleep(2)
    return "success"

def run():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    events = manifest["events"]

    # Queue ordered: Mantam first, then chronological
    event_keys = []
    if "NEWS-MANTAM-20160813" in events:
        event_keys.append("NEWS-MANTAM-20160813")
    other_events = sorted([k for k in events.keys() if k != "NEWS-MANTAM-20160813"], key=lambda k: events[k]["T"])
    event_keys.extend(other_events)

    items = []
    seen_files = set()

    for ev_key in event_keys:
        ev = events[ev_key]
        t_compact = ev["T"].replace("-", "")
        for p in ev["pairs"]:
            pair_name = p["pair"]
            sec_date = pair_name.split("_")[1]
            if sec_date >= t_compact:
                continue # Invariant enforcement: no secondary >= T
            for fname in p["files"]:
                if fname not in seen_files:
                    seen_files.add(fname)
                    items.append({
                        "event": ev_key,
                        "pair": pair_name,
                        "slot": p["slot"],
                        "frame": p["frame"],
                        "page": p["page"],
                        "file": fname
                    })

    log(f"Starting deduplicated parallel downloader with {NUM_WORKERS} workers. Total unique files: {len(items)}")

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        results = list(executor.map(process_item, items))

    successes = results.count("success")
    skipped = results.count("skipped")
    failures = results.count("failed")
    log(f"Finished! Successes: {successes}, Already present: {skipped}, Failures: {failures}")

if __name__ == "__main__":
    run()
