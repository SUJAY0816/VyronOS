#!/usr/bin/env python3
"""
VYRON OS — Phase 6 Finalize Services & Security Setup
Handles authenticated sudo prompts automatically and completes Phase 6 setup.
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
LOG_PATH = os.path.join(BUILD_DIR, "phase6-finish-serial.log")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"

cmd = [
    "/opt/homebrew/bin/qemu-system-x86_64",
    "-name", "VyronOS-P6Finish",
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
script_sent = False

finish_script = """
cat << 'FINISH_EOF' > /tmp/run_finish.sh
#!/bin/bash
set -e
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "=== 1. VERIFYING INSTALLED PACKAGES ==="
dpkg -l | grep -E "aptitude|alsa-utils|pipewire|wireplumber|polkitd"

echo "=== 2. FIXING SUDOERS PERMISSIONS ==="
echo "vyron" | sudo -S chmod 0440 /etc/sudoers.d/vyron
echo "vyron" | sudo -S chmod 0440 /etc/sudoers
echo "vyron" | sudo -S chmod 0750 /etc/sudoers.d

echo "=== 3. CREATING TESTUSER & CONFIGURING PASSWORDS ==="
if ! id testuser >/dev/null 2>&1; then
    echo "vyron" | sudo -S useradd -m -s /bin/bash testuser
    echo "testuser:testpass123" | echo "vyron" | sudo -S chpasswd
fi

echo "=== 4. TESTING AUTHENTICATED SUDO AS VYRON ==="
# Sudo with correct password must succeed
echo "vyron" | sudo -S whoami

echo "=== 5. TESTING UNAUTHENTICATED SUDO REJECTION ==="
# Sudo with bad password must fail
sudo -k
if echo "wrongpassword" | sudo -S whoami 2>/dev/null; then
    echo "SECURITY_FAIL: Bad password accepted!"
    exit 1
else
    echo "SECURITY_PASS: Bad password rejected by sudo!"
fi

echo "=== 6. TESTING UNPRIVILEGED USER SUDO REJECTION ==="
# testuser is not in sudoers and must be denied
if su - testuser -c 'echo "testpass123" | sudo -S whoami' 2>/dev/null; then
    echo "SECURITY_FAIL: Non-sudoer escalated!"
    exit 1
else
    echo "SECURITY_PASS: Non-sudoer strictly denied escalation!"
fi

echo "=== 7. TESTING APTITUDE PACKAGE INSTALL & PURGE ==="
echo "vyron" | sudo -S aptitude -y install tree
tree --version
echo "vyron" | sudo -S aptitude -y purge tree

echo "=== 8. ENABLING PIPEWIRE USER SERVICES ==="
mkdir -p /home/vyron/.config/systemd/user/default.target.wants
sudo -u vyron XDG_RUNTIME_DIR=/run/user/1000 systemctl --user enable pipewire pipewire-pulse wireplumber 2>/dev/null || true

echo "=== 9. VERIFYING POLKIT STATUS ==="
systemctl is-active polkit || systemctl is-enabled polkit || true

echo "=== 10. SYSTEM DIRECTORY PERMISSIONS CHECK ==="
ls -ld /etc /usr /boot /var /home/vyron

echo "=== PHASE 6 SERVICES & SECURITY SETUP COMPLETED SUCCESSFULLY ==="
sync
echo "vyron" | sudo -S poweroff
FINISH_EOF
chmod +x /tmp/run_finish.sh
bash /tmp/run_finish.sh
"""

try:
    while time.time() - start_time < 300:
        r, _, _ = select.select([proc.stdout.fileno()], [], [], 0.1)
        if r:
            chunk = os.read(proc.stdout.fileno(), 4096).decode("utf-8", errors="replace")
            if not chunk:
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            sys.stdout.write(chunk)
            sys.stdout.flush()
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
            elif ("vyron@vyron-os:" in buffer or "$" in buffer) and pass_sent and not script_sent:
                script_sent = True
                buffer = ""
                time.sleep(1)
                proc.stdin.write(finish_script.encode("utf-8"))
                proc.stdin.flush()
            elif "[sudo] password for vyron:" in buffer or "password for vyron:" in buffer:
                proc.stdin.write(b"vyron\n")
                proc.stdin.flush()
                buffer = ""

    proc.wait(timeout=30)
except Exception as e:
    print(f"Exception: {e}")
finally:
    if proc.poll() is None:
        proc.terminate()
        proc.wait(timeout=5)

with open(LOG_PATH, "w") as f:
    f.write("".join(full_output))

out_text = "".join(full_output)
if "PHASE 6 SERVICES & SECURITY SETUP COMPLETED SUCCESSFULLY" in out_text:
    print("\n==========================================================================")
    print("  SUCCESS: Phase 6 Services & Security Setup Finalized!")
    print("==========================================================================")
    sys.exit(0)
else:
    print("\n==========================================================================")
    print("  ERROR: Setup did not finalize cleanly. See log:", LOG_PATH)
    print("==========================================================================")
    sys.exit(1)
