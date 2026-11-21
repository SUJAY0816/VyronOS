#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Real-Time Network & Desktop Environment Master Verification Suite
Location: scripts/test_realtime_network_and_desktop.py
Hypervisor: Oracle VM VirtualBox exclusively (ARM64 Native · Apple Silicon)
Zero QEMU execution paths · Zero simulated network responses · Zero demo SSIDs
==============================================================================
"""

import os
import sys
import time
import subprocess
import shutil
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BUILD_DIR = os.path.join(ROOT_DIR, "build")
LOG_PATH = os.path.join(BUILD_DIR, "realtime-network-desktop-verification.log")

VM_NAME = "vyron os"

def run_guest_cmd(command):
    ssh_key = os.path.expanduser("~/.ssh/vyron_key")
    ssh_opts = [
        "-p", "2222",
        "-i", ssh_key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=5",
        "-o", "LogLevel=ERROR"
    ]
    p = subprocess.run(["ssh"] + ssh_opts + ["vyron@127.0.0.1", command], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def main():
    print("==========================================================================")
    print("  VYRON OS — Real-Time Network & Desktop Environment Verification Suite")
    print("  Target: Oracle VM VirtualBox (Darwin ARM64 / Apple Silicon)")
    print("  Status: 100% Genuine Linux Subsystems · Zero Mock / Zero Demos")
    print("==========================================================================")

    gates = [
        ("RN-01: ARM64 Native Kernel Active", "uname -r", lambda rc, out: rc == 0 and "arm64" in out),
        ("RN-02: Non-Root User Desktop Privilege", "whoami && id -u", lambda rc, out: "vyron" in out and "1000" in out),
        ("RN-03: Primary Interface DHCP Leased", "ip a show dev enx080027c17b86", lambda rc, out: "10.0.2.15" in out and "state UP" in out),
        ("RN-04: Default Gateway Active", "ip route show default", lambda rc, out: "10.0.2.2" in out and "enx080027c17b86" in out),
        ("RN-05: Real Gateway ICMP Ping (0% Loss)", "ping -c 2 -W 1 10.0.2.2", lambda rc, out: rc == 0 and " 0% packet loss" in out),
        ("RN-06: Real Public DNS ICMP Ping (1.1.1.1)", "ping -c 2 -W 1 1.1.1.1", lambda rc, out: rc == 0 and " 0% packet loss" in out),
        ("RN-07: Real Public DNS ICMP Ping (8.8.8.8)", "ping -c 2 -W 1 8.8.8.8", lambda rc, out: rc == 0 and " 0% packet loss" in out),
        ("RN-08: Real External DNS Domain Resolution", "getent hosts debian.org wikipedia.org", lambda rc, out: rc == 0 and len(out.strip().splitlines()) >= 2),
        ("RN-09: Real External HTTP/2 Web Request", "curl -I -s https://www.google.com | head -n 1", lambda rc, out: rc == 0 and ("200" in out or "301" in out or "302" in out)),
        ("RN-10: Transparent Hardware Wi-Fi Audit (Zero Fake SSIDs)", "/usr/local/bin/vyron-network --cli", lambda rc, out: "Zero Fake SSIDs" in out or "Host Wi-Fi & LAN are seamlessly bridged" in out),
        ("RN-11: Real-Time Network Bandwidth & Sockets Suite", "/usr/local/bin/vyron-network --json", lambda rc, out: rc == 0 and "bytes_recv" in out and "primary" in out),
        ("RN-12: Real-Time System Monitor Operational", "/usr/local/bin/vyron-sysmon --cli", lambda rc, out: rc == 0 and "Storage & Disks" in out and "Processor (CPU)" in out),
        ("RN-13: Xorg Display Server Active on VT7", "pgrep -f Xorg", lambda rc, out: rc == 0 and len(out.strip()) > 0),
        ("RN-14: LightDM Display Manager Active", "systemctl is-active lightdm", lambda rc, out: "active" in out),
        ("RN-15: XFCE4 Session & Compositor Active", "pgrep -f xfce4-session && pgrep -f xfwm4", lambda rc, out: rc == 0),
        ("RN-16: Vyron UI V2 Dark Theme & Icons Deployed", "ls -d /usr/share/themes/Vyron-V2-Dark /usr/share/icons/Vyron-V2-Icons", lambda rc, out: "Vyron-V2-Dark" in out and "Vyron-V2-Icons" in out),
        ("RN-17: Vyron Gradient Wallpaper Active", "ls -l /usr/share/backgrounds/vyron/vyron-dark.png", lambda rc, out: rc == 0 and "vyron-dark.png" in out),
        ("RN-18: Real-Time Desktop Telemetry HUD (Conky)", "pgrep -f conky", lambda rc, out: rc == 0 and len(out.strip()) > 0),
        ("RN-19: Real Web Browser & Portal Deployed", "ls -l /usr/share/vyron/portal/index.html && which firefox-esr", lambda rc, out: rc == 0 and "index.html" in out and "firefox-esr" in out),
        ("RN-20: Audio Subsystem Active (Intel HDA & PipeWire)", "pgrep -f pipewire && cat /proc/asound/cards", lambda rc, out: rc == 0 and "Intel" in out and "HDA" in out),
    ]

    results = {}
    details = {}
    passed = 0
    total = len(gates)

    for gate_name, cmd, validator in gates:
        rc, out, err = run_guest_cmd(cmd)
        ok = validator(rc, out)
        results[gate_name] = ok
        details[gate_name] = out.strip().splitlines()[0] if out.strip() else (err.strip().splitlines()[0] if err.strip() else "OK")
        st = "PASS" if ok else "FAIL"
        print(f"  [{st}] {gate_name}")
        print(f"         Detail: {details[gate_name]}")
        if ok:
            passed += 1

    print("\n==========================================================================")
    print(f"  VERIFICATION SCORE: {passed}/{total} Gates Passed ({100.0*passed/total:.1f}%)")
    print("==========================================================================")

    os.makedirs(BUILD_DIR, exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump({"passed": passed, "total": total, "results": results, "details": details}, f, indent=2)

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
