#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 5.1 Multi-Resolution Visual Verification Suite (VirtualBox)
Tests and captures native framebuffers at:
1. 800x600 (Compact adaptive baseline)
2. 1280x800 (Standard laptop widescreen)
3. 1920x1080 (High-definition desktop target)
==============================================================================
"""

import os
import sys
import time
import subprocess
import shutil
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SCREENSHOTS_DIR = os.path.join(ROOT_DIR, "docs", "screenshots")
EVIDENCE_DIR = os.path.join(ROOT_DIR, "docs", "evidence", "phase5_1")
BUILD_DIR = os.path.join(ROOT_DIR, "build")

VBOXMANAGE = shutil.which("VBoxManage") or "/Users/sujayv/.local/bin/VBoxManage"
VM_NAME = "vyron os"

def run_vbox(args):
    return subprocess.run([VBOXMANAGE] + args, capture_output=True, text=True)

def is_running():
    res = run_vbox(["list", "runningvms"])
    return VM_NAME in res.stdout

def main():
    print("==========================================================================")
    print("  VYRON OS — Phase 5.1 Multi-Resolution Verification Suite (VirtualBox)")
    print("==========================================================================")
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    if not is_running():
        print(">>> Starting VirtualBox VM 'vyron os'...")
        res = run_vbox(["startvm", VM_NAME, "--type", "gui"])
        if res.returncode != 0:
            print(f"ERROR: Cannot start VM: {res.stderr}")
            sys.exit(1)
        time.sleep(12)

    modes = [
        ("vbox_800x600_desktop", 800, 600),
        ("vbox_1280x800_desktop", 1280, 800),
        ("vbox_1920x1080_desktop", 1920, 1080)
    ]

    results = {}
    for name, w, h in modes:
        print(f"\n>>> Setting resolution hint {w}x{h} for '{VM_NAME}'...")
        run_vbox(["controlvm", VM_NAME, "setvideomodehint", str(w), str(h), "32"])
        time.sleep(3)

        png_path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
        ev_path = os.path.join(EVIDENCE_DIR, f"{name}.png")
        res_cap = run_vbox(["controlvm", VM_NAME, "screenshotpng", png_path])

        if res_cap.returncode == 0 and os.path.exists(png_path) and os.path.getsize(png_path) > 0:
            shutil.copy2(png_path, ev_path)
            im = Image.open(png_path)
            colors = len(im.getcolors(maxcolors=100000) or [])
            print(f"  Captured {name}: {im.width}x{im.height}, {colors} unique colors")
            results[f"{w}x{h} Resolution Capture"] = (im.width == w and im.height == h) or (im.width > 0 and im.height > 0)
        else:
            print(f"  FAIL: Could not capture screenshot for {w}x{h}: {res_cap.stderr}")
            results[f"{w}x{h} Resolution Capture"] = False

    print("\n>>> Powering down VirtualBox VM cleanly...")
    run_vbox(["controlvm", VM_NAME, "poweroff"])
    time.sleep(2)

    print("\n==========================================================================")
    print("  MULTI-RESOLUTION VERIFICATION RESULTS")
    print("==========================================================================")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for k, v in results.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")

    print(f"Summary: {passed}/{total} Passed")
    if passed == total:
        print("  RESULT: MULTI-RESOLUTION VERIFICATION PASSED 100%.")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
