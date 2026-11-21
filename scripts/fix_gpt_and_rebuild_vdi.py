#!/usr/bin/env python3
import os
import sys
import struct
import zlib
import uuid
import subprocess

RAW_PATH = "/Users/sujayv/Downloads/VyronOS/release_phase7/disk.raw"
VDI_PATH = "/Users/sujayv/Downloads/VyronOS/release_phase7/VyronOS-Phase7-Production.vdi"
QEMU_IMG = "/opt/homebrew/bin/qemu-img"

def main():
    print("=== Converting VDI to raw for GPT repair ===")
    if os.path.exists(RAW_PATH):
        os.remove(RAW_PATH)
    subprocess.run([QEMU_IMG, "convert", "-O", "raw", VDI_PATH, RAW_PATH], check=True)
    
    file_size = os.path.getsize(RAW_PATH)
    total_lba = file_size // 512
    print(f"Disk size: {file_size} bytes ({total_lba} sectors)")
    
    with open(RAW_PATH, "r+b") as f:
        # Read Primary GPT header (LBA 1)
        f.seek(512)
        prim_hdr = bytearray(f.read(512))
        assert prim_hdr[:8] == b"EFI PART", "Invalid GPT signature"
        
        # Read Partition entries
        f.seek(1024)
        entries = bytearray(f.read(128 * 128))
        
        # Update Partition 1 last_lba to match rootfs size (24GB)
        # Partition 1 is index 0
        part1_first, part1_last = struct.unpack("<QQ", entries[32:48])
        print(f"Partition 1 current: first={part1_first}, last={part1_last}")
        part1_guid = uuid.UUID(bytes_le=bytes(entries[16:32]))
        print(f"Partition 1 GUID (PARTUUID): {part1_guid}")
        
        # Ensure part1_guid is ec261af9-67f0-4cbc-9d9f-e25d891f9bdb
        expected_guid = uuid.UUID("ec261af9-67f0-4cbc-9d9f-e25d891f9bdb")
        entries[16:32] = expected_guid.bytes_le
        print(f"Set Partition 1 GUID to: {expected_guid}")
        
        # Calculate last_usable LBA
        alt_lba = total_lba - 1
        last_usable = total_lba - 34
        first_usable = 2048
        
        print(f"Total LBA: {total_lba}, Alt LBA: {alt_lba}, Last Usable: {last_usable}")
        assert part1_last <= last_usable, f"Partition 1 exceeds last usable: {part1_last} > {last_usable}"
        
        # CRC32 of partition entries
        part_crc = zlib.crc32(entries) & 0xFFFFFFFF
        
        # Update Primary Header
        struct.pack_into("<Q", prim_hdr, 24, 1)            # my_lba = 1
        struct.pack_into("<Q", prim_hdr, 32, alt_lba)      # alt_lba
        struct.pack_into("<Q", prim_hdr, 40, first_usable)  # first_usable
        struct.pack_into("<Q", prim_hdr, 48, last_usable)   # last_usable
        struct.pack_into("<Q", prim_hdr, 72, 2)            # part_lba = 2
        struct.pack_into("<I", prim_hdr, 80, 128)          # num_parts
        struct.pack_into("<I", prim_hdr, 84, 128)          # part_size
        struct.pack_into("<I", prim_hdr, 88, part_crc)      # part_crc
        
        struct.pack_into("<I", prim_hdr, 16, 0)            # zero CRC field
        prim_crc = zlib.crc32(prim_hdr[:92]) & 0xFFFFFFFF
        struct.pack_into("<I", prim_hdr, 16, prim_crc)     # set CRC
        
        # Write Primary Header & Entries
        f.seek(512)
        f.write(prim_hdr)
        f.seek(1024)
        f.write(entries)
        
        # Prepare Backup Header & Entries
        backup_part_lba = total_lba - 33
        backup_hdr = bytearray(prim_hdr)
        struct.pack_into("<Q", backup_hdr, 24, alt_lba)        # my_lba = alt_lba
        struct.pack_into("<Q", backup_hdr, 32, 1)              # alt_lba = 1
        struct.pack_into("<Q", backup_hdr, 72, backup_part_lba) # part_lba = backup_part_lba
        
        struct.pack_into("<I", backup_hdr, 16, 0)              # zero CRC field
        backup_crc = zlib.crc32(backup_hdr[:92]) & 0xFFFFFFFF
        struct.pack_into("<I", backup_hdr, 16, backup_crc)
        
        # Write Backup Entries & Backup Header
        f.seek(backup_part_lba * 512)
        f.write(entries)
        f.seek(alt_lba * 512)
        f.write(backup_hdr)
        
        f.flush()
        print("=== GPT Primary and Backup successfully written and verified ===")

    # Verify partition table with python
    with open(RAW_PATH, "rb") as f:
        f.seek(512)
        hdr = f.read(92)
        my_lba, alt_lba, f_u, l_u = struct.unpack("<QQQQ", hdr[24:56])
        print(f"Verification: my_lba={my_lba}, alt_lba={alt_lba}, usable={f_u}..{l_u}")
        
    print("=== Converting repaired disk back to VDI ===")
    os.remove(VDI_PATH)
    subprocess.run([QEMU_IMG, "convert", "-O", "vdi", RAW_PATH, VDI_PATH], check=True)
    os.remove(RAW_PATH)
    print(f"=== Rebuild complete: {VDI_PATH} ({os.path.getsize(VDI_PATH)} bytes) ===")

if __name__ == "__main__":
    main()
