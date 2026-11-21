#!/usr/bin/env bash
# ==============================================================================
# VYRON Micro-OS - Master USB Pendrive Live-Boot Creator
# Prepares any USB Flash Drive for Live-Booting on Mac, Intel & AMD PCs
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO_PATH="${SCRIPT_DIR}/Vyron-Micro-OS.iso"
UEFI_DIR="${SCRIPT_DIR}/uefi-payload"
X86_EFI="${UEFI_DIR}/target/x86_64-unknown-uefi/release/vyron-uefi-kernel.efi"
ARM_EFI="${UEFI_DIR}/target/aarch64-unknown-uefi/release/vyron-uefi-kernel.efi"

echo "=============================================================================="
echo "         VYRON Micro-OS - USB Pendrive Live-Boot Creator"
echo "=============================================================================="
echo ""

# Ensure latest ISO and binaries are built
if [[ ! -f "${ISO_PATH}" || ! -f "${X86_EFI}" ]]; then
    echo ">>> Building latest dual-architecture UEFI kernel & ISO image..."
    "${SCRIPT_DIR}/build_iso.sh"
fi

echo "Scanning connected storage devices..."
echo "------------------------------------------------------------------------------"
diskutil list external || echo "No external drives found yet. Please connect your USB pendrive."
echo "------------------------------------------------------------------------------"
echo ""

# Auto-detect external USB drive (excluding internal Apple APFS disks)
EXTERNAL_DISKS=$(diskutil list external | grep -E "^/dev/disk[0-9]+" | awk '{print $1}')

if [[ -z "${EXTERNAL_DISKS}" ]]; then
    echo "⚠️  No USB Flash Drive detected."
    echo "👉 Please insert your USB pendrive into the USB port, then re-run this script:"
    echo "   cd /Users/sujayv/Downloads/VyronOS && ./flash_to_usb.sh"
    exit 0
fi

echo "Detected external drive(s):"
for d in ${EXTERNAL_DISKS}; do
    SIZE=$(diskutil info "$d" | grep "Disk Size" | awk -F: '{print $2}' | xargs)
    NAME=$(diskutil info "$d" | grep "Device / Media Name" | awk -F: '{print $2}' | xargs)
    echo "  -> Disk: $d ($NAME, $SIZE)"
done
echo ""

# If only one external drive, suggest it
DEFAULT_DISK=$(echo "${EXTERNAL_DISKS}" | head -n 1)
read -p "Enter the target disk identifier to format [default: ${DEFAULT_DISK}]: " TARGET_DISK
TARGET_DISK="${TARGET_DISK:-${DEFAULT_DISK}}"

# Security check: Never allow internal disk
IS_INTERNAL=$(diskutil info "${TARGET_DISK}" | grep -i "Internal:" | awk '{print $2}' || true)
if [[ "${IS_INTERNAL}" == "Yes" ]]; then
    echo "❌ ERROR: ${TARGET_DISK} is an INTERNAL drive! Aborting to protect your Mac."
    exit 1
fi

echo ""
echo "⚠️  WARNING: ALL DATA ON ${TARGET_DISK} WILL BE FORMATTED!"
echo "Target Disk: ${TARGET_DISK}"
read -p "Are you sure you want to proceed? (y/N): " CONFIRM
if [[ "${CONFIRM}" != "y" && "${CONFIRM}" != "Y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo ""
echo "Choose Live-Boot USB Creation Mode:"
echo "  [1] UEFI FAT32 EFI System Partition (Recommended: 3 seconds, works on ALL UEFI Mac & PCs)"
echo "  [2] Raw Hybrid ISO dd Flash (Overwrites partition table with byte-exact ISO9660)"
read -p "Select mode [1/2, default 1]: " MODE
MODE="${MODE:-1}"

if [[ "${MODE}" == "1" ]]; then
    echo ""
    echo ">>> [1/3] Formatting ${TARGET_DISK} as FAT32 'VYRON_BOOT' with MBR/GPT..."
    diskutil eraseDisk FAT32 VYRON_BOOT MBR "${TARGET_DISK}"

    # Find the mounted volume
    VOL_PATH="/Volumes/VYRON_BOOT"
    if [[ ! -d "${VOL_PATH}" ]]; then
        # Wait a moment for macOS Automount
        sleep 2
    fi

    echo ">>> [2/3] Installing dual-architecture UEFI bootloader structure..."
    mkdir -p "${VOL_PATH}/EFI/BOOT"
    mkdir -p "${VOL_PATH}/System/Library/CoreServices"

    # Install x86_64 UEFI Bootloader (Intel / AMD PCs and Intel Macs)
    cp -v "${X86_EFI}" "${VOL_PATH}/EFI/BOOT/BOOTX64.EFI"
    cp -v "${X86_EFI}" "${VOL_PATH}/System/Library/CoreServices/boot.efi"

    # Install ARM64 UEFI Bootloader (Apple Silicon Macs & ARM64 laptops)
    if [[ -f "${ARM_EFI}" ]]; then
        cp -v "${ARM_EFI}" "${VOL_PATH}/EFI/BOOT/BOOTAA64.EFI"
    fi

    # Apple Mac boot metadata
    cat << 'EOF' > "${VOL_PATH}/System/Library/CoreServices/SystemVersion.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>ProductBuildVersion</key>
    <string>24M5011a</string>
    <key>ProductName</key>
    <string>VYRON Micro-OS</string>
    <key>ProductVersion</key>
    <string>1.0</string>
</dict>
</plist>
EOF

    cat << 'EOF' > "${VOL_PATH}/README.TXT"
==============================================================================
VYRON Micro-OS v1.0 LTS - Live Boot USB Drive
Architecture: Modular Rust Micro-Kernel & Modern Desktop Compositor
Author: SREEHARAN (Operating Systems Concepts - 25PCCS201)
==============================================================================

Boot Instructions:
- Apple Mac: Hold Option (Alt) key immediately upon pressing Power button.
  Select the orange 'EFI Boot' disk icon.
- Intel / AMD PC Laptops (Dell, HP, Lenovo, ASUS): Press F12 (or F2 / Del)
  during boot to enter the One-Time Boot Menu. Select 'UEFI: VYRON_BOOT'.
==============================================================================
EOF

    echo ">>> [3/3] Synchronizing drive writes and safely ejecting..."
    sync
    diskutil eject "${TARGET_DISK}"
    echo ""
    echo "=============================================================================="
    echo "  🎉 SUCCESS: USB Live-Boot Pendrive is 100% READY!"
    echo "=============================================================================="

else
    echo ""
    echo ">>> Unmounting ${TARGET_DISK} for raw block flash..."
    diskutil unmountDisk "${TARGET_DISK}"
    RAW_DISK="/dev/r${TARGET_DISK#/dev/}"
    echo ">>> Flashing ${ISO_PATH} directly to ${RAW_DISK} (sudo required)..."
    sudo dd if="${ISO_PATH}" of="${RAW_DISK}" bs=4m status=progress
    sync
    diskutil eject "${TARGET_DISK}" || true
    echo ""
    echo "=============================================================================="
    echo "  🎉 SUCCESS: Raw ISO Flashed to Pendrive!"
    echo "=============================================================================="
fi

echo ""
echo "HOW TO LIVE BOOT IN FRONT OF YOUR SIR:"
echo "------------------------------------------------------------------------------"
echo "1. On Apple Mac:"
echo "   - Plug pendrive in, restart Mac while holding Option (Alt) key."
echo "   - Select 'EFI Boot' icon. Press Enter."
echo "2. On Windows / Intel / AMD Laptops:"
echo "   - Plug pendrive in, turn on laptop while tapping F12 (Dell/Lenovo), F9 (HP), or F8 (ASUS)."
echo "   - Select 'UEFI: USB Drive' / 'EFI Boot'. Press Enter."
echo "3. The laptop will immediately display the VYRON OS Logo, run the progressive"
echo "   5-component boot benchmark (WiFi/LAN, Laptop HW, Aptitude/APT, Snap Store),"
echo "   and load the full live interactive desktop!"
echo "=============================================================================="
