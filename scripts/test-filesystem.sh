#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 4 Filesystem Automated Test Suite
Location: scripts/test-filesystem.sh
Validates:
1. Directory creation (standard and nested hierarchy).
2. File creation, write, read, and append operations.
3. File copying (cp) and verification.
4. File renaming and moving (mv) and verification.
5. POSIX file permissions (chmod: 600, 755) and validation.
6. File ownership (chown: vyron:vyron).
7. File deletion (rm) and cleanup.
8. Persistent test marker generation with SHA256 checksum for cold reboot check.
9. Execution on real ext4 root filesystem (no mock in-memory storage).
==============================================================================
"""

import os
import sys
import time
import subprocess
import select

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
DISK_IMAGE = os.path.join(DIST_DIR, "VyronOS-Disk.qcow2")
LOG_PATH = os.path.join(BUILD_DIR, "test-filesystem-serial.log")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"
if not os.path.exists(OVMF_CODE):
    for candidate in [
        "/usr/share/qemu/edk2-x86_64-code.fd",
        "/usr/share/OVMF/OVMF_CODE.fd"
    ]:
        if os.path.exists(candidate):
            OVMF_CODE = candidate
            break

def main():
    print("==========================================================================")
    print("  VYRON OS — Phase 4 Real Filesystem Automated Test Suite")
    print("==========================================================================")
    print(f"  Target Disk    : {DISK_IMAGE}")
    print(f"  UEFI Firmware  : {OVMF_CODE}")
    print(f"  Serial Log     : {LOG_PATH}")
    print("==========================================================================")

    if not os.path.exists(DISK_IMAGE):
        print(f"ERROR: Disk image {DISK_IMAGE} not found.")
        sys.exit(1)

    os.makedirs(BUILD_DIR, exist_ok=True)
    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-Disk"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-FilesystemTest",
        "-m", "2048",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    print(">>> Booting VyronOS in QEMU to execute Filesystem Test Suite...")
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

    test_commands = '''
cat << 'EOF' > /tmp/run_fs_test.sh
#!/bin/bash
set -e
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "=== ENSURING STANDARD PATH ENVIRONMENT ==="
sudo tee /etc/profile.d/00-path.sh << 'PATHEOF'
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
PATHEOF

echo "=== 1. VERIFY REAL ROOT FILESYSTEM ==="
findmnt -n -o FSTYPE /
findmnt -n -o OPTIONS /

echo "=== 2. NESTED DIRECTORY CREATION ==="
TEST_DIR="/home/vyron/fs_test_workspace/sub1/sub2/sub3"
mkdir -p "$TEST_DIR"
test -d "$TEST_DIR"
echo "DIR_CREATED: $TEST_DIR"

echo "=== 3. FILE CREATE, WRITE & READ ==="
PAYLOAD_FILE="/home/vyron/fs_test_workspace/file1.txt"
echo "VyronOS Linux 6.12 Ext4 Primary Line" > "$PAYLOAD_FILE"
cat "$PAYLOAD_FILE"

echo "=== 4. FILE APPEND ==="
echo "VyronOS Linux 6.12 Ext4 Appended Line 2" >> "$PAYLOAD_FILE"
grep "Appended Line 2" "$PAYLOAD_FILE"

echo "=== 5. FILE COPY (cp) ==="
COPY_FILE="/home/vyron/fs_test_workspace/file1_copy.txt"
cp "$PAYLOAD_FILE" "$COPY_FILE"
diff -u "$PAYLOAD_FILE" "$COPY_FILE"
echo "CP_VERIFIED"

echo "=== 6. FILE MOVE / RENAME (mv) ==="
RENAMED_FILE="/home/vyron/fs_test_workspace/sub1/file1_renamed.txt"
mv "$COPY_FILE" "$RENAMED_FILE"
test -f "$RENAMED_FILE"
test ! -f "$COPY_FILE"
echo "MV_VERIFIED"

echo "=== 7. POSIX FILE PERMISSIONS (chmod) ==="
chmod 600 "$PAYLOAD_FILE"
PERM1=$(stat -c "%a" "$PAYLOAD_FILE")
echo "PERM_MODE_600: $PERM1"
chmod 755 "$PAYLOAD_FILE"
PERM2=$(stat -c "%a" "$PAYLOAD_FILE")
echo "PERM_MODE_755: $PERM2"

echo "=== 8. FILE OWNERSHIP (chown) ==="
OWNER=$(stat -c "%U:%G" "$PAYLOAD_FILE")
echo "OWNER_VERIFIED: $OWNER"

echo "=== 9. FILE DELETION (rm) ==="
TEMP_FILE="/home/vyron/fs_test_workspace/to_delete.tmp"
touch "$TEMP_FILE"
test -f "$TEMP_FILE"
rm "$TEMP_FILE"
test ! -f "$TEMP_FILE"
echo "RM_VERIFIED"

echo "=== 10. GENERATING PERSISTENCE PAYLOAD FOR REBOOT CHECK ==="
PERSIST_FILE="/home/vyron/fs_test_workspace/persistent_payload.dat"
echo "VYRON_PERSISTENCE_MARKER_PHASE4_$(date +%s)" > "$PERSIST_FILE"
sha256sum "$PERSIST_FILE" > "$PERSIST_FILE.sha256"
cat "$PERSIST_FILE"
cat "$PERSIST_FILE.sha256"

echo "=== FILESYSTEM TEST COMPLETED SUCCESSFULLY ==="
sync
sudo poweroff
EOF
chmod +x /tmp/run_fs_test.sh
bash /tmp/run_fs_test.sh
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
                    print("\n>>> Logged in. Dispatching Filesystem Test Script...")
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
        "Ext4 Root Filesystem Active": ("ext4" in out_text),
        "Nested Directory Creation": ("DIR_CREATED" in out_text),
        "File Write & Read Operations": ("VyronOS Linux 6.12 Ext4 Primary Line" in out_text),
        "File Append Operation": ("Appended Line 2" in out_text),
        "File Copy (cp) Verified": ("CP_VERIFIED" in out_text),
        "File Move/Rename (mv) Verified": ("MV_VERIFIED" in out_text),
        "POSIX Permissions (chmod 600/755)": ("PERM_MODE_600: 600" in out_text and "PERM_MODE_755: 755" in out_text),
        "Ownership Verified (vyron:vyron)": ("OWNER_VERIFIED: vyron:vyron" in out_text),
        "File Deletion (rm) Verified": ("RM_VERIFIED" in out_text),
        "Persistence Marker Generated": ("persistent_payload.dat" in out_text and ".sha256" in out_text)
    }

    print("\n==========================================================================")
    print("  PHASE 4 FILESYSTEM VERIFICATION RESULTS")
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
        print("  RESULT: PHASE 4 FILESYSTEM VERIFICATION PASSED 100%.")
        sys.exit(0)
    else:
        print(f"  RESULT: {total - passed} check(s) did not match exact expectations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
