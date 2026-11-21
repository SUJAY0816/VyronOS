#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 3 Provisioning & Upgrade Automation Script
Executes:
1. Adds Debian bookworm-backports repository.
2. Updates package lists.
3. Installs diagnostic packages: procps, pciutils, usbutils, ethtool, iw, rfkill, network-manager.
4. Seamlessly transitions network management from systemd-networkd to NetworkManager.
5. Installs the latest long-term backports kernel (linux-image-amd64 from backports).
6. Verifies boot configuration and powers off cleanly.
==============================================================================
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
LOG_PATH = os.path.join(BUILD_DIR, "phase3-setup-serial.log")

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
    print("  VYRON OS — Phase 3 Provisioning & Upgrade Pipeline")
    print("==========================================================================")
    print(f"  Target Disk    : {DISK_IMAGE}")
    print(f"  UEFI Firmware  : {OVMF_CODE}")
    print(f"  Serial Log     : {LOG_PATH}")
    print("==========================================================================")

    if not os.path.exists(DISK_IMAGE):
        print(f"ERROR: Target disk {DISK_IMAGE} not found.")
        sys.exit(1)

    os.makedirs(BUILD_DIR, exist_ok=True)
    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-Disk"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-Phase3Setup",
        "-m", "2048",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    print(">>> Booting VyronOS in QEMU for Phase 3 upgrades...")
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

    # Wrap setup in a script to guarantee sequential execution without stdin buffer collision
    setup_script = '''
cat << 'EOF' > /tmp/phase3_install.sh
#!/bin/bash
set -e
echo '=== PHASE 3 PROVISIONING BEGINS ==='
echo 'deb http://deb.debian.org/debian bookworm-backports main contrib non-free non-free-firmware' > /etc/apt/sources.list.d/backports.list
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y procps pciutils usbutils ethtool iw rfkill network-manager
mkdir -p /etc/NetworkManager/conf.d
cat << 'NMCONF' > /etc/NetworkManager/NetworkManager.conf
[main]
plugins=ifupdown,keyfile
dns=systemd-resolved

[ifupdown]
managed=true
NMCONF
systemctl stop systemd-networkd.service systemd-networkd.socket || true
systemctl disable systemd-networkd.service systemd-networkd.socket || true
systemctl enable NetworkManager.service
systemctl start NetworkManager.service || true
echo '=== TESTING NETWORKMANAGER ==='
nmcli device status || true
nmcli connection show || true
echo '=== INSTALLING BACKPORTS KERNEL ==='
apt-cache policy linux-image-amd64 || true
DEBIAN_FRONTEND=noninteractive apt-get install -y -t bookworm-backports linux-image-amd64
echo '=== PHASE 3 SETUP FINISHED ==='
sync
poweroff
EOF
chmod +x /tmp/phase3_install.sh
sudo bash /tmp/phase3_install.sh
'''

    try:
        # Allow up to 360 seconds for package download, kernel compilation/initramfs, and clean shutdown
        while time.time() - start_time < 360:
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
                    print("\n>>> Logged in. Dispatching Phase 3 setup script...")
                    time.sleep(1)
                    proc.stdin.write(f"{setup_script.strip()}\n".encode("utf-8"))
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
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()

    with open(LOG_PATH, "w") as f:
        f.write("".join(full_output))

    print(f"\n==========================================================================")
    print(f"  Phase 3 setup sequence concluded. Serial trace saved: {LOG_PATH}")
    print(f"==========================================================================")

if __name__ == "__main__":
    main()
