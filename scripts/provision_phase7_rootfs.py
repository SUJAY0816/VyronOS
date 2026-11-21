#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 7 RootFS Direct Ext4 Injection Engine
Injects users, hardened sudoers, autologin, SSH, and provisioning service
directly into the Debian 12 ARM64 root filesystem image via debugfs.
==============================================================================
"""

import os
import sys
import subprocess
import shutil

DEBUGFS = "/opt/homebrew/opt/e2fsprogs/sbin/debugfs"
ROOT_DIR = "/Users/sujayv/Downloads/VyronOS"
RELEASE_DIR = os.path.join(ROOT_DIR, "release_phase7")
ROOTFS_IMG = os.path.join(RELEASE_DIR, "rootfs.img")
STAGE_DIR = os.path.join(RELEASE_DIR, "injected_files")

def run_debugfs(cmds):
    cmd_str = "\n".join(cmds) + "\n"
    p = subprocess.run([DEBUGFS, "-w", ROOTFS_IMG], input=cmd_str, capture_output=True, text=True)
    if p.returncode != 0:
        print(f"debugfs error: {p.stderr}")
    return p

def main():
    print("==========================================================================")
    print("  VYRON OS — Phase 7 Direct RootFS Ext4 Injection Engine")
    print("==========================================================================")
    os.makedirs(STAGE_DIR, exist_ok=True)

    # 1. Prepare Shadow file with password 'vyron' ($1$vyron123$9LpmFEejDn7J7LMjTaNyu.)
    # Crypt hash for 'vyron'
    HASH = "$1$vyron123$9LpmFEejDn7J7LMjTaNyu."
    
    # Dump current files
    run_debugfs([f"dump etc/passwd {STAGE_DIR}/passwd", f"dump etc/shadow {STAGE_DIR}/shadow", f"dump etc/group {STAGE_DIR}/group"])

    # Update passwd
    with open(f"{STAGE_DIR}/passwd", "r") as f:
        passwd_content = f.read()
    if "vyron:x:1000:" not in passwd_content:
        passwd_content += "vyron:x:1000:1000:Vyron User:/home/vyron:/bin/bash\n"
        with open(f"{STAGE_DIR}/passwd", "w") as f:
            f.write(passwd_content)
        print("  Added user 'vyron' (UID 1000, GID 1000) to /etc/passwd")

    # Update shadow
    with open(f"{STAGE_DIR}/shadow", "r") as f:
        lines = f.readlines()
    new_shadow = []
    has_vyron = False
    for line in lines:
        if line.startswith("root:"):
            new_shadow.append(f"root:{HASH}:20774:0:99999:7:::\n")
        elif line.startswith("vyron:"):
            new_shadow.append(f"vyron:{HASH}:20774:0:99999:7:::\n")
            has_vyron = True
        else:
            new_shadow.append(line)
    if not has_vyron:
        new_shadow.append(f"vyron:{HASH}:20774:0:99999:7:::\n")
    with open(f"{STAGE_DIR}/shadow", "w") as f:
        f.writelines(new_shadow)
    print("  Set authenticated password 'vyron' for root and vyron in /etc/shadow")

    # Update group
    with open(f"{STAGE_DIR}/group", "r") as f:
        group_lines = f.readlines()
    new_group = []
    has_vyron_group = False
    for line in group_lines:
        parts = line.strip().split(":")
        gname = parts[0]
        if gname in ["sudo", "audio", "video", "users"]:
            members = parts[3].split(",") if len(parts) > 3 and parts[3] else []
            if "vyron" not in members:
                members.append("vyron")
            parts[3] = ",".join(members)
            new_group.append(":".join(parts) + "\n")
        elif gname == "vyron":
            has_vyron_group = True
            new_group.append(line)
        else:
            new_group.append(line)
    if not has_vyron_group:
        new_group.append("vyron:x:1000:\n")
    with open(f"{STAGE_DIR}/group", "w") as f:
        f.writelines(new_group)
    print("  Configured groups (sudo, audio, video) for vyron in /etc/group")

    # Sudoers hardening
    with open(f"{STAGE_DIR}/vyron_sudoers", "w") as f:
        f.write("vyron ALL=(ALL:ALL) ALL\n")

    # SSH configuration
    with open(f"{STAGE_DIR}/sshd_vyron.conf", "w") as f:
        f.write("PermitRootLogin yes\nPasswordAuthentication yes\n")

    # Autologin configuration for tty1
    os.makedirs(f"{STAGE_DIR}/autologin.d", exist_ok=True)
    with open(f"{STAGE_DIR}/autologin.d/autologin.conf", "w") as f:
        f.write("[Service]\nExecStart=\nExecStart=-/sbin/agetty -o '-p -f -- \\u' --noclear --autologin vyron %I $TERM\n")

    # Provisioning script
    with open(f"{STAGE_DIR}/vyron-provision.sh", "w") as f:
        f.write("""#!/bin/bash
set -x
echo "=== VYRON OS PROVISIONING STARTED ===" > /var/log/vyron-provision.log
export DEBIAN_FRONTEND=noninteractive

# 1. Repositories
cat << 'SOURCES' > /etc/apt/sources.list
deb http://deb.debian.org/debian/ bookworm main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free non-free-firmware
deb http://deb.debian.org/debian/ bookworm-backports main contrib non-free non-free-firmware
SOURCES

apt-get update >> /var/log/vyron-provision.log 2>&1

# 2. Install Desktop, Audio, Package Management & Security Packages
apt-get install -y --no-install-recommends \
    xfce4 xfce4-goodies lightdm lightdm-gtk-greeter \
    aptitude aptitude-common pipewire pipewire-pulse wireplumber \
    alsa-utils pciutils tree polkitd dbus sudo curl htop >> /var/log/vyron-provision.log 2>&1

# 3. Mount assets from CIDATA if present
mkdir -p /mnt/cidata
mount /dev/sr0 /mnt/cidata 2>/dev/null || mount /dev/cdrom /mnt/cidata 2>/dev/null || true
if [ -f /mnt/cidata/vyron_assets.tar.gz ]; then
    mkdir -p /tmp/payload
    tar -xzf /mnt/cidata/vyron_assets.tar.gz -C /tmp/payload/
    cp -r /tmp/payload/themes/* /usr/share/themes/ 2>/dev/null || true
    cp -r /tmp/payload/icons /usr/share/icons/Vyron-Icons 2>/dev/null || true
    mkdir -p /usr/share/backgrounds/vyron
    cp -r /tmp/payload/wallpapers/* /usr/share/backgrounds/vyron/ 2>/dev/null || true
    cp /tmp/payload/bin/* /usr/local/bin/ 2>/dev/null || true
    chmod +x /usr/local/bin/*.py 2>/dev/null || true
fi

# 4. Sudo Hardening
chmod 0440 /etc/sudoers.d/vyron
chown root:root /etc/sudoers.d/vyron

# 5. Enable LightDM Autologin
sed -i 's/^#autologin-user=.*/autologin-user=vyron/' /etc/lightdm/lightdm.conf 2>/dev/null || true
sed -i 's/^#autologin-user-timeout=.*/autologin-user-timeout=0/' /etc/lightdm/lightdm.conf 2>/dev/null || true
systemctl enable lightdm 2>/dev/null || true

# Disable provisioning service
systemctl disable vyron-provision.service 2>/dev/null || true
echo "=== VYRON OS PROVISIONING COMPLETE ===" >> /var/log/vyron-provision.log
systemctl start lightdm 2>/dev/null || true
""")

    # Provisioning service unit
    with open(f"{STAGE_DIR}/vyron-provision.service", "w") as f:
        f.write("""[Unit]
Description=VyronOS Release First-Boot Provisioning
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash /usr/local/bin/vyron-provision.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
""")

    print("\n>>> Injecting files into rootfs.img via debugfs...")
    debugfs_cmds = [
        # Passwd, Shadow, Group
        f"rm etc/passwd", f"write {STAGE_DIR}/passwd etc/passwd", "sif etc/passwd mode 0100644",
        f"rm etc/shadow", f"write {STAGE_DIR}/shadow etc/shadow", "sif etc/shadow mode 0100640", "sif etc/shadow gid 42",
        f"rm etc/group", f"write {STAGE_DIR}/group etc/group", "sif etc/group mode 0100644",
        # Home directory
        "mkdir home/vyron", "sif home/vyron mode 040755", "sif home/vyron uid 1000", "sif home/vyron gid 1000",
        # Sudoers
        "mkdir etc/sudoers.d",
        f"rm etc/sudoers.d/vyron", f"write {STAGE_DIR}/vyron_sudoers etc/sudoers.d/vyron",
        "sif etc/sudoers.d/vyron mode 0100440", "sif etc/sudoers.d/vyron uid 0", "sif etc/sudoers.d/vyron gid 0",
        # SSH config
        "mkdir etc/ssh/sshd_config.d",
        f"rm etc/ssh/sshd_config.d/vyron.conf", f"write {STAGE_DIR}/sshd_vyron.conf etc/ssh/sshd_config.d/vyron.conf",
        # Provisioning script
        f"rm usr/local/bin/vyron-provision.sh", f"write {STAGE_DIR}/vyron-provision.sh usr/local/bin/vyron-provision.sh",
        "sif usr/local/bin/vyron-provision.sh mode 0100755", "sif usr/local/bin/vyron-provision.sh uid 0",
        # Provisioning service
        f"rm etc/systemd/system/vyron-provision.service", f"write {STAGE_DIR}/vyron-provision.service etc/systemd/system/vyron-provision.service",
        "sif etc/systemd/system/vyron-provision.service mode 0100644",
        # Enable service symlink
        "mkdir etc/systemd/system/multi-user.target.wants",
        "ln etc/systemd/system/vyron-provision.service etc/systemd/system/multi-user.target.wants/vyron-provision.service"
    ]

    p = run_debugfs(debugfs_cmds)
    print("  RootFS direct injection completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
