#!/usr/bin/env python3
"""
VYRON OS — Phase 6 Baseline System Audit
Inspects current package management, audio configuration, sudoers setup,
and user privilege separation on dist/VyronOS-Disk-Phase6-Working.qcow2.
"""

import os
import sys
import time
import subprocess
import select

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
WORKING_DISK = os.path.join(DIST_DIR, "VyronOS-Disk-Phase6-Working.qcow2")
LOG_PATH = os.path.join(BUILD_DIR, "phase6-baseline-audit.log")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"

cmd = [
    "/opt/homebrew/bin/qemu-system-x86_64",
    "-name", "VyronOS-P6Audit",
    "-m", "2048",
    "-smp", "2",
    "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
    "-drive", f"file={WORKING_DISK},format=qcow2,file.locking=off",
    "-netdev", "user,id=net0,hostname=vyron-os",
    "-device", "virtio-net-pci,netdev=net0",
    "-device", "intel-hda",
    "-device", "hda-duplex",
    "-display", "none",
    "-serial", "stdio"
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
os.set_blocking(proc.stdout.fileno(), False)

buffer = ""
full_output = []
start_time = time.time()
login_sent = False
pass_sent = False
audit_sent = False

audit_script = """
cat << 'AUDIT_END' > /tmp/run_audit.sh
#!/bin/bash
echo "=== 1. KERNEL & SYSTEMD ==="
uname -a
systemctl is-system-running || true

echo "=== 2. CURRENT SUDOERS & PRIVILEGES ==="
id
ls -la /etc/sudoers /etc/sudoers.d/
cat /etc/sudoers.d/* 2>/dev/null || true

echo "=== 3. AUDIO SUBSYSTEM BASELINE ==="
cat /proc/asound/cards 2>/dev/null || echo "NO_ASOUND_CARDS"
which aplay amixer pactl pipewire wireplumber 2>/dev/null || true
lspci -nnk | grep -A 3 -i audio || echo "NO_PCI_AUDIO_DETECTED"

echo "=== 4. PACKAGE MANAGEMENT BASELINE ==="
dpkg --version | head -n 1
apt-get --version | head -n 1
which aptitude || echo "APTITUDE_NOT_INSTALLED"
cat /etc/apt/sources.list

echo "=== 5. BASELINE AUDIT COMPLETE ==="
sync
sudo poweroff
AUDIT_END
chmod +x /tmp/run_audit.sh
bash /tmp/run_audit.sh
"""

while time.time() - start_time < 120:
    r, _, _ = select.select([proc.stdout.fileno()], [], [], 0.1)
    if r:
        chunk = os.read(proc.stdout.fileno(), 4096).decode("utf-8", errors="replace")
        if not chunk:
            if proc.poll() is not None:
                break
            time.sleep(0.05)
            continue
        buffer += chunk
        full_output.append(chunk)

        if ("login:" in buffer or "vyron-os login:" in buffer) and not login_sent:
            proc.stdin.write(b"vyron\n")
            proc.stdin.flush()
            login_sent = True
            buffer = ""
        elif ("Password:" in buffer or "password:" in buffer) and login_sent and not pass_sent:
            proc.stdin.write(b"vyron\n")
            proc.stdin.flush()
            pass_sent = True
            buffer = ""
        elif ("vyron@vyron-os:" in buffer or "$" in buffer) and pass_sent and not audit_sent:
            audit_sent = True
            buffer = ""
            time.sleep(0.5)
            proc.stdin.write(audit_script.encode("utf-8"))
            proc.stdin.flush()

proc.wait(timeout=20)
with open(LOG_PATH, "w") as f:
    f.write("".join(full_output))

print("Baseline audit completed. Saved to:", LOG_PATH)
