#!/usr/bin/env python3
"""
Step 1: Extract exact deb URIs from guest package manager.
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
DISK_IMAGE = os.path.join(DIST_DIR, "VyronOS-Disk.qcow2")
URIS_FILE = os.path.join(BUILD_DIR, "debs_uris.txt")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"

def main():
    os.makedirs(BUILD_DIR, exist_ok=True)
    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-UriExtract"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-UriExtract",
        "-m", "2048",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
    os.set_blocking(proc.stdout.fileno(), False)

    full_output = []
    buffer = ""
    start_time = time.time()
    login_user_sent = False
    login_pass_sent = False
    commands_sent = False

    test_commands = '''
cat << 'EOF' > /tmp/get_uris.sh
#!/bin/bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
echo "=== BEGIN_DEB_URIS ==="
apt-get --print-uris --yes install --no-install-recommends \
    xserver-xorg-core \
    xserver-xorg-video-all \
    xserver-xorg-input-all \
    xinit \
    x11-xserver-utils \
    lightdm \
    lightdm-gtk-greeter \
    xfce4-session \
    xfwm4 \
    xfce4-panel \
    xfdesktop4 \
    xfce4-settings \
    xfce4-terminal \
    thunar \
    xfce4-whiskermenu-plugin \
    greybird-gtk-theme \
    adwaita-icon-theme \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    libglib2.0-bin \
    xdotool \
    xterm \
    dbus-x11
echo "=== END_DEB_URIS ==="
sync
sudo poweroff
EOF
chmod +x /tmp/get_uris.sh
bash /tmp/get_uris.sh
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
                    time.sleep(0.5)
                    proc.stdin.write(f"{test_commands.strip()}\n".encode("utf-8"))
                    proc.stdin.flush()

                if "Powering off" in buffer or "reboot: Power down" in buffer or "ACPI: PM: Preparing to enter system sleep state S5" in buffer:
                    break
            else:
                if proc.poll() is not None:
                    break
    finally:
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()

    out_text = "".join(full_output)
    if "=== BEGIN_DEB_URIS ===" in out_text and "=== END_DEB_URIS ===" in out_text:
        part = out_text.split("=== BEGIN_DEB_URIS ===")[1].split("=== END_DEB_URIS ===")[0]
        uris = [line.strip() for line in part.splitlines() if line.strip().startswith("'http")]
        with open(URIS_FILE, "w") as f:
            f.write("\n".join(uris))
        print(f"Extracted {len(uris)} package URIs to {URIS_FILE}")
        sys.exit(0)
    else:
        print("Failed to extract URIs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
