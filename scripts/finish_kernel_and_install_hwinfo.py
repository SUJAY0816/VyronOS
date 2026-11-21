#!/usr/bin/env python3
"""
Completes dpkg configuration, update-grub, deploys /usr/local/bin/vyron-hwinfo,
executes the hardware introspection report, and powers off cleanly.
"""
import os, sys, time, subprocess, select

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
DISK_IMAGE = os.path.join(DIST_DIR, "VyronOS-Disk.qcow2")
LOG_PATH = os.path.join(BUILD_DIR, "finish-kernel-hwinfo.log")
HWINFO_LOCAL = os.path.join(SCRIPT_DIR, "vyron_hwinfo.py")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"

import base64

with open(HWINFO_LOCAL, "rb") as f:
    hwinfo_b64 = base64.b64encode(f.read()).decode("ascii")

cmd = [
    "/opt/homebrew/bin/qemu-system-x86_64",
    "-name", "VyronOS-KernelFinish",
    "-m", "2048",
    "-smp", "2",
    "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
    "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
    "-netdev", "user,id=net0,hostname=vyron-os",
    "-device", "virtio-net-pci,netdev=net0",
    "-display", "none",
    "-serial", "stdio"
]

print(">>> Booting VyronOS in QEMU to finish kernel configuration & install vyron-hwinfo...")
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
os.set_blocking(proc.stdout.fileno(), False)

buffer = ""
full_output = []
login_sent = False
pass_sent = False
script_sent = False
start = time.time()

# Script to finish package config, deploy vyron-hwinfo, test it, and shutdown
commands = f'''
cat << 'EOF' > /tmp/finish_p3.sh
#!/bin/bash
echo "=== FINISHING DPKG AND GRUB CONFIGURATION ==="
dpkg --configure -a
update-grub

echo "=== CHECKING KERNELS IN BOOT ==="
ls -lh /boot/vmlinuz* /boot/initrd.img*

echo "=== DEPLOYING VYRON-HWINFO ==="
echo "{hwinfo_b64}" | base64 -d > /usr/local/bin/vyron-hwinfo
chmod +x /usr/local/bin/vyron-hwinfo

echo "=== EXECUTING VYRON-HWINFO CLI REPORT ==="
/usr/local/bin/vyron-hwinfo

echo "=== EXECUTING VYRON-HWINFO JSON OUTPUT ==="
/usr/local/bin/vyron-hwinfo --json

echo "=== TESTING NMCLI NETWORK STATUS ==="
nmcli device status
nmcli connection show
nmcli device wifi list || true

echo "=== PING CONNECTIVITY CHECK ==="
ping -c 2 1.1.1.1
ping -c 2 debian.org

echo "=== FINISHED SUCCESSFULLY ==="
sync
poweroff
EOF
chmod +x /tmp/finish_p3.sh
sudo bash /tmp/finish_p3.sh
'''

try:
    while time.time() - start < 480:
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
                print("\n>>> Logged in. Dispatching kernel finish & vyron-hwinfo script...")
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

print("\n>>> Finish kernel & hwinfo run completed.")
