#!/usr/bin/env bash
# ==============================================================================
# VYRON OS - Phase 2 Master Build Pipeline
# Builds a genuine bootable Debian-based Linux system for QEMU & UEFI hardware.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CACHE_DIR="${ROOT_DIR}/cache"
BUILD_DIR="${ROOT_DIR}/build"
DIST_DIR="${ROOT_DIR}/dist"
BOOT_ASSETS="${BUILD_DIR}/boot_assets"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin"

DEBIAN_IMAGE_URL="https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-nocloud-amd64.qcow2"
BASE_IMAGE="${CACHE_DIR}/debian-12-nocloud-amd64.qcow2"
TARGET_DISK="${DIST_DIR}/VyronOS-Disk.qcow2"
TARGET_ISO="${DIST_DIR}/VyronOS-Live.iso"
OVMF_CODE="/opt/homebrew/share/qemu/edk2-x86_64-code.fd"

if [[ ! -f "${OVMF_CODE}" ]]; then
    OVMF_CODE=$(find /opt/homebrew /usr/share/qemu -name "*edk2-x86_64-code.fd" 2>/dev/null | head -n 1 || true)
fi

echo "=========================================================================="
echo "  VYRON OS — Phase 2 Boot System & RootFS Build Pipeline"
echo "=========================================================================="
echo "  Base Directory   : ${ROOT_DIR}"
echo "  Target Disk      : ${TARGET_DISK}"
echo "  Target Live ISO  : ${TARGET_ISO}"
echo "  Firmware         : ${OVMF_CODE}"
echo "=========================================================================="

mkdir -p "${CACHE_DIR}" "${BUILD_DIR}" "${DIST_DIR}" "${BOOT_ASSETS}"

# 1. Dependency Checks
echo ">>> [1/5] Checking toolchain dependencies..."
for tool in qemu-system-x86_64 qemu-img xorriso curl python3; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo "ERROR: Required build tool '${tool}' is not installed in PATH."
        exit 1
    fi
    echo "    Found: $(which ${tool})"
done

# 2. Download Official Debian Base Image if not cached
echo ">>> [2/5] Verifying Debian Bookworm base image cache..."
if [[ ! -f "${BASE_IMAGE}" ]]; then
    echo "    Downloading Debian 12 Bookworm nocloud image..."
    curl -L --retry 3 -C - -o "${BASE_IMAGE}" "${DEBIAN_IMAGE_URL}"
else
    echo "    Cached base image verified: ${BASE_IMAGE} ($(du -h "${BASE_IMAGE}" | cut -f1))"
fi

# 3. Assemble and Provision VyronOS Persistent Virtual Disk
echo ">>> [3/5] Assembling VyronOS persistent virtual disk (10 GB ext4 rootfs)..."
if [[ ! -f "${TARGET_DISK}" ]]; then
    cp "${BASE_IMAGE}" "${TARGET_DISK}"
    qemu-img resize "${TARGET_DISK}" 10G
    echo "    Resized virtual disk to 10 GiB."
else
    echo "    Target disk exists: ${TARGET_DISK}"
fi

# 4. Verify / Extract Kernel & Initramfs Boot Assets
echo ">>> [4/5] Checking genuine Linux kernel & initramfs boot assets..."
VMLINUZ="${BOOT_ASSETS}/vmlinuz-6.1.0-56-amd64"
INITRD="${BOOT_ASSETS}/initrd.img-6.1.0-56-amd64"

if [[ ! -f "${VMLINUZ}" || ! -f "${INITRD}" ]]; then
    echo "    Extracting boot assets from base system image..."
    RAW_EXPORT="${BUILD_DIR}/boot_export.raw"
    dd if=/dev/zero of="${RAW_EXPORT}" bs=1M count=128 status=none
    
    # Run guest export
    python3 -c "
import subprocess, time
cmd = [
    'qemu-system-x86_64', '-m', '1024', '-smp', '2',
    '-drive', 'if=pflash,format=raw,readonly=on,file=${OVMF_CODE}',
    '-drive', 'file=${TARGET_DISK},format=qcow2',
    '-drive', 'file=${RAW_EXPORT},format=raw',
    '-display', 'none', '-serial', 'stdio'
]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
time.sleep(18)
p.stdin.write('root\nvyron\n')
p.stdin.flush()
time.sleep(2)
p.stdin.write('tar -czf /dev/sdb -C /boot . && sync && poweroff\n')
p.stdin.flush()
p.wait(timeout=60)
"
    tar -xzf "${RAW_EXPORT}" -C "${BOOT_ASSETS}"
fi

echo "    Kernel Image : ${VMLINUZ} ($(du -h "${VMLINUZ}" | cut -f1))"
echo "    Initramfs    : ${INITRD} ($(du -h "${INITRD}" | cut -f1))"

# 5. Build Bootable Hybrid UEFI Live ISO
echo ">>> [5/5] Mastering VyronOS Live Bootable UEFI Hybrid ISO..."
python3 "${SCRIPT_DIR}/make_iso.py"

echo "=========================================================================="
echo "  BUILD SUCCESSFUL"
echo "  Persistent Disk : ${TARGET_DISK}"
echo "  Live UEFI ISO   : ${TARGET_ISO}"
echo "  To launch       : ${SCRIPT_DIR}/run-qemu.sh"
echo "  To test boot    : ${SCRIPT_DIR}/test-boot.sh"
echo "=========================================================================="
