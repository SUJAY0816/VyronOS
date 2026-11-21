#!/usr/bin/env python3
"""
==============================================================================
VYRON Micro-OS - Master VirtualBox Disk & EFI Image Builder
Builds the bootable EFI virtual disk (Vyron-Boot.vdi) for Oracle VM VirtualBox.
==============================================================================
"""

import os
import sys
import uuid
import zlib
import struct
import subprocess
import shutil

SECTOR = 512

def lfn_entries(long_name, short11):
    chk = 0
    for c in short11:
        chk = (((chk & 1) << 7) + (chk >> 1) + c) & 0xFF
    units = [ord(c) for c in long_name] + [0]
    while len(units) % 13:
        units.append(0xFFFF)
    parts = [units[i:i + 13] for i in range(0, len(units), 13)]
    out = []
    for n in range(len(parts), 0, -1):
        u = parts[n - 1]
        seq = n | (0x40 if n == len(parts) else 0)
        e = (bytes([seq]) +
             struct.pack("<5H", *u[0:5]) +
             bytes([0x0F, 0, chk]) +
             struct.pack("<6H", *u[5:11]) +
             b"\0\0" +
             struct.pack("<2H", *u[11:13]))
        assert len(e) == 32
        out.append(e)
    return out

def make_dirent(name11, attr, cluster, size):
    e = bytearray(32)
    e[0:11] = name11
    e[11] = attr
    struct.pack_into("<H", e, 20, (cluster >> 16) & 0xFFFF)
    struct.pack_into("<H", e, 26, cluster & 0xFFFF)
    struct.pack_into("<I", e, 28, size)
    return bytes(e)

def build_fat32_partition(total_sectors, efi_bytes, efi_aa64_bytes, readme_bytes):
    spc = 1
    reserved = 32
    
    fat_sectors = 1
    while True:
        clusters = (total_sectors - reserved - 2 * fat_sectors) // spc
        need = ((clusters + 2) * 4 + SECTOR - 1) // SECTOR
        if need <= fat_sectors:
            break
        fat_sectors += 1

    assert clusters >= 65525, f"Not enough clusters for FAT32: {clusters}"

    part = bytearray(total_sectors * SECTOR)

    # Boot Sector
    bs = bytearray(SECTOR)
    bs[0:3] = b"\xEB\x58\x90"
    bs[3:11] = b"VYRONFAT"
    struct.pack_into("<HBHBHHBHHHII", bs, 11,
                     SECTOR, spc, reserved, 2, 0, 0, 0xF8, 0, 32, 64, 2048, total_sectors)
    struct.pack_into("<IHHIHH", bs, 36, fat_sectors, 0, 0, 2, 1, 6)
    bs[66] = 0x29
    struct.pack_into("<I", bs, 67, 0x20261114)
    bs[71:82] = b"VYRON BOOT "
    bs[82:90] = b"FAT32   "
    bs[510:512] = b"\x55\xAA"
    part[0:SECTOR] = bs
    part[6 * SECTOR:7 * SECTOR] = bs

    # FSInfo
    fsinfo = bytearray(SECTOR)
    fsinfo[0:4] = b"RRaA"
    fsinfo[484:488] = b"rrAa"
    struct.pack_into("<II", fsinfo, 488, 0xFFFFFFFF, 3)
    fsinfo[508:512] = b"\x00\x00\x55\xAA"
    part[SECTOR:2 * SECTOR] = fsinfo
    part[7 * SECTOR:8 * SECTOR] = fsinfo

    fat_off = reserved * SECTOR
    first_data = reserved + 2 * fat_sectors
    next_cluster = [3]

    def fat_set(c, v):
        for k in range(2):
            o = fat_off + k * fat_sectors * SECTOR + c * 4
            struct.pack_into("<I", part, o, v)

    fat_set(0, 0x0FFFFFF8)
    fat_set(1, 0x0FFFFFFF)
    fat_set(2, 0x0FFFFFFF)

    def cluster_off(c):
        return (first_data + (c - 2) * spc) * SECTOR

    def alloc_chain(data):
        if not data:
            return 0
        n = (len(data) + spc * SECTOR - 1) // (spc * SECTOR)
        first = next_cluster[0]
        cl = list(range(first, first + n))
        next_cluster[0] += n
        for i, c in enumerate(cl):
            fat_set(c, cl[i + 1] if i + 1 < n else 0x0FFFFFFF)
            chunk = data[i * spc * SECTOR:(i + 1) * spc * SECTOR]
            part[cluster_off(c):cluster_off(c) + len(chunk)] = chunk
        return first

    bootx64_c = alloc_chain(efi_bytes)
    bootaa64_c = alloc_chain(efi_aa64_bytes) if efi_aa64_bytes else 0
    readme_c = alloc_chain(readme_bytes)

    # /EFI/BOOT
    boot_c = next_cluster[0]
    next_cluster[0] += 1
    fat_set(boot_c, 0x0FFFFFFF)

    # /EFI
    efi_c = next_cluster[0]
    next_cluster[0] += 1
    fat_set(efi_c, 0x0FFFFFFF)

    # Fill /EFI/BOOT
    boot_dir = bytearray()
    boot_dir += make_dirent(b".          ", 0x10, boot_c, 0)
    boot_dir += make_dirent(b"..         ", 0x10, efi_c, 0)
    boot_dir += make_dirent(b"BOOTX64 EFI", 0x20, bootx64_c, len(efi_bytes))
    if efi_aa64_bytes:
        boot_dir += make_dirent(b"BOOTAA64EFI", 0x20, bootaa64_c, len(efi_aa64_bytes))
    part[cluster_off(boot_c):cluster_off(boot_c) + len(boot_dir)] = boot_dir

    # Fill /EFI
    efi_dir = bytearray()
    efi_dir += make_dirent(b".          ", 0x10, efi_c, 0)
    efi_dir += make_dirent(b"..         ", 0x10, 0, 0)
    efi_dir += make_dirent(b"BOOT       ", 0x10, boot_c, 0)
    part[cluster_off(efi_c):cluster_off(efi_c) + len(efi_dir)] = efi_dir

    # Fill Root directory
    root = bytearray()
    root += make_dirent(b"VYRON BOOT ", 0x08, 0, 0)
    root += make_dirent(b"EFI        ", 0x10, efi_c, 0)
    root += make_dirent(b"README  TXT", 0x20, readme_c, len(readme_bytes))
    part[cluster_off(2):cluster_off(2) + len(root)] = root

    return part

def build_boot_disk(out_img_path, efi_bytes, efi_aa64_bytes, readme_bytes):
    total_disk_sectors = 131072 # 64 MB
    esp_lba_start = 2048
    esp_lba_end = total_disk_sectors - 34
    esp_sectors = esp_lba_end - esp_lba_start + 1

    fat_data = build_fat32_partition(esp_sectors, efi_bytes, efi_aa64_bytes, readme_bytes)

    disk = bytearray(total_disk_sectors * SECTOR)

    # 1. Protective / Hybrid MBR
    mbr = bytearray(SECTOR)
    mbr[446] = 0x80 # Bootable
    mbr[447:450] = b"\x00\x20\x21"
    mbr[450] = 0xEF # EFI System Partition
    mbr[451:454] = b"\xFE\xFF\xFF"
    struct.pack_into("<II", mbr, 454, esp_lba_start, esp_sectors)
    mbr[510:512] = b"\x55\xAA"
    disk[0:SECTOR] = mbr

    # 2. Primary GPT
    disk_guid = uuid.uuid4().bytes_le
    part_guid = uuid.uuid4().bytes_le
    esp_type_guid = uuid.UUID("{C12A7328-F81F-11D2-BA4B-00A0C93EC93B}").bytes_le

    part_entry = bytearray(128)
    part_entry[0:16] = esp_type_guid
    part_entry[16:32] = part_guid
    struct.pack_into("<QQQ", part_entry, 32, esp_lba_start, esp_lba_end, 0)
    name_utf16 = "EFI System Partition".encode("utf-16le")
    part_entry[56:56 + len(name_utf16)] = name_utf16

    part_table = bytearray(128 * 128)
    part_table[0:128] = part_entry
    part_crc = zlib.crc32(part_table) & 0xFFFFFFFF

    gpt_hdr = bytearray(92)
    gpt_hdr[0:8] = b"EFI PART"
    struct.pack_into("<II", gpt_hdr, 8, 0x00010000, 92)
    struct.pack_into("<I", gpt_hdr, 20, 0)
    struct.pack_into("<QQQQ", gpt_hdr, 24, 1, total_disk_sectors - 1, 2048, total_disk_sectors - 34)
    gpt_hdr[56:72] = disk_guid
    struct.pack_into("<QII", gpt_hdr, 72, 2, 128, 128)
    struct.pack_into("<I", gpt_hdr, 88, part_crc)
    hdr_crc = zlib.crc32(gpt_hdr) & 0xFFFFFFFF
    struct.pack_into("<I", gpt_hdr, 16, hdr_crc)

    disk[SECTOR:2 * SECTOR] = gpt_hdr + bytearray(SECTOR - 92)
    disk[2 * SECTOR:34 * SECTOR] = part_table

    # 3. Partition Data
    disk[esp_lba_start * SECTOR:(esp_lba_start + esp_sectors) * SECTOR] = fat_data

    # 4. Backup GPT
    disk[(total_disk_sectors - 33) * SECTOR:(total_disk_sectors - 1) * SECTOR] = part_table

    gpt_bak = bytearray(gpt_hdr)
    struct.pack_into("<I", gpt_bak, 16, 0)
    struct.pack_into("<QQ", gpt_bak, 24, total_disk_sectors - 1, 1)
    struct.pack_into("<Q", gpt_bak, 72, total_disk_sectors - 33)
    bak_crc = zlib.crc32(gpt_bak) & 0xFFFFFFFF
    struct.pack_into("<I", gpt_bak, 16, bak_crc)
    disk[(total_disk_sectors - 1) * SECTOR:total_disk_sectors * SECTOR] = gpt_bak + bytearray(SECTOR - 92)

    with open(out_img_path, "wb") as f:
        f.write(disk)

VYRON_BOOT_UUID = "8899aabb-ccdd-eeff-0011-223344556677"

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    efi_src = os.path.join(script_dir, "..", "uefi-payload", "target", "x86_64-unknown-uefi", "release", "vyron-uefi-kernel.efi")
    efi_aa64_src = os.path.join(script_dir, "..", "uefi-payload", "target", "aarch64-unknown-uefi", "release", "vyron-uefi-kernel.efi")
    
    if not os.path.exists(efi_src):
        print(f"ERROR: Cannot find EFI binary at {efi_src}")
        sys.exit(1)

    with open(efi_src, "rb") as f:
        efi_bytes = f.read()

    efi_aa64_bytes = None
    if os.path.exists(efi_aa64_src):
        with open(efi_aa64_src, "rb") as f:
            efi_aa64_bytes = f.read()

    readme_text = b"VYRON Micro-OS v1.0 LTS\nHigh-Performance Micro Operating System\nAuthor: SREEHARAN\n"

    boot_raw = os.path.join(script_dir, "Vyron-Boot.raw")
    boot_vdi = os.path.join(script_dir, "Vyron-Boot.vdi")

    print(f"Building dual-architecture EFI disk image: {boot_raw} (x86_64: {len(efi_bytes)}B, aarch64: {len(efi_aa64_bytes) if efi_aa64_bytes else 0}B)...")
    build_boot_disk(boot_raw, efi_bytes, efi_aa64_bytes, readme_text)

    # Convert to VDI if qemu-img or VBoxManage is available
    qemu_img = shutil.which("qemu-img") or "/opt/homebrew/bin/qemu-img"
    vboxmanage = shutil.which("VBoxManage") or r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    
    if os.path.exists(qemu_img):
        print(f"Converting raw disk to VDI format using qemu-img: {boot_vdi}...")
        if os.path.exists(boot_vdi):
            os.remove(boot_vdi)
        subprocess.run([qemu_img, "convert", "-U", "-O", "vdi", boot_raw, boot_vdi], check=True)
        try:
            vbm = "/Users/sujayv/.local/bin/VBoxManage"
            if os.path.exists(vbm):
                subprocess.run([vbm, "internalcommands", "sethduuid", boot_vdi, "202789b6-1180-43f8-a472-5b6871ba636d"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        print(f"SUCCESS: Vyron-Boot.vdi created successfully at: {boot_vdi}")
    elif os.path.exists(vboxmanage):
        print(f"Converting raw disk to VirtualBox VDI format: {boot_vdi}...")
        if os.path.exists(boot_vdi):
            try:
                subprocess.run([vboxmanage, "closemedium", "disk", boot_vdi], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            os.remove(boot_vdi)
        subprocess.run([vboxmanage, "convertfromraw", boot_raw, boot_vdi, "--format", "VDI", f"--uuid={VYRON_BOOT_UUID}"], check=True)
        print(f"SUCCESS: Vyron-Boot.vdi created successfully at: {boot_vdi}")
    else:
        print(f"SUCCESS: Vyron-Boot.raw created successfully at: {boot_raw}")

if __name__ == "__main__":
    main()
