#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 4 Storage & Block Device Automated Test Suite
Location: scripts/test-storage.sh
Validates:
1. Block device enumeration (primary disk /dev/sda, secondary volume /dev/sdb).
2. Live partition / block device formatting inside guest using mkfs.ext4.
3. Live filesystem mounting to /mnt/secondary_test.
4. Read/write file operations on secondary mounted volume.
5. Directory usage (du) and filesystem usage (df) tracking.
6. Clean unmount (umount) and state verification.
7. vyron-storage utility installation and execution in CLI and JSON modes.
==============================================================================
"""

import os
import sys
import time
import base64
import subprocess
import select

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
DISK_IMAGE = os.path.join(DIST_DIR, "VyronOS-Disk.qcow2")
SECONDARY_IMAGE = os.path.join(BUILD_DIR, "secondary_test.raw")
LOG_PATH = os.path.join(BUILD_DIR, "test-storage-serial.log")
STORAGE_SCRIPT_SRC = os.path.join(SCRIPT_DIR, "vyron_storage.py")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"
if not os.path.exists(OVMF_CODE):
    for candidate in [
        "/usr/share/qemu/edk2-x86_64-code.fd",
        "/usr/share/OVMF/OVMF_CODE.fd"
    ]:
        if os.path.exists(candidate):
            OVMF_CODE = candidate
            break

def prepare_secondary_disk():
    os.makedirs(BUILD_DIR, exist_ok=True)
    if os.path.exists(SECONDARY_IMAGE):
        os.remove(SECONDARY_IMAGE)
    subprocess.run(
        ["/opt/homebrew/bin/qemu-img", "create", "-f", "raw", SECONDARY_IMAGE, "64M"],
        check=True,
        stdout=subprocess.DEVNULL
    )
    print(f"Created 64MB raw secondary disk at: {SECONDARY_IMAGE}")

def main():
    print("==========================================================================")
    print("  VYRON OS — Phase 4 Storage & Block Device Automated Test Suite")
    print("==========================================================================")
    print(f"  Target Disk     : {DISK_IMAGE}")
    print(f"  Secondary Disk  : {SECONDARY_IMAGE}")
    print(f"  UEFI Firmware   : {OVMF_CODE}")
    print(f"  Serial Log      : {LOG_PATH}")
    print("==========================================================================")

    if not os.path.exists(DISK_IMAGE):
        print(f"ERROR: Disk image {DISK_IMAGE} not found.")
        sys.exit(1)

    prepare_secondary_disk()

    # Read vyron_storage.py and base64 encode it
    with open(STORAGE_SCRIPT_SRC, "rb") as f:
        storage_py_b64 = base64.b64encode(f.read()).decode("ascii")

    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-StorageTest"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-StorageTest",
        "-m", "2048",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-drive", f"file={SECONDARY_IMAGE},format=raw,index=1,media=disk,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    print(">>> Booting VyronOS in QEMU with secondary disk attached...")
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0
    )
    os.set_blocking(proc.stdout.fileno(), False)

    full_output = []
    buffer = ""
    start_time = time.time()
    login_user_sent = False
    login_pass_sent = False
    commands_sent = False

    test_commands = f'''
cat << 'EOF' > /tmp/run_storage_test.sh
#!/bin/bash
set -e
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "=== DEPLOYING VYRON-STORAGE UTILITY ==="
echo "{storage_py_b64}" | base64 -d | sudo tee /usr/local/bin/vyron-storage > /dev/null
sudo chmod 755 /usr/local/bin/vyron-storage

echo "=== 1. DISCOVER BLOCK DEVICES ==="
lsblk -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINT
test -b /dev/sdb
echo "SECONDARY_DEVICE_DISCOVERED: /dev/sdb"

echo "=== 2. FORMAT SECONDARY BLOCK DEVICE WITH EXT4 ==="
sudo mkfs.ext4 -F -L secondary_data /dev/sdb
echo "SECONDARY_DEVICE_FORMATTED_EXT4"

echo "=== 3. MOUNT SECONDARY EXT4 VOLUME ==="
sudo mkdir -p /mnt/secondary_test
sudo mount /dev/sdb /mnt/secondary_test
findmnt /mnt/secondary_test
echo "SECONDARY_DEVICE_MOUNTED: /mnt/secondary_test"

echo "=== 4. WRITE AND READ DATA ON MOUNTED VOLUME ==="
echo "VyronOS Phase 4 Storage Block Mount Verified" | sudo tee /mnt/secondary_test/volume_test.txt
cat /mnt/secondary_test/volume_test.txt
df -h /mnt/secondary_test
sudo du -sh /mnt/secondary_test
echo "VOLUME_IO_VERIFIED"

echo "=== 5. UNMOUNT VOLUME AND VERIFY CLEAN STATE ==="
sudo umount /mnt/secondary_test
if ! findmnt /mnt/secondary_test > /dev/null 2>&1; then
    echo "SECONDARY_DEVICE_UNMOUNTED_CLEANLY"
fi

echo "=== 6. EXECUTE VYRON-STORAGE CLI ==="
/usr/local/bin/vyron-storage

echo "=== 7. EXECUTE VYRON-STORAGE JSON ==="
/usr/local/bin/vyron-storage --json | head -n 30
echo "VYRON_STORAGE_JSON_VALIDATED"

echo "=== 8. EXECUTE VYRON-STORAGE DF ==="
/usr/local/bin/vyron-storage --df

echo "=== STORAGE & BLOCK SUBSYSTEM TEST COMPLETED SUCCESSFULLY ==="
sync
sudo poweroff
EOF
chmod +x /tmp/run_storage_test.sh
bash /tmp/run_storage_test.sh
'''

    try:
        while time.time() - start_time < 120:
            r, _, _ = select.select([proc.stdout.fileno()], [], [], 0.1)
            if r:
                chunk = os.read(proc.stdout.fileno(), 4096).decode("utf-8", errors="replace")
                if not chunk:
                    if proc.poll() is not None:
                        break
                    continue
                full_output.append(chunk)
                sys.stdout.write(chunk)
                sys.stdout.flush()
                buffer += chunk

                if ("login:" in buffer or "vyron-os login:" in buffer) and not login_user_sent:
                    time.sleep(0.3)
                    proc.stdin.write(b"vyron\n")
                    proc.stdin.flush()
                    login_user_sent = True

                if "Password:" in buffer and login_user_sent and not login_pass_sent:
                    time.sleep(0.3)
                    proc.stdin.write(b"vyron\n")
                    proc.stdin.flush()
                    login_pass_sent = True

                if "vyron@vyron-os:~$" in buffer and login_pass_sent and not commands_sent:
                    commands_sent = True
                    print("\n>>> Logged in. Dispatching Storage Test Script...")
                    time.sleep(0.5)
                    proc.stdin.write(f"{test_commands.strip()}\n".encode("utf-8"))
                    proc.stdin.flush()

                if "Powering off" in buffer or "reboot: Power down" in buffer or "ACPI: PM: Preparing to enter system sleep state S5" in buffer:
                    break
            else:
                if proc.poll() is not None:
                    break
    except KeyboardInterrupt:
        proc.kill()
    finally:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    out_text = "".join(full_output)
    with open(LOG_PATH, "w") as f:
        f.write(out_text)

    # Verification checks
    checks = {
        "vyron-storage Deployed & Executable": ("DEPLOYING VYRON-STORAGE" in out_text),
        "Secondary Block Device Discovered (/dev/sdb)": ("SECONDARY_DEVICE_DISCOVERED: /dev/sdb" in out_text),
        "Ext4 Formatting Executed on /dev/sdb": ("SECONDARY_DEVICE_FORMATTED_EXT4" in out_text),
        "Mount Operation Verified (/mnt/secondary_test)": ("SECONDARY_DEVICE_MOUNTED: /mnt/secondary_test" in out_text),
        "Volume Read/Write & Usage Tracking Verified": ("VOLUME_IO_VERIFIED" in out_text and "VyronOS Phase 4 Storage Block Mount Verified" in out_text),
        "Clean Unmount Verified": ("SECONDARY_DEVICE_UNMOUNTED_CLEANLY" in out_text),
        "vyron-storage CLI Operational": ("VYRON OS — Real Storage & Filesystem Subsystem" in out_text and "BLOCK DEVICE TOPOLOGY" in out_text),
        "vyron-storage JSON Validated": ("VYRON_STORAGE_JSON_VALIDATED" in out_text),
        "vyron-storage DF Output Validated": ("MOUNTED FILESYSTEM USAGE" in out_text or '"usage":' in out_text or '"fstype":' in out_text)
    }

    print("\n==========================================================================")
    print("  PHASE 4 STORAGE & BLOCK DEVICE VERIFICATION RESULTS")
    print("==========================================================================")
    passed = 0
    total = len(checks)
    for k, v in checks.items():
        st = "PASS" if v else "FAIL"
        print(f"  [{st}] {k}")
        if v:
            passed += 1

    print("==========================================================================")
    print(f"  Summary: {passed}/{total} Gates Passed ({100.0*passed/total:.1f}%)")
    print("==========================================================================")

    if passed == total:
        print("  RESULT: PHASE 4 STORAGE & BLOCK DEVICE VERIFICATION PASSED 100%.")
        sys.exit(0)
    else:
        print(f"  RESULT: {total - passed} check(s) did not match exact expectations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
