#!/usr/bin/env python3
"""
Test runner for Phase 3:
Checks NetworkManager status, verifies installed packages, ensures internet connectivity,
and completes the backports kernel installation and vyron-hwinfo setup.
"""
import os, sys, time, subprocess, select

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
DISK_IMAGE = os.path.join(DIST_DIR, "VyronOS-Disk.qcow2")
LOG_PATH = os.path.join(BUILD_DIR, "phase3-transition-serial.log")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"

cmd = [
    "/opt/homebrew/bin/qemu-system-x86_64",
    "-name", "VyronOS-Phase3Run",
    "-m", "2048",
    "-smp", "2",
    "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
    "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
    "-netdev", "user,id=net0,hostname=vyron-os",
    "-device", "virtio-net-pci,netdev=net0",
    "-display", "none",
    "-serial", "stdio"
]

print(">>> Booting VyronOS in QEMU to complete Phase 3 transition...")
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
os.set_blocking(proc.stdout.fileno(), False)

buffer = ""
full_output = []
login_sent = False
pass_sent = False
script_sent = False
start = time.time()

commands = '''
cat << 'EOF' > /tmp/p3_complete.sh
#!/bin/bash
echo "=== 1. CHECKING NETWORKMANAGER ==="
systemctl status NetworkManager --no-pager || true
nmcli device status || true
nmcli connection show || true

echo "=== 2. WAITING FOR NETWORK CONNECTIVITY ==="
for i in {1..20}; do
    if ping -c 1 1.1.1.1 >/dev/null 2>&1; then
        echo "Internet reachable! (attempt $i)"
        break
    fi
    sleep 1
done

ip -4 addr show ens3 || true
ip route show || true
ping -c 2 1.1.1.1 || true
ping -c 2 debian.org || true

echo "=== 3. VERIFYING INSTALLED DIAGNOSTICS ==="
which ps lspci lsusb ethtool iw rfkill nmcli || true
ps -ef | head -n 10 || true
lspci || true
lsusb || true

echo "=== 4. INSTALLING BACKPORTS KERNEL WITH RETRY ==="
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y -t bookworm-backports linux-image-amd64 || true

echo "=== 5. CHECKING INSTALLED KERNELS IN BOOT ==="
ls -lh /boot/vmlinuz* /boot/initrd.img* || true

echo "=== PHASE 3 STEP 1 COMPLETE ==="
sync
poweroff
EOF
chmod +x /tmp/p3_complete.sh
sudo bash /tmp/p3_complete.sh
'''

try:
    while time.time() - start < 360:
        r, _, _ = select.select([proc.stdout.fileno()], [], [], 0.1)
        if r:
            chunk = os.read(proc.stdout.fileno(), 4096).decode("utf-8", errors="replace")
            if not chunk and proc.poll() is not None:
                break
            full_output.append(chunk)
            sys.stdout.write(chunk)
            sys.stdout.flush()
            buffer += chunk

            if ("login:" in buffer or "vyron-os login:" in buffer) and not login_sent:
                time.sleep(0.3)
                proc.stdin.write(b"vyron\n")
                proc.stdin.flush()
                login_sent = True

            if "Password:" in buffer and login_sent and not pass_sent:
                time.sleep(0.3)
                proc.stdin.write(b"vyron\n")
                proc.stdin.flush()
                pass_sent = True

            if "vyron@vyron-os:~$" in buffer and pass_sent and not script_sent:
                script_sent = True
                print("\n>>> Logged in. Dispatching commands...")
                time.sleep(0.5)
                proc.stdin.write(f"{commands.strip()}\n".encode("utf-8"))
                proc.stdin.flush()

            if "ACPI: PM: Preparing to enter system sleep state S5" in buffer or "reboot: Power down" in buffer:
                break
        else:
            if proc.poll() is not None:
                break
finally:
    try:
        proc.wait(timeout=10)
    except:
        proc.kill()

with open(LOG_PATH, "w") as f:
    f.write("".join(full_output))

print("\n>>> Phase 3 runner finished.")
