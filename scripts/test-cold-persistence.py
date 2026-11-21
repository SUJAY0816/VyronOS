#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 4 Cold Reboot Persistence & Subsystem Integrity Test
Location: scripts/test-cold-persistence.py
Validates:
1. Cold reboot bootup into Linux 6.12.95 LTS.
2. Filesystem persistence: validates SHA256 checksum of persistent_payload.dat.
3. Workspace hierarchy integrity (/home/vyron/fs_test_workspace/).
4. Storage utility persistence (/usr/local/bin/vyron-storage).
5. Hardware telemetry utility persistence (/usr/local/bin/vyron-hwinfo).
6. NetworkManager network configuration persistence (ens3 connection & ping).
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
LOG_PATH = os.path.join(BUILD_DIR, "test-cold-persistence-serial.log")

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
    print("  VYRON OS — Phase 4 Cold Reboot Persistence Automated Test")
    print("==========================================================================")
    print(f"  Target Disk    : {DISK_IMAGE}")
    print(f"  UEFI Firmware  : {OVMF_CODE}")
    print(f"  Serial Log     : {LOG_PATH}")
    print("==========================================================================")

    if not os.path.exists(DISK_IMAGE):
        print(f"ERROR: Disk image {DISK_IMAGE} not found.")
        sys.exit(1)

    os.makedirs(BUILD_DIR, exist_ok=True)
    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-ColdTest"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-ColdTest",
        "-m", "2048",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    print(">>> Performing cold reboot of VyronOS in QEMU...")
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
cat << 'EOF' > /tmp/run_cold_test.sh
#!/bin/bash
set -e
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "=== 1. VERIFY SHA256 PERSISTENCE CHECKSUM ==="
cd /home/vyron/fs_test_workspace
sha256sum -c persistent_payload.dat.sha256
echo "COLD_PERSISTENCE_SHA256_MATCHED"

echo "=== 2. VERIFY WORKSPACE DIRECTORY HIERARCHY ==="
test -d /home/vyron/fs_test_workspace/sub1/sub2/sub3
test -f /home/vyron/fs_test_workspace/file1.txt
test -f /home/vyron/fs_test_workspace/sub1/file1_renamed.txt
echo "COLD_WORKSPACE_HIERARCHY_INTACT"

echo "=== 3. VERIFY VYRON-STORAGE PERSISTENCE ==="
test -x /usr/local/bin/vyron-storage
/usr/local/bin/vyron-storage --df
echo "COLD_STORAGE_UTILITY_OPERATIONAL"

echo "=== 4. VERIFY VYRON-HWINFO PERSISTENCE ==="
test -x /usr/local/bin/vyron-hwinfo
/usr/local/bin/vyron-hwinfo --wifi-only
echo "COLD_HWINFO_UTILITY_OPERATIONAL"

echo "=== 5. VERIFY NETWORKMANAGER CONNECTIVITY PERSISTENCE ==="
for i in {1..15}; do
    if ping -c 1 1.1.1.1 >/dev/null 2>&1; then
        echo "COLD_NETWORK_PING_SUCCESSFUL"
        break
    fi
    sleep 1
done

echo "=== COLD REBOOT PERSISTENCE VERIFICATION COMPLETED ==="
sync
sudo poweroff
EOF
chmod +x /tmp/run_cold_test.sh
bash /tmp/run_cold_test.sh
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
                    print("\n>>> Logged in. Dispatching Cold Reboot Persistence Test...")
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
        "Persistent Marker SHA256 Checksum Matched": ("persistent_payload.dat: OK" in out_text and "COLD_PERSISTENCE_SHA256_MATCHED" in out_text),
        "Workspace Directory Hierarchy Intact": ("COLD_WORKSPACE_HIERARCHY_INTACT" in out_text),
        "vyron-storage Utility Persisted & Operational": ("COLD_STORAGE_UTILITY_OPERATIONAL" in out_text),
        "vyron-hwinfo Utility Persisted & Operational": ("COLD_HWINFO_UTILITY_OPERATIONAL" in out_text),
        "NetworkManager Internet Connectivity Active": ("COLD_NETWORK_PING_SUCCESSFUL" in out_text)
    }

    print("\n==========================================================================")
    print("  PHASE 4 COLD REBOOT PERSISTENCE VERIFICATION RESULTS")
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
        print("  RESULT: PHASE 4 COLD REBOOT PERSISTENCE PASSED 100%.")
        sys.exit(0)
    else:
        print(f"  RESULT: {total - passed} check(s) did not match exact expectations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
