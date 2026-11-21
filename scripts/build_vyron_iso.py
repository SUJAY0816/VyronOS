#!/usr/bin/env python3
"""
==============================================================================
VYRON Micro-OS - Master Bootable Hybrid ISO Generation Pipeline
Packages the UEFI kernel payload into a universal hybrid bootable ISO image.
Compatible with: QEMU, VirtualBox, VMware, UTM, and real hardware (Mac/PC).
==============================================================================
"""

import os
import sys
import shutil
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
VM_DIR = os.path.join(PROJECT_ROOT, "vm")
UEFI_DIR = os.path.join(PROJECT_ROOT, "uefi-payload")

sys.path.insert(0, VM_DIR)
from build_vyron_vdi import build_fat32_partition

def main():
    print("==========================================================================")
    print("  VYRON Micro-OS - Master Bootable Hybrid ISO Build Pipeline")
    print("==========================================================================")

    # 1. Verify / Compile UEFI binaries for both x86_64 and aarch64
    efi_binary = os.path.join(UEFI_DIR, "target", "x86_64-unknown-uefi", "release", "vyron-uefi-kernel.efi")
    efi_aa64_binary = os.path.join(UEFI_DIR, "target", "aarch64-unknown-uefi", "release", "vyron-uefi-kernel.efi")
    cargo_bin = shutil.which("cargo") or os.path.expanduser("~/.cargo/bin/cargo")
    if os.path.exists(cargo_bin):
        print(">>> [1/4] Compiling dual-architecture UEFI kernel payloads (x86_64 + aarch64) with Cargo...")
        subprocess.run([cargo_bin, "build", "--target", "x86_64-unknown-uefi", "--release"], cwd=UEFI_DIR)
        subprocess.run([cargo_bin, "build", "--target", "aarch64-unknown-uefi", "--release"], cwd=UEFI_DIR)
    
    if not os.path.exists(efi_binary):
        print(f"ERROR: Cannot find x86_64 UEFI binary at {efi_binary}")
        sys.exit(1)

    with open(efi_binary, "rb") as f:
        efi_bytes = f.read()
    print(f"    Loaded x86_64 UEFI Kernel Binary ({len(efi_bytes)} bytes)")

    efi_aa64_bytes = None
    if os.path.exists(efi_aa64_binary):
        with open(efi_aa64_binary, "rb") as f:
            efi_aa64_bytes = f.read()
        print(f"    Loaded ARM64 UEFI Kernel Binary ({len(efi_aa64_bytes)} bytes)")

    # 2. Prepare ISO staging workspace
    iso_work = "/tmp/vyron_iso_staging"
    iso_root = os.path.join(iso_work, "iso")
    shutil.rmtree(iso_work, ignore_errors=True)
    os.makedirs(os.path.join(iso_root, "EFI", "BOOT"), exist_ok=True)
    os.makedirs(os.path.join(iso_root, "boot"), exist_ok=True)
    os.makedirs(os.path.join(iso_root, "System", "Library", "CoreServices"), exist_ok=True)

    print(">>> [2/4] Staging ISO filesystem layout...")
    shutil.copyfile(efi_binary, os.path.join(iso_root, "EFI", "BOOT", "BOOTX64.EFI"))
    shutil.copyfile(efi_binary, os.path.join(iso_root, "System", "Library", "CoreServices", "boot.efi"))
    if efi_aa64_binary and os.path.exists(efi_aa64_binary):
        shutil.copyfile(efi_aa64_binary, os.path.join(iso_root, "EFI", "BOOT", "BOOTAA64.EFI"))

    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
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
"""
    with open(os.path.join(iso_root, "System", "Library", "CoreServices", "SystemVersion.plist"), "w") as f:
        f.write(plist_content)

    print(">>> [2b/4] Attaching complete Rust microkernel source code to ISO...")
    rust_dest = os.path.join(iso_root, "rust_source")
    shutil.rmtree(rust_dest, ignore_errors=True)
    os.makedirs(rust_dest, exist_ok=True)
    
    # Copy kernel (ignoring target and build artifacts)
    shutil.copytree(
        os.path.join(PROJECT_ROOT, "kernel"),
        os.path.join(rust_dest, "kernel"),
        ignore=shutil.ignore_patterns("target", "*.log", ".cargo*", "*.exe", "*.rlib")
    )
    
    # Copy uefi-payload (ignoring target and build artifacts)
    shutil.copytree(
        os.path.join(PROJECT_ROOT, "uefi-payload"),
        os.path.join(rust_dest, "uefi-payload"),
        ignore=shutil.ignore_patterns("target", "*.log", ".cargo*", "*.bak")
    )

    readme_txt = """================================================================================
  VYRON Micro-OS v1.0 LTS — Universal Hybrid UEFI Bootable ISO Image
================================================================================
  Architecture: EuraliOS Microkernel Subsystems (TC1-TC10) in Rust 2021
  Boot Mode: Native UEFI 64-bit (x86_64 and ARM64 / Apple Silicon)

================================================================================
  ATTACHED RUST SOURCE CODE:
================================================================================
  This ISO image includes the complete genuine Rust source code directly in
  the 'rust_source/' directory:

  1. rust_source/kernel/
     • Cargo.toml & Cargo.lock: Rust project build manifests
     • src/main.rs & src/lib.rs: Microkernel entry and system exports
     • src/scheduler/: Priority preemptive task scheduling engine
     • src/ipc/: Synchronous Rendezvous Channel message passing
     • src/vfs/: Capability-based Virtual Filesystem node hierarchy
     • src/drivers/: PCI Bus discovery, BAR decoder, RTL8139 & VirtIO-Net
     • src/memory/: Paging, page frame allocator, virtual memory manager
     • src/syscall/: System call dispatchers
     • tests/test_cases.rs: Microkernel test validation suites (TC1-TC10)
     • docs/: Technical reports, architecture specs, and viva prep

  2. rust_source/uefi-payload/
     • Cargo.toml: UEFI application manifest
     • src/main.rs: Direct UEFI graphical bootstrap
     • src/gui.rs: Framebuffer compositor & display driver
     • src/font8x16.rs: Bitmap font rendering engine

================================================================================
  HOW TO RUN THIS ISO:
================================================================================
  1. In Oracle VM VirtualBox:
     • Create a Linux (64-bit) VM.
     • Enable EFI in System -> Motherboard -> Enable EFI.
     • In Storage, attach this 'Vyron-Micro-OS.iso' to the Optical Drive.
     • Start the VM.

  2. On Physical Hardware:
     • Flash to a USB flash drive using BalenaEtcher or Rufus.
     • Boot your PC/Mac in UEFI mode.
================================================================================
"""
    with open(os.path.join(iso_root, "README.TXT"), "w") as f:
        f.write(readme_txt)

    # 3. Build EFI FAT32 Partition Image
    print(">>> [3/4] Generating El Torito EFI Boot Partition (FAT32)...")
    fat_img = build_fat32_partition(68000, efi_bytes, efi_aa64_bytes, b"VYRON Micro-OS")
    with open(os.path.join(iso_root, "boot", "efi.img"), "wb") as f:
        f.write(fat_img)

    # 4. Master ISO with xorriso
    print(">>> [4/4] Mastering Universal Hybrid ISO with xorriso...")
    xorriso_bin = shutil.which("xorriso") or "/opt/homebrew/bin/xorriso"
    if not os.path.exists(xorriso_bin):
        print(f"ERROR: xorriso not found at {xorriso_bin}. Install via Homebrew: brew install xorriso")
        sys.exit(1)

    out_iso_vm = os.path.join(VM_DIR, "Vyron-Micro-OS.iso")
    out_iso_root = os.path.join(PROJECT_ROOT, "Vyron-Micro-OS.iso")
    for p in (out_iso_vm, out_iso_root):
        if os.path.exists(p):
            os.remove(p)

    cmd = [
        xorriso_bin, "-as", "mkisofs",
        "-iso-level", "3",
        "-full-iso9660-filenames",
        "-volid", "VYRON_OS",
        "-appid", "VYRON Micro-OS v1.0 LTS",
        "-publisher", "SREEHARAN",
        "-eltorito-alt-boot",
        "-e", "boot/efi.img",
        "-no-emul-boot",
        "-isohybrid-gpt-basdat",
        "-output", out_iso_vm,
        iso_root
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("Xorriso error:", res.stderr)
        sys.exit(res.returncode)

    shutil.copyfile(out_iso_vm, out_iso_root)
    iso_size_mb = os.path.getsize(out_iso_vm) / (1024 * 1024)

    print("==========================================================================")
    print(f"  SUCCESS: Bootable ISO created successfully ({iso_size_mb:.1f} MB)")
    print(f"  VM Location   : {out_iso_vm}")
    print(f"  Root Location : {out_iso_root}")
    print("==========================================================================")

if __name__ == "__main__":
    main()
