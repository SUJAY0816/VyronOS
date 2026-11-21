#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BUILD_DIR = os.path.join(ROOT_DIR, "build")
BOOT_ASSETS = os.path.join(BUILD_DIR, "boot_assets")
DIST_DIR = os.path.join(ROOT_DIR, "dist")
ISO_STAGING = os.path.join(BUILD_DIR, "iso_staging")
OUT_ISO = os.path.join(DIST_DIR, "VyronOS-Live.iso")

sys.path.insert(0, os.path.join(ROOT_DIR, "vm"))
from build_vyron_vdi import build_fat32_partition

def main():
    print(">>> Staging VyronOS Live Bootable UEFI ISO...")
    shutil.rmtree(ISO_STAGING, ignore_errors=True)
    os.makedirs(os.path.join(ISO_STAGING, "EFI", "BOOT"), exist_ok=True)
    os.makedirs(os.path.join(ISO_STAGING, "boot", "grub", "x86_64-efi"), exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)

    # 1. Copy Kernel & Initramfs
    vmlinuz_src = os.path.join(BOOT_ASSETS, "vmlinuz-6.1.0-56-amd64")
    initrd_src = os.path.join(BOOT_ASSETS, "initrd.img-6.1.0-56-amd64")
    shutil.copyfile(vmlinuz_src, os.path.join(ISO_STAGING, "boot", "vmlinuz"))
    shutil.copyfile(initrd_src, os.path.join(ISO_STAGING, "boot", "initrd.img"))
    print(f"    Kernel : {vmlinuz_src} -> boot/vmlinuz")
    print(f"    Initrd : {initrd_src} -> boot/initrd.img")

    # 2. Copy GRUB EFI Bootloaders (use grubx64 directly as BOOTX64.EFI to avoid shim search errors)
    bootx64 = os.path.join(BOOT_ASSETS, "efi", "EFI", "BOOT", "BOOTX64.EFI")
    grubx64 = os.path.join(BOOT_ASSETS, "efi", "EFI", "BOOT", "grubx64.efi")
    shutil.copyfile(grubx64, os.path.join(ISO_STAGING, "EFI", "BOOT", "BOOTX64.EFI"))
    shutil.copyfile(grubx64, os.path.join(ISO_STAGING, "EFI", "BOOT", "grubx64.efi"))

    # Copy GRUB modules
    grub_mods_src = os.path.join(BOOT_ASSETS, "grub", "x86_64-efi")
    if os.path.exists(grub_mods_src):
        for f in os.listdir(grub_mods_src):
            s = os.path.join(grub_mods_src, f)
            if os.path.isfile(s):
                shutil.copyfile(s, os.path.join(ISO_STAGING, "boot", "grub", "x86_64-efi", f))

    # 3. Create GRUB Configuration
    grub_cfg = """set default="0"
set timeout=3

insmod efi_gop
insmod font
insmod gfxterm
insmod all_video

menuentry "VYRON Desktop OS 1.0 LTS (Live Serial Console)" --class os {
    linux /boot/vmlinuz console=ttyS0,115200 console=tty0
    initrd /boot/initrd.img
}

menuentry "VYRON Desktop OS 1.0 LTS (Quiet Live Boot)" --class os {
    linux /boot/vmlinuz quiet splash loglevel=3 console=ttyS0 console=tty0
    initrd /boot/initrd.img
}

menuentry "Reboot System" {
    reboot
}

menuentry "Power Off" {
    halt
}
"""
    with open(os.path.join(ISO_STAGING, "boot", "grub", "grub.cfg"), "w") as f:
        f.write(grub_cfg)

    # 4. Build EFI System Partition Image (FAT32)
    with open(grubx64, "rb") as f:
        grub_bytes = f.read()
    efi_fat = build_fat32_partition(68000, grub_bytes, None, b"VYRON Desktop OS EFI Bootloader")
    with open(os.path.join(ISO_STAGING, "boot", "efi.img"), "wb") as f:
        f.write(efi_fat)
    print("    Built EFI System Partition (boot/efi.img)")

    # 5. Master Hybrid ISO with xorriso
    xorriso_bin = "/opt/homebrew/bin/xorriso"
    if not os.path.exists(xorriso_bin):
        xorriso_bin = shutil.which("xorriso")
    if not xorriso_bin:
        print("ERROR: xorriso not found")
        sys.exit(1)

    cmd = [
        xorriso_bin, "-as", "mkisofs",
        "-iso-level", "3",
        "-full-iso9660-filenames",
        "-volid", "VYRON_OS",
        "-appid", "VYRON Desktop OS 1.0 LTS",
        "-publisher", "VYRON Engineering",
        "-eltorito-alt-boot",
        "-e", "boot/efi.img",
        "-no-emul-boot",
        "-isohybrid-gpt-basdat",
        "-output", OUT_ISO,
        ISO_STAGING
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("Xorriso error:", res.stderr)
        sys.exit(res.returncode)

    size_mb = os.path.getsize(OUT_ISO) / (1024 * 1024)
    print(f"=== ISO CREATION SUCCESSFUL: {OUT_ISO} ({size_mb:.1f} MB) ===")

if __name__ == "__main__":
    main()
