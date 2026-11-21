#!/usr/bin/env python3
"""
Step 2: Download packages on macOS host in parallel and build debs.iso.
"""

import os
import sys
import urllib.request
import concurrent.futures
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BUILD_DIR = os.path.join(ROOT_DIR, "build")
URIS_FILE = os.path.join(BUILD_DIR, "debs_uris.txt")
DEBS_DIR = os.path.join(BUILD_DIR, "gui_debs")
ISO_PATH = os.path.join(BUILD_DIR, "debs.iso")

def download_file(item):
    url, filename, size = item
    dest = os.path.join(DEBS_DIR, filename)
    if os.path.exists(dest) and os.path.getsize(dest) == size:
        return filename, True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VyronOS-Downloader/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as out:
            out.write(resp.read())
        return filename, True
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return filename, False

def main():
    if not os.path.exists(URIS_FILE):
        print(f"ERROR: {URIS_FILE} not found.")
        sys.exit(1)

    os.makedirs(DEBS_DIR, exist_ok=True)

    items = []
    with open(URIS_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("'http"):
                parts = line.split()
                url = parts[0].strip("'")
                filename = parts[1]
                size = int(parts[2])
                items.append((url, filename, size))

    total = len(items)
    print(f"Starting parallel download of {total} packages into {DEBS_DIR}...")
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(download_file, it) for it in items]
        for fut in concurrent.futures.as_completed(futures):
            fn, ok = fut.result()
            if ok:
                completed += 1
                if completed % 10 == 0 or completed == total:
                    print(f"Progress: {completed}/{total} ({100.0*completed/total:.1f}%)")

    if completed < total:
        print(f"Warning: Only {completed}/{total} packages downloaded successfully.")
        sys.exit(1)

    print("Building debs.iso using xorriso...")
    if os.path.exists(ISO_PATH):
        os.remove(ISO_PATH)

    cmd = [
        "/opt/homebrew/bin/xorriso",
        "-as", "mkisofs",
        "-r", "-J",
        "-o", ISO_PATH,
        DEBS_DIR
    ]
    subprocess.run(cmd, check=True)
    print(f"SUCCESS: Built {ISO_PATH} ({os.path.getsize(ISO_PATH) // (1024*1024)} MB)")

if __name__ == "__main__":
    main()
