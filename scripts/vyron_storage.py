#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Real Storage & Filesystem Management Tool
Location: /usr/local/bin/vyron-storage
Queries real Linux storage facilities (lsblk, findmnt, df, blkid, /sys/block).
Provides CLI formatted disk/partition status and structured JSON for desktop apps.
==============================================================================
"""

import sys
import os
import json
import subprocess
import shutil

def run_cmd(args):
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=5)
        return res.stdout.strip()
    except Exception:
        return ""

def get_block_devices():
    """Retrieve block devices with partition hierarchy, sizes, types, and UUIDs."""
    out = run_cmd(["lsblk", "-o", "NAME,FSTYPE,SIZE,MOUNTPOINT,UUID,TYPE,MODEL", "-J"])
    if out:
        try:
            return json.loads(out).get("blockdevices", [])
        except Exception:
            pass
    return []

def get_mount_info():
    """Retrieve all mounted filesystems with mount options, types, and usage."""
    mounts = []
    out = run_cmd(["findmnt", "-l", "-o", "TARGET,SOURCE,FSTYPE,OPTIONS", "-J"])
    if out:
        try:
            mounts = json.loads(out).get("filesystems", [])
        except Exception:
            pass
    return mounts

def get_disk_usage():
    """Retrieve filesystem capacity, used space, free space, and percentages."""
    usage = []
    out = run_cmd(["df", "-h", "--output=source,fstype,size,used,avail,pcent,target", "-x", "tmpfs", "-x", "devtmpfs", "-x", "squashfs"])
    if out:
        lines = out.splitlines()
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 7:
                    usage.append({
                        "source": parts[0],
                        "fstype": parts[1],
                        "size": parts[2],
                        "used": parts[3],
                        "avail": parts[4],
                        "pcent": parts[5],
                        "target": parts[6]
                    })
    return usage

def get_storage_overview():
    return {
        "blockdevices": get_block_devices(),
        "usage": get_disk_usage(),
        "mounts": get_mount_info()
    }

def print_cli_storage():
    overview = get_storage_overview()
    print("==========================================================================")
    print("  VYRON OS — Real Storage & Filesystem Subsystem")
    print("==========================================================================")
    print("  MOUNTED FILESYSTEM USAGE (df -h):")
    print(f"  {'Filesystem':<18} {'Type':<8} {'Size':<8} {'Used':<8} {'Avail':<8} {'Use%':<6} {'Mountpoint'}")
    print("  " + "-" * 70)
    for u in overview["usage"]:
        print(f"  {u['source']:<18} {u['fstype']:<8} {u['size']:<8} {u['used']:<8} {u['avail']:<8} {u['pcent']:<6} {u['target']}")

    print("\n  BLOCK DEVICE TOPOLOGY (lsblk):")
    def print_device(dev, indent="  "):
        name = dev.get("name", "")
        fstype = dev.get("fstype") or "-"
        size = dev.get("size", "")
        mount = dev.get("mountpoint") or "-"
        uuid = dev.get("uuid") or "-"
        dtype = dev.get("type", "")
        print(f"{indent}• /dev/{name:<10} [{dtype:<4}] Size: {size:<7} FSTYPE: {fstype:<8} Mount: {mount}")
        if uuid != "-":
            print(f"{indent}  UUID: {uuid}")
        for child in dev.get("children", []):
            print_device(child, indent + "    ")

    for dev in overview["blockdevices"]:
        if dev.get("name") not in ["fd0", "sr0"] or dev.get("size") != "4K":
            print_device(dev)

    print("==========================================================================")

def main():
    if "--json" in sys.argv:
        print(json.dumps(get_storage_overview(), indent=2))
    elif "--df" in sys.argv:
        print(json.dumps(get_disk_usage(), indent=2))
    else:
        print_cli_storage()

if __name__ == "__main__":
    main()
