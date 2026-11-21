#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Oracle VM VirtualBox Hypervisor & Desktop Manager
Location: scripts/vbox_manager.py
Manages VM lifecycle, display geometry, screenshot capture, and test validation
directly through VirtualBox's native VBoxManage management interface.
==============================================================================
"""

import os
import sys
import time
import subprocess
import json
import shutil
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SCREENSHOTS_DIR = os.path.join(ROOT_DIR, "docs", "screenshots")
EVIDENCE_DIR = os.path.join(ROOT_DIR, "docs", "evidence", "phase5")

VM_NAME = "vyron os"

# Locate VBoxManage
VBOXMANAGE = shutil.which("VBoxManage")
if not VBOXMANAGE or not os.path.exists(VBOXMANAGE):
    candidates = [
        "/Users/sujayv/.local/bin/VBoxManage",
        "/Applications/VirtualBox.app/Contents/MacOS/VBoxManage",
        "/usr/local/bin/VBoxManage"
    ]
    for c in candidates:
        if os.path.exists(c):
            VBOXMANAGE = c
            break

if not VBOXMANAGE:
    print("ERROR: VBoxManage not found on system.")
    sys.exit(1)

def run_vbox(args, check=False):
    cmd = [VBOXMANAGE] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"VBoxManage command failed ({res.returncode}): {' '.join(cmd)}\n{res.stderr}")
    return res

def is_vm_running(vm_name=VM_NAME):
    res = run_vbox(["list", "runningvms"])
    return vm_name in res.stdout

def get_vm_info(vm_name=VM_NAME):
    res = run_vbox(["showvminfo", vm_name, "--machinereadable"])
    info = {}
    if res.returncode == 0:
        for line in res.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                info[k.strip().strip('"')] = v.strip().strip('"')
    return info

def start_vm(vm_name=VM_NAME, wait_seconds=5):
    if is_vm_running(vm_name):
        print(f"VM '{vm_name}' is already running.")
        return True
    print(f">>> Starting VirtualBox VM '{vm_name}' (GUI mode)...")
    res = run_vbox(["startvm", vm_name, "--type", "gui"])
    if res.returncode != 0:
        print(f"ERROR starting VM: {res.stderr}")
        return False
    print(f"Waiting {wait_seconds}s for VM to stabilize...")
    time.sleep(wait_seconds)
    return True

def stop_vm(vm_name=VM_NAME, force=False):
    if not is_vm_running(vm_name):
        print(f"VM '{vm_name}' is already stopped.")
        return True
    if force:
        print(f">>> Powering off VirtualBox VM '{vm_name}'...")
        run_vbox(["controlvm", vm_name, "poweroff"])
    else:
        print(f">>> Gracefully stopping VirtualBox VM '{vm_name}' (ACPI power button)...")
        run_vbox(["controlvm", vm_name, "acpipowerbutton"])
        for _ in range(15):
            if not is_vm_running(vm_name):
                print(f"VM '{vm_name}' stopped cleanly.")
                return True
            time.sleep(1)
        print("ACPI shutdown timed out; forcing poweroff...")
        run_vbox(["controlvm", vm_name, "poweroff"])
    time.sleep(1)
    return not is_vm_running(vm_name)

def capture_screenshot(output_path, vm_name=VM_NAME):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    if not is_vm_running(vm_name):
        print(f"ERROR: Cannot capture screenshot; VM '{vm_name}' is not running.")
        return False
    res = run_vbox(["controlvm", vm_name, "screenshotpng", output_path])
    if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        try:
            im = Image.open(output_path)
            print(f"Captured VirtualBox screenshot: {output_path} ({im.width}x{im.height}, {im.mode})")
            return True
        except Exception as e:
            print(f"Screenshot written but failed to open: {e}")
            return False
    else:
        print(f"ERROR: Failed to capture screenshot via VBoxManage: {res.stderr}")
        return False

def set_video_mode(width, height, bpp=32, vm_name=VM_NAME):
    print(f">>> Setting video mode hint to {width}x{height}x{bpp} for '{vm_name}'...")
    res = run_vbox(["controlvm", vm_name, "setvideomodehint", str(width), str(height), str(bpp)])
    # Also set EFI resolution extradata
    run_vbox(["setextradata", vm_name, "VBoxInternal2/EfiGraphicsResolution", f"{width}x{height}"])
    return res.returncode == 0

def inspect_vm_hardware(vm_name=VM_NAME):
    info = get_vm_info(vm_name)
    print("==========================================================================")
    print(f"  VIRTUALBOX VM HARDWARE CONFIGURATION: {vm_name}")
    print("==========================================================================")
    print(f"  VM Name             : {info.get('name', 'N/A')}")
    print(f"  UUID                : {info.get('UUID', 'N/A')}")
    print(f"  Guest OS Type       : {info.get('ostype', 'N/A')}")
    print(f"  CPU Count           : {info.get('cpus', 'N/A')}")
    print(f"  Memory (RAM)        : {info.get('memory', 'N/A')} MB")
    print(f"  VRAM (Video RAM)    : {info.get('vram', 'N/A')} MB")
    print(f"  Graphics Controller : {info.get('graphicscontroller', 'N/A')}")
    print(f"  Pointing Device     : {info.get('pointing', 'N/A')}")
    print(f"  Keyboard Device     : {info.get('keyboard', 'N/A')}")
    print(f"  Firmware            : {info.get('firmware', 'N/A')}")
    print(f"  Network Adapter 1   : {info.get('nic1', 'N/A')} ({info.get('nictype1', 'N/A')})")
    print(f"  Storage Port 0 (HDD): {info.get('SATA-0-0', 'N/A')}")
    print(f"  Storage Port 1 (DVD): {info.get('SATA-1-0', 'N/A')}")
    print(f"  State               : {'RUNNING' if is_vm_running(vm_name) else 'POWERED OFF'}")
    print("==========================================================================")
    return info

def main():
    if len(sys.argv) < 2:
        print("Usage: vbox_manager.py [info|start|stop|restart|screenshot <path>|resolution <w> <h>]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "info":
        inspect_vm_hardware()
    elif cmd == "start":
        start_vm()
    elif cmd == "stop":
        stop_vm(force=("-f" in sys.argv or "--force" in sys.argv))
    elif cmd == "restart":
        stop_vm()
        time.sleep(2)
        start_vm()
    elif cmd == "screenshot":
        path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SCREENSHOTS_DIR, "vbox_current_screen.png")
        capture_screenshot(path)
    elif cmd == "resolution":
        if len(sys.argv) < 4:
            print("Usage: vbox_manager.py resolution <width> <height>")
            sys.exit(1)
        w, h = int(sys.argv[2]), int(sys.argv[3])
        set_video_mode(w, h)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
