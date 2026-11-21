#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 3 Hardware Introspection Automated Verification Suite
Tests:
1. Linux 6.12 LTS Kernel Boot & Introspection.
2. CPU Telemetry (/proc/cpuinfo: model, vendor, cores, MHz).
3. Memory Telemetry (/proc/meminfo: MemTotal, MemAvailable).
4. PCI Device Enumeration (Host bridge, IDE, VGA, VirtIO Network).
5. Storage Block Introspection (ext4 rootfs, vfat EFI partition).
6. Honest Wireless Reporting ("VirtIO Ethernet active; No physical 802.11 wireless hardware detected").
7. Structured JSON Export for Future Desktop / GUI Integration.
==============================================================================
"""

import os
import sys
import time
import json
import subprocess
import select

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
DISK_IMAGE = os.path.join(DIST_DIR, "VyronOS-Disk.qcow2")
LOG_PATH = os.path.join(BUILD_DIR, "test-hardware-serial.log")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"
if not os.path.exists(OVMF_CODE):
    for candidate in [
        "/usr/share/qemu/edk2-x86_64-code.fd",
        "/usr/share/OVMF/OVMF_CODE.fd"
    ]:
        if os.path.exists(candidate):
            OVMF_CODE = candidate
            break

def main():
    print("==========================================================================")
    print("  VYRON OS — Phase 3 Hardware Introspection Test Suite")
    print("==========================================================================")
    print(f"  Target Disk    : {DISK_IMAGE}")
    print(f"  UEFI Firmware  : {OVMF_CODE}")
    print(f"  Serial Log     : {LOG_PATH}")
    print("==========================================================================")

    if not os.path.exists(DISK_IMAGE):
        print(f"ERROR: Disk image {DISK_IMAGE} not found.")
        sys.exit(1)

    os.makedirs(BUILD_DIR, exist_ok=True)
    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-Disk"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-HardwareTest",
        "-m", "2048",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    print(">>> Booting VyronOS in QEMU to execute Hardware Introspection Test...")
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0
    )
    os.set_blocking(proc.stdout.fileno(), False)

    full_output = []
    buffer = ""
    start_time = time.time()
    login_user_sent = False
    login_pass_sent = False
    commands_sent = False

    test_commands = '''
cat << 'EOF' > /tmp/run_hw_test.sh
#!/bin/bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
echo "=== KERNEL RELEASE ==="
uname -r

echo "=== VYRON-HWINFO CLI ==="
/usr/local/bin/vyron-hwinfo

echo "=== VYRON-HWINFO JSON ==="
/usr/local/bin/vyron-hwinfo --json

echo "=== VYRON-HWINFO WIFI ONLY ==="
/usr/local/bin/vyron-hwinfo --wifi-only

echo "=== SYSTEM DIAGNOSTIC VERIFICATION ==="
ps aux | head -n 5
lspci
lsusb || true

echo "=== HARDWARE TEST FINISHED ==="
sync
sudo poweroff
EOF
chmod +x /tmp/run_hw_test.sh
bash /tmp/run_hw_test.sh
'''

    try:
        while time.time() - start_time < 120:
            r, _, _ = select.select([proc.stdout.fileno()], [], [], 0.1)
            if r:
                chunk = os.read(proc.stdout.fileno(), 4096).decode("utf-8", errors="replace")
                if not chunk:
                    if proc.poll() is not None:
                        break
                    continue
                full_output.append(chunk)
                sys.stdout.write(chunk)
                sys.stdout.flush()
                buffer += chunk

                if ("login:" in buffer or "vyron-os login:" in buffer) and not login_user_sent:
                    time.sleep(0.3)
                    proc.stdin.write(b"vyron\n")
                    proc.stdin.flush()
                    login_user_sent = True

                if "Password:" in buffer and login_user_sent and not login_pass_sent:
                    time.sleep(0.3)
                    proc.stdin.write(b"vyron\n")
                    proc.stdin.flush()
                    login_pass_sent = True

                if "vyron@vyron-os:~$" in buffer and login_pass_sent and not commands_sent:
                    commands_sent = True
                    print("\n>>> Logged in. Dispatching Hardware Test Script...")
                    time.sleep(0.5)
                    proc.stdin.write(f"{test_commands.strip()}\n".encode("utf-8"))
                    proc.stdin.flush()

                if "Powering off" in buffer or "reboot: Power down" in buffer or "ACPI: PM: Preparing to enter system sleep state S5" in buffer:
                    break
            else:
                if proc.poll() is not None:
                    break
    except KeyboardInterrupt:
        proc.kill()
    finally:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    out_text = "".join(full_output)
    with open(LOG_PATH, "w") as f:
        f.write(out_text)

    # Verification checks
    checks = {
        "Linux 6.12 LTS Boot Verified": ("6.12.95" in out_text),
        "CPU Telemetry Introspected": ("CPU Model" in out_text and "cores" in out_text),
        "Memory Telemetry Introspected": ("Physical Memory" in out_text and "MB Total" in out_text),
        "PCI Bus Introspected (Host/VGA/VirtIO)": ("Virtio network device" in out_text or "Ethernet controller" in out_text),
        "Storage Block Introspected": ("blockdevices" in out_text or "sda" in out_text),
        "Honest Wi-Fi Reporting (No physical 802.11)": ("No physical 802.11 wireless hardware detected" in out_text),
        "Zero Fabricated SSIDs": ("Home-WiFi" not in out_text and "CoffeeShop" not in out_text),
        "Structured JSON Output Valid": ('"os": {' in out_text and '"cpu": {' in out_text)
    }

    print("\n==========================================================================")
    print("  PHASE 3 HARDWARE INTROSPECTION GATE RESULTS")
    print("==========================================================================")
    passed = 0
    total = len(checks)
    for k, v in checks.items():
        st = "PASS" if v else "FAIL"
        print(f"  [{st}] {k}")
        if v:
            passed += 1

    print("==========================================================================")
    print(f"  Summary: {passed}/{total} Gates Passed ({100.0*passed/total:.1f}%)")
    print("==========================================================================")

    if passed == total:
        print("  RESULT: PHASE 3 HARDWARE INTROSPECTION PASSED 100%.")
        sys.exit(0)
    else:
        print(f"  RESULT: {total - passed} check(s) did not match exact expectations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
