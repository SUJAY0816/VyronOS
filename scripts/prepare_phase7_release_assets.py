#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 7 Asset Packager and Cloud-Init Seed Generator
Prepares the complete self-contained asset tarball and cloud-init seed ISO
for the automated Debian 12 Bookworm ARM64 VirtualBox provisioning.
==============================================================================
"""

import os
import sys
import shutil
import tarfile
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
RELEASE_DIR = os.path.join(ROOT_DIR, "release_phase7")
CIDATA_DIR = os.path.join(RELEASE_DIR, "cidata")
PAYLOAD_DIR = os.path.join(CIDATA_DIR, "payload")

def main():
    print("==========================================================================")
    print("  VYRON OS — Phase 7 Asset Packaging & Cloud-Init Staging")
    print("==========================================================================")
    os.makedirs(PAYLOAD_DIR, exist_ok=True)

    # 1. Stage Themes
    dest_themes = os.path.join(PAYLOAD_DIR, "themes")
    os.makedirs(dest_themes, exist_ok=True)
    for t in ["Vyron-V2-Dark", "Vyron-V2-Light"]:
        src = os.path.join(ROOT_DIR, "themes", t)
        if os.path.exists(src):
            dst = os.path.join(dest_themes, t)
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)
            print(f"  Staged Theme: {t}")

    # 2. Stage Icons
    dest_icons = os.path.join(PAYLOAD_DIR, "icons")
    os.makedirs(dest_icons, exist_ok=True)
    src_icons = os.path.join(ROOT_DIR, "assets", "icons")
    if os.path.exists(src_icons):
        for f in os.listdir(src_icons):
            if f.endswith((".svg", ".png")):
                shutil.copy2(os.path.join(src_icons, f), dest_icons)
        print(f"  Staged Icons ({len(os.listdir(dest_icons))} icons)")

    # 3. Stage Wallpapers
    dest_wallpapers = os.path.join(PAYLOAD_DIR, "wallpapers")
    os.makedirs(dest_wallpapers, exist_ok=True)
    src_wallpapers = os.path.join(ROOT_DIR, "assets", "wallpapers")
    if os.path.exists(src_wallpapers):
        for f in os.listdir(src_wallpapers):
            if f.endswith((".png", ".jpg")):
                shutil.copy2(os.path.join(src_wallpapers, f), dest_wallpapers)
        print(f"  Staged Wallpapers ({len(os.listdir(dest_wallpapers))} files)")

    # 4. Stage Custom Utilities
    dest_bin = os.path.join(PAYLOAD_DIR, "bin")
    os.makedirs(dest_bin, exist_ok=True)
    for s in ["vyron_theme.py", "vyron_sysmon.py", "test_phase6_security_and_services.py"]:
        src = os.path.join(SCRIPT_DIR, s)
        if os.path.exists(src):
            shutil.copy2(src, dest_bin)
            print(f"  Staged Utility: {s}")

    # 5. Create Compressed Tarball
    tar_path = os.path.join(CIDATA_DIR, "vyron_assets.tar.gz")
    print(f"\n>>> Creating payload archive: {tar_path}...")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(PAYLOAD_DIR, arcname=".")
    print(f"  Archive created ({os.path.getsize(tar_path) / (1024*1024):.2f} MB)")

    # 6. Write Cloud-Init meta-data
    with open(os.path.join(CIDATA_DIR, "meta-data"), "w") as f:
        f.write("instance-id: vyron-os-release-v1\nlocal-hostname: vyron-os\n")

    # 7. Write Cloud-Init user-data
    user_data = """#cloud-config
ssh_pwauth: true
disable_root: false
chpasswd:
  list: |
    root:vyron
    vyron:vyron
  expire: false
users:
  - name: vyron
    gecos: "Vyron User"
    primary_group: vyron
    groups: sudo, audio, video
    shell: /bin/bash
    sudo: "ALL=(ALL:ALL) ALL"
    lock_passwd: false

write_files:
  - path: /etc/sudoers.d/vyron
    permissions: "0440"
    owner: "root:root"
    content: |
      vyron ALL=(ALL:ALL) ALL

runcmd:
  - echo "==========================================================" >> /var/log/vyron-install.log
  - echo "  VYRON OS Phase 7 Automated Provisioning Starting...     " >> /var/log/vyron-install.log
  - echo "==========================================================" >> /var/log/vyron-install.log
  - export DEBIAN_FRONTEND=noninteractive
  - apt-get update >> /var/log/vyron-install.log 2>&1
  - apt-get install -y --no-install-recommends xfce4 xfce4-goodies lightdm lightdm-gtk-greeter aptitude pipewire pipewire-pulse wireplumber alsa-utils pciutils tree polkitd dbus sudo curl htop >> /var/log/vyron-install.log 2>&1
  - mkdir -p /mnt/cidata && mount /dev/sr0 /mnt/cidata 2>/dev/null || mount /dev/cdrom /mnt/cidata 2>/dev/null || true
  - tar -xzf /mnt/cidata/vyron_assets.tar.gz -C /tmp/vyron_payload/ 2>/dev/null || true
  - cp -r /tmp/vyron_payload/themes/* /usr/share/themes/ 2>/dev/null || true
  - cp -r /tmp/vyron_payload/icons /usr/share/icons/Vyron-Icons 2>/dev/null || true
  - mkdir -p /usr/share/backgrounds/vyron && cp -r /tmp/vyron_payload/wallpapers/* /usr/share/backgrounds/vyron/ 2>/dev/null || true
  - cp /tmp/vyron_payload/bin/* /usr/local/bin/ 2>/dev/null || true
  - chmod +x /usr/local/bin/*.py 2>/dev/null || true
  - sed -i 's/^#autologin-user=.*/autologin-user=vyron/' /etc/lightdm/lightdm.conf 2>/dev/null || true
  - sed -i 's/^#autologin-user-timeout=.*/autologin-user-timeout=0/' /etc/lightdm/lightdm.conf 2>/dev/null || true
  - chmod 0440 /etc/sudoers.d/vyron
  - chown root:root /etc/sudoers.d/vyron
  - systemctl enable lightdm
  - systemctl start lightdm || true
  - echo "VYRON OS Phase 7 Provisioning Complete" >> /var/log/vyron-install.log
"""
    with open(os.path.join(CIDATA_DIR, "user-data"), "w") as f:
        f.write(user_data)

    print("  Cloud-init meta-data and user-data generated.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
