#!/bin/bash
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
apt-get install -y --no-install-recommends \
    xfce4 xfce4-goodies lightdm lightdm-gtk-greeter \
    xserver-xorg xserver-xorg-input-libinput xserver-xorg-video-all \
    virtualbox-guest-utils virtualbox-guest-x11 \
    firefox-esr thunar xfce4-terminal xfce4-taskmanager \
    htop tree pciutils curl wget aptitude \
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
