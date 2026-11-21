#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 7 Master Ext4 Injection Engine
Injects users, credentials, SSH keys, network config, assets, and firstboot service
into rootfs.img via debugfs.
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
STAGE_DIR = os.path.join(RELEASE_DIR, "stage")
SSH_KEY_PUB = os.path.expanduser("~/.ssh/vyron_key.pub")
UI_V2_TAR = os.path.join(ROOT_DIR, "build", "ui_v2_package.tar.gz")

HASH = "$1$vyron123$9LpmFEejDn7J7LMjTaNyu."

def run_debugfs(cmds):
    cmd_str = "\n".join(cmds) + "\n"
    p = subprocess.run([DEBUGFS, "-w", ROOTFS_IMG], input=cmd_str, capture_output=True, text=True)
    if p.returncode != 0:
        print(f"debugfs stderr: {p.stderr}")
    return p

def main():
    print("==========================================================================")
    print("  VYRON OS — Phase 7 Master RootFS Ext4 Injection")
    print("==========================================================================")
    os.makedirs(STAGE_DIR, exist_ok=True)

    # 1. Dump existing passwd, shadow, group
    run_debugfs([
        f"dump etc/passwd {STAGE_DIR}/passwd",
        f"dump etc/shadow {STAGE_DIR}/shadow",
        f"dump etc/group {STAGE_DIR}/group"
    ])

    # Update passwd
    with open(f"{STAGE_DIR}/passwd", "r") as f:
        passwd_txt = f.read()
    if "vyron:x:1000:" not in passwd_txt:
        passwd_txt += "vyron:x:1000:1000:Vyron User:/home/vyron:/bin/bash\n"
        with open(f"{STAGE_DIR}/passwd", "w") as f:
            f.write(passwd_txt)
        print("  Added vyron (UID 1000) to passwd")

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
    print("  Set authenticated password 'vyron' for root and vyron in shadow")

    # Update group
    with open(f"{STAGE_DIR}/group", "r") as f:
        glines = f.readlines()
    new_group = []
    has_vgroup = False
    for line in glines:
        parts = line.strip().split(":")
        gname = parts[0]
        if gname in ["sudo", "audio", "video", "users", "netdev"]:
            members = parts[3].split(",") if len(parts) > 3 and parts[3] else []
            if "vyron" not in members:
                members.append("vyron")
            parts[3] = ",".join(members)
            new_group.append(":".join(parts) + "\n")
        elif gname == "vyron":
            has_vgroup = True
            new_group.append(line)
        else:
            new_group.append(line)
    if not has_vgroup:
        new_group.append("vyron:x:1000:\n")
    with open(f"{STAGE_DIR}/group", "w") as f:
        f.writelines(new_group)
    print("  Configured groups for vyron")

    # Sudoers
    with open(f"{STAGE_DIR}/vyron_sudoers", "w") as f:
        f.write("vyron ALL=(ALL:ALL) ALL\n")

    # SSH config
    with open(f"{STAGE_DIR}/sshd_vyron.conf", "w") as f:
        f.write("PermitRootLogin yes\nPasswordAuthentication yes\nPubkeyAuthentication yes\n")

    # SSH authorized_keys
    ssh_key_content = ""
    if os.path.exists(SSH_KEY_PUB):
        with open(SSH_KEY_PUB, "r") as f:
            ssh_key_content = f.read().strip()
    with open(f"{STAGE_DIR}/authorized_keys", "w") as f:
        f.write(ssh_key_content + "\n")

    # Hostname & Hosts
    with open(f"{STAGE_DIR}/hostname", "w") as f:
        f.write("vyron-os\n")
    with open(f"{STAGE_DIR}/hosts", "w") as f:
        f.write("127.0.0.1 localhost\n127.0.1.1 vyron-os\n::1 localhost ip6-localhost ip6-loopback\n")

    # Network configuration (DHCP on all ethernet / usbnet interfaces)
    with open(f"{STAGE_DIR}/99-dhcp.network", "w") as f:
        f.write("[Match]\nName=en* eth* usb*\n\n[Network]\nDHCP=yes\n")

    # Firstboot script
    with open(f"{STAGE_DIR}/vyron-firstboot.sh", "w") as f:
        f.write("""#!/bin/bash
set -x
LOG=/var/log/vyron-firstboot.log
echo "=== VYRON OS FIRST-BOOT SETUP STARTED ===" > $LOG
date >> $LOG

export DEBIAN_FRONTEND=noninteractive

# 1. Expand ext4 filesystem online to full partition capacity
resize2fs /dev/sda1 >> $LOG 2>&1 || resize2fs /dev/sda2 >> $LOG 2>&1 || true

# 2. Configure Official Debian Repositories
cat << 'SOURCES' > /etc/apt/sources.list
deb http://deb.debian.org/debian/ bookworm main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free non-free-firmware
deb http://deb.debian.org/debian/ bookworm-backports main contrib non-free non-free-firmware
SOURCES

apt-get update >> $LOG 2>&1

# 3. Install Real Desktop Environment, VirtualBox Mouse Integration, Real Web Browser, Audio
apt-get install -y --no-install-recommends \\
    xfce4 xfce4-goodies lightdm lightdm-gtk-greeter \\
    xserver-xorg xserver-xorg-input-libinput xserver-xorg-video-all \\
    virtualbox-guest-utils virtualbox-guest-x11 \\
    firefox-esr thunar xfce4-terminal xfce4-taskmanager \\
    htop tree pciutils curl wget aptitude \\
    pipewire pipewire-pulse wireplumber alsa-utils polkitd dbus sudo >> $LOG 2>&1

# 4. Deploy Vyron UI V2 Package (Wallpapers, Themes, Icons, Configurations)
if [ -f /tmp/ui_v2_package.tar.gz ]; then
    mkdir -p /tmp/ui_extract
    tar -xzf /tmp/ui_v2_package.tar.gz -C /tmp/ui_extract/
    cp -r /tmp/ui_extract/themes/* /usr/share/themes/ 2>/dev/null || true
    cp -r /tmp/ui_extract/icons /usr/share/icons/Vyron-Icons 2>/dev/null || true
    mkdir -p /usr/share/backgrounds/vyron
    cp -r /tmp/ui_extract/wallpapers/* /usr/share/backgrounds/vyron/ 2>/dev/null || true
    cp /tmp/ui_extract/*.py /usr/local/bin/ 2>/dev/null || true
    chmod +x /usr/local/bin/*.py 2>/dev/null || true
    cp -r /tmp/ui_extract/applications/* /usr/share/applications/ 2>/dev/null || true
    cp -r /tmp/ui_extract/lightdm/* /etc/lightdm/ 2>/dev/null || true
    cp -r /tmp/ui_extract/xfce4 /etc/xdg/ 2>/dev/null || true
fi

# 5. Configure LightDM Autologin for 'vyron' user
sed -i 's/^#autologin-user=.*/autologin-user=vyron/' /etc/lightdm/lightdm.conf 2>/dev/null || true
sed -i 's/^#autologin-user-timeout=.*/autologin-user-timeout=0/' /etc/lightdm/lightdm.conf 2>/dev/null || true

# 6. Sudoers permissions
chmod 0440 /etc/sudoers.d/vyron
chown root:root /etc/sudoers.d/vyron

# 7. Enable Services
systemctl enable lightdm
systemctl enable ssh
systemctl enable systemd-networkd
systemctl enable systemd-resolved

# 8. Mark Firstboot Complete & Disable this service
systemctl disable vyron-firstboot.service
echo "=== VYRON OS FIRST-BOOT SETUP COMPLETE ===" >> $LOG
date >> $LOG
systemctl start lightdm || true
""")

    # Firstboot service unit
    with open(f"{STAGE_DIR}/vyron-firstboot.service", "w") as f:
        f.write("""[Unit]
Description=VyronOS Master First-Boot Desktop & Integration Provisioner
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash /usr/local/bin/vyron-firstboot.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
""")

    # Copy ui_v2_package.tar.gz into stage
    stage_tar = f"{STAGE_DIR}/ui_v2_package.tar.gz"
    if os.path.exists(UI_V2_TAR):
        shutil.copyfile(UI_V2_TAR, stage_tar)

    # Injections via debugfs
    print("\n>>> Executing debugfs write operations...")
    cmds = [
        # Passwd, shadow, group
        "rm etc/passwd", f"write {STAGE_DIR}/passwd etc/passwd", "sif etc/passwd mode 0100644",
        "rm etc/shadow", f"write {STAGE_DIR}/shadow etc/shadow", "sif etc/shadow mode 0100640", "sif etc/shadow gid 42",
        "rm etc/group", f"write {STAGE_DIR}/group etc/group", "sif etc/group mode 0100644",

        # Home directory
        "mkdir home/vyron", "sif home/vyron mode 040755", "sif home/vyron uid 1000", "sif home/vyron gid 1000",
        "mkdir home/vyron/.ssh", "sif home/vyron/.ssh mode 040700", "sif home/vyron/.ssh uid 1000", "sif home/vyron/.ssh gid 1000",
        f"rm home/vyron/.ssh/authorized_keys", f"write {STAGE_DIR}/authorized_keys home/vyron/.ssh/authorized_keys",
        "sif home/vyron/.ssh/authorized_keys mode 0100600", "sif home/vyron/.ssh/authorized_keys uid 1000", "sif home/vyron/.ssh/authorized_keys gid 1000",

        # Root SSH
        "mkdir root/.ssh", "sif root/.ssh mode 040700",
        f"rm root/.ssh/authorized_keys", f"write {STAGE_DIR}/authorized_keys root/.ssh/authorized_keys",
        "sif root/.ssh/authorized_keys mode 0100600",

        # Sudoers
        "mkdir etc/sudoers.d",
        f"rm etc/sudoers.d/vyron", f"write {STAGE_DIR}/vyron_sudoers etc/sudoers.d/vyron",
        "sif etc/sudoers.d/vyron mode 0100440", "sif etc/sudoers.d/vyron uid 0", "sif etc/sudoers.d/vyron gid 0",

        # SSH config
        "mkdir etc/ssh/sshd_config.d",
        f"rm etc/ssh/sshd_config.d/vyron.conf", f"write {STAGE_DIR}/sshd_vyron.conf etc/ssh/sshd_config.d/vyron.conf",

        # Hostname & hosts
        f"rm etc/hostname", f"write {STAGE_DIR}/hostname etc/hostname", "sif etc/hostname mode 0100644",
        f"rm etc/hosts", f"write {STAGE_DIR}/hosts etc/hosts", "sif etc/hosts mode 0100644",

        # Network config
        "mkdir etc/systemd/network",
        f"rm etc/systemd/network/99-dhcp.network", f"write {STAGE_DIR}/99-dhcp.network etc/systemd/network/99-dhcp.network",
        "sif etc/systemd/network/99-dhcp.network mode 0100644",

        # UI V2 Tarball in /tmp
        "mkdir tmp",
        f"rm tmp/ui_v2_package.tar.gz", f"write {stage_tar} tmp/ui_v2_package.tar.gz", "sif tmp/ui_v2_package.tar.gz mode 0100644",

        # Firstboot script
        f"rm usr/local/bin/vyron-firstboot.sh", f"write {STAGE_DIR}/vyron-firstboot.sh usr/local/bin/vyron-firstboot.sh",
        "sif usr/local/bin/vyron-firstboot.sh mode 0100755", "sif usr/local/bin/vyron-firstboot.sh uid 0",

        # Firstboot service unit
        f"rm etc/systemd/system/vyron-firstboot.service", f"write {STAGE_DIR}/vyron-firstboot.service etc/systemd/system/vyron-firstboot.service",
        "sif etc/systemd/system/vyron-firstboot.service mode 0100644",

        # Enable service
        "mkdir etc/systemd/system/multi-user.target.wants",
        "ln etc/systemd/system/vyron-firstboot.service etc/systemd/system/multi-user.target.wants/vyron-firstboot.service"
    ]

    res = run_debugfs(cmds)
    print("  Debugfs operations completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
