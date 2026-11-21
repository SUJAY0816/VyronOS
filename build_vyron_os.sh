#!/usr/bin/env bash
# ==============================================================================
# VYRON Micro-OS - Master Automated ISO Generation Pipeline (M5 Edition)
# ==============================================================================
# Target Hardware: Apple Silicon M5 (ARM64 / aarch64 & UEFI Universal)
# Core Architectural Principles:
#  1. In-built Package Manager: APTITUDE (Aliased to 'apt' and 'apt-get')
#  2. Network Connectivity (WiFi & LAN via VirtIO & Broadcom)
#  3. Standard Debian POSIX Command Suite (ls, ps, pwd, df, free, cat, aptitude)
#  4. Bespoke Clean Boot Sequence & Live Minimal Console
#  5. Zero GUI Bloat (Headless / Minimal Micro-OS)
#  6. Snap Purged (Zero canonical snap daemon or store overhead)
#  7. Zstandard Level 19 SquashFS Compression + Ephemeral RAM OverlayFS
# ==============================================================================
set -euo pipefail

VYRON_VERSION="1.0-M5-LTS"
TARGET_ARCH="${1:-arm64}" # Default to Apple Silicon arm64, or pass amd64
WORK_DIR="/tmp/vyron_build_${TARGET_ARCH}"
ROOTFS="${WORK_DIR}/rootfs"
ISODIR="${WORK_DIR}/iso"
OUTPUT_ISO="Vyron-Micro-OS-${VYRON_VERSION}-${TARGET_ARCH}.iso"
DEBIAN_SUITE="bookworm"
DEBIAN_MIRROR="http://deb.debian.org/debian/"

echo "=========================================================================="
echo "  VYRON Micro-OS Master ISO Build Pipeline"
echo "  Target Architecture: ${TARGET_ARCH} (Apple Silicon M5 Target)"
echo "  Version: ${VYRON_VERSION}"
echo "=========================================================================="

# ------------------------------------------------------------------------------
# Stage 1: Clean and Prepare Workspaces
# ------------------------------------------------------------------------------
echo ">>> [1/7] Cleaning and preparing build workspaces..."
rm -rf "${WORK_DIR}"
mkdir -p "${ROOTFS}" \
         "${ISODIR}/live" \
         "${ISODIR}/boot/grub" \
         "${ISODIR}/EFI/BOOT" \
         "${ISODIR}/System/Library/CoreServices"

# ------------------------------------------------------------------------------
# Stage 2: Bootstrap Minimal Debian Rootfs (Minbase Variant)
# ------------------------------------------------------------------------------
echo ">>> [2/7] Bootstrapping Minimal Debian Rootfs (${DEBIAN_SUITE} - ${TARGET_ARCH})..."
debootstrap --arch="${TARGET_ARCH}" --variant=minbase "${DEBIAN_SUITE}" "${ROOTFS}" "${DEBIAN_MIRROR}"

# ------------------------------------------------------------------------------
# Stage 3: Chroot Provisioning & Core Components Integration
# ------------------------------------------------------------------------------
echo ">>> [3/7] Provisioning Core Services, Networking, Aptitude & Mac CLI Tools..."

cat << 'CHROOT_SCRIPT' > "${ROOTFS}/vyron_setup.sh"
#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
export HOME=/root

# --- 1. Repositories with Non-Free Firmware ---
cat << 'SOURCES' > /etc/apt/sources.list
deb http://deb.debian.org/debian/ bookworm main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free non-free-firmware
SOURCES

apt-get update

# --- 2. Install Kernel, Live-Boot & Core Micro-OS Utilities (NO GUI) ---
# Kernel selection based on architecture
ARCH=$(dpkg --print-architecture)
if [ "$ARCH" = "arm64" ]; then
    apt-get install -y --no-install-recommends linux-image-arm64
else
    apt-get install -y --no-install-recommends linux-image-amd64
fi

apt-get install -y --no-install-recommends \
    live-boot \
    systemd-sysv \
    systemd-resolved \
    dbus \
    pciutils \
    usbutils \
    kmod \
    udev \
    dialog \
    whiptail \
    sudo \
    curl \
    wget \
    htop \
    tmux \
    nano \
    file \
    bsdmainutils

# --- 3. Network Connectivity (WiFi & LAN / VirtIO) ---
apt-get install -y --no-install-recommends \
    network-manager \
    wpasupplicant \
    wireless-regdb \
    firmware-brcm80211 \
    firmware-misc-nonfree \
    ethtool \
    iproute2 \
    rfkill \
    iputils-ping \
    net-tools \
    dnsutils \
    traceroute

# Unblock boot: Mask NetworkManager-wait-online to achieve sub-1.5s boot
systemctl mask NetworkManager-wait-online.service
systemctl mask systemd-networkd-wait-online.service
systemctl enable NetworkManager.service

# --- 4. In-Built Package Manager: APTITUDE Aliased to APT ---
apt-get install -y --no-install-recommends \
    aptitude \
    aptitude-common

# System-wide Aliasing (apt, apt-get -> aptitude)
cat << 'ALIAS_SH' > /etc/profile.d/01-aptitude-alias.sh
alias apt='/usr/bin/aptitude'
alias apt-get='/usr/bin/aptitude'
export APT_CONFIG="/etc/apt/apt.conf.d/99vyron"
ALIAS_SH

echo "alias apt='/usr/bin/aptitude'" >> /etc/bash.bashrc
echo "alias apt-get='/usr/bin/aptitude'" >> /etc/bash.bashrc

# Defer APT daily background update timers to preserve DPKG lock
mkdir -p /etc/systemd/system/apt-daily.timer.d/
cat << 'APT_TIMER' > /etc/systemd/system/apt-daily.timer.d/override.conf
[Timer]
OnBootSec=30min
OnUnitActiveSec=1d
AccuracySec=1h
RandomizedDelaySec=30min
APT_TIMER

# --- 5. Pure Headless Micro-OS (Zero Snap) ---
# Verify snapd is completely absent
apt-get purge -y snapd 2>/dev/null || true

# --- 6. Hardware Modules (Apple Silicon & VirtIO) ---
cat << 'MODS' > /etc/modules-load.d/apple-hardware.conf
virtio_net
virtio_blk
virtio_pci
virtio_gpu
virtio_balloon
applesmc
hid_apple
MODS

# --- 7. Operating System Branding & Identity ---
cat << 'OS_RELEASE' > /etc/os-release
NAME="VYRON"
PRETTY_NAME="VYRON Micro-OS v1.0 LTS (Apple Silicon M5 Edition)"
ID=vyron
ID_LIKE=debian
VERSION="1.0-M5-LTS"
VERSION_ID="1.0"
HOME_URL="https://vyron.dev"
OS_RELEASE

echo "vyron-m5" > /etc/hostname
echo "127.0.0.1 localhost vyron-m5" >> /etc/hosts

# Create Default Live User
useradd -m -s /bin/bash -G sudo,adm,dialout,cdrom,audio,video,plugdev vyron
echo "vyron:vyron" | chpasswd
echo "vyron ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/vyron

# Clean APT caches
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
CHROOT_SCRIPT

chmod +x "${ROOTFS}/vyron_setup.sh"
chroot "${ROOTFS}" /bin/bash /vyron_setup.sh
rm -f "${ROOTFS}/vyron_setup.sh"

# ------------------------------------------------------------------------------
# Stage 4: Install System Helpers & First Boot Console
# ------------------------------------------------------------------------------
echo ">>> [4/7] Deploying Standard Debian Utilities and First Boot Console..."
mkdir -p "${ROOTFS}/usr/local/bin"

cp "scripts/vyron-firstboot" "${ROOTFS}/usr/local/bin/vyron-firstboot"
chmod +x "${ROOTFS}/usr/local/bin/"*

# Configure First Boot TUI Screen on TTY1
cat << 'FIRSTBOOT_SERVICE' > "${ROOTFS}/etc/systemd/system/vyron-firstboot.service"
[Unit]
Description=VYRON Micro-OS First Boot Interactive HUD
After=network.target getty@tty1.service
Conflicts=getty@tty1.service

[Service]
Type=idle
ExecStart=/usr/local/bin/vyron-firstboot
StandardInput=tty
StandardOutput=tty
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes

[Install]
WantedBy=multi-user.target
FIRSTBOOT_SERVICE

# Enable First Boot Screen
chroot "${ROOTFS}" systemctl enable vyron-firstboot.service

# ------------------------------------------------------------------------------
# Stage 5: Extract Kernel bzImage and Initramfs
# ------------------------------------------------------------------------------
echo ">>> [5/7] Extracting Kernel and Initramfs for Live Boot..."
KERNEL_VER=$(ls -1 "${ROOTFS}/boot/" | grep -E '^vmlinuz-' | sort -V | tail -n1 | sed 's/vmlinuz-//')
echo "Detected Kernel Version: ${KERNEL_VER}"

cp "${ROOTFS}/boot/vmlinuz-${KERNEL_VER}" "${ISODIR}/live/vmlinuz"
cp "${ROOTFS}/boot/initrd.img-${KERNEL_VER}" "${ISODIR}/live/initrd.img"

# ------------------------------------------------------------------------------
# Stage 6: Compress RootFS into Zstandard Level 19 SquashFS
# ------------------------------------------------------------------------------
echo ">>> [6/7] Compressing Rootfs into High-Speed ZSTD SquashFS..."
mksquashfs "${ROOTFS}" "${ISODIR}/live/filesystem.squashfs" \
    -comp zstd \
    -Xcompression-level 19 \
    -b 1048576 \
    -noappend \
    -wildcards \
    -e "boot/*" \
    -e "var/cache/apt/archives/*" \
    -e "tmp/*"

# ------------------------------------------------------------------------------
# Stage 7: Master Universal Bootable Hybrid ISO with Apple EFI Blessing
# ------------------------------------------------------------------------------
echo ">>> [7/7] Staging EFI Bootloader and Mastering Universal Hybrid ISO..."

# GRUB2 Master Menu Configuration
cat << 'GRUB_CFG' > "${ISODIR}/boot/grub/grub.cfg"
set default="0"
set timeout=3

menuentry "VYRON Micro-OS (Apple Silicon M5 Live Edition)" --class os {
    linux /live/vmlinuz boot=live components quiet console=tty1 console=ttyAMA0,115200 loglevel=3
    initrd /live/initrd.img
}

menuentry "VYRON Micro-OS (RAM Ephemeral Toram Mode)" --class os {
    linux /live/vmlinuz boot=live components toram quiet loglevel=3
    initrd /live/initrd.img
}

menuentry "Reboot Machine" {
    reboot
}
GRUB_CFG

# Apple CoreServices SystemVersion.plist for Startup Manager
cat << 'PLIST' > "${ISODIR}/System/Library/CoreServices/SystemVersion.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>ProductBuildVersion</key>
    <string>24M5011a</string>
    <key>ProductName</key>
    <string>VYRON OS (M5)</string>
    <key>ProductVersion</key>
    <string>1.0</string>
</dict>
</plist>
PLIST

# Build EFI System Partition
dd if=/dev/zero of="${ISODIR}/boot/grub/efi.img" bs=1M count=8
mkfs.vfat -F 12 -n "VYRON_EFI" "${ISODIR}/boot/grub/efi.img"

# Embedded GRUB configuration
cat << 'EMBED_GRUB' > /tmp/vyron_embed_grub.cfg
search --no-floppy --set=root --label VYRON_OS
set prefix=($root)/boot/grub
configfile $prefix/grub.cfg
EMBED_GRUB

# Compile Standalone GRUB binary for target architecture
if [ "${TARGET_ARCH}" = "arm64" ]; then
    grub-mkstandalone \
        --format=arm64-efi \
        --output=/tmp/bootaa64.efi \
        --locales="" \
        --fonts="" \
        "boot/grub/grub.cfg=/tmp/vyron_embed_grub.cfg"
    cp /tmp/bootaa64.efi "${ISODIR}/EFI/BOOT/BOOTAA64.EFI"
    mmd -i "${ISODIR}/boot/grub/efi.img" ::EFI ::EFI/BOOT
    mcopy -i "${ISODIR}/boot/grub/efi.img" /tmp/bootaa64.efi ::EFI/BOOT/BOOTAA64.EFI
else
    grub-mkstandalone \
        --format=x86_64-efi \
        --output=/tmp/bootx64.efi \
        --locales="" \
        --fonts="" \
        "boot/grub/grub.cfg=/tmp/vyron_embed_grub.cfg"
    cp /tmp/bootx64.efi "${ISODIR}/EFI/BOOT/BOOTX64.EFI"
    cp /tmp/bootx64.efi "${ISODIR}/System/Library/CoreServices/boot.efi"
    mmd -i "${ISODIR}/boot/grub/efi.img" ::EFI ::EFI/BOOT
    mcopy -i "${ISODIR}/boot/grub/efi.img" /tmp/bootx64.efi ::EFI/BOOT/BOOTX64.EFI
fi

# Master Universal Hybrid ISO
xorriso -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "VYRON_OS" \
    -appid "VYRON Micro-OS Build Pipeline" \
    -publisher "VYRON Systems Group" \
    -eltorito-alt-boot \
    -e boot/grub/efi.img \
    -no-emul-boot \
    -isohybrid-gpt-basdat \
    -output "${OUTPUT_ISO}" \
    "${ISODIR}"

echo "=========================================================================="
echo "  BUILD SUCCESSFUL: ${OUTPUT_ISO}"
echo "  Run via QEMU: ./run_vyron_m5_qemu.sh ${OUTPUT_ISO}"
echo "  Run via UTM: Open UTM -> Create VM -> Virtualize -> Linux -> Select ISO"
echo "=========================================================================="
