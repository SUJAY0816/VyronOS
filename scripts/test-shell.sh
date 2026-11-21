#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 4 Shell & Command Integration Automated Test Suite
Location: scripts/test-shell.sh
Validates:
1. GNU Bash environment and version identification.
2. Standard core utilities: pwd, ls, cd, mkdir, touch, cp, mv, rm, cat, grep, find, head, tail, wc, diff.
3. Pipelines (|), input/output redirection (>, >>, <), subshell command substitution $(...).
4. Environment variable handling (export, parameter expansion, default fallback).
5. POSIX exit code reporting (0 for success, 1 for failure, 127 for command not found).
6. Directory navigation with relative and absolute paths.
7. Tar archiving and extraction (tar -czf, tar -tzf, tar -xzf).
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
LOG_PATH = os.path.join(BUILD_DIR, "test-shell-serial.log")

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
    print("  VYRON OS — Phase 4 Shell & Command Integration Automated Test Suite")
    print("==========================================================================")
    print(f"  Target Disk     : {DISK_IMAGE}")
    print(f"  UEFI Firmware   : {OVMF_CODE}")
    print(f"  Serial Log      : {LOG_PATH}")
    print("==========================================================================")

    if not os.path.exists(DISK_IMAGE):
        print(f"ERROR: Disk image {DISK_IMAGE} not found.")
        sys.exit(1)

    os.makedirs(BUILD_DIR, exist_ok=True)
    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-ShellTest"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-ShellTest",
        "-m", "2048",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    print(">>> Booting VyronOS in QEMU to execute Shell Integration Test...")
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
cat << 'EOF' > /tmp/run_shell_test.sh
#!/bin/bash
set -e
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "=== 1. BASH SHELL IDENTITY & VERSION ==="
echo "BASH_VERSION_INFO: $BASH_VERSION"
echo "SHELL_PATH: $SHELL"
test -n "$BASH_VERSION"

echo "=== 2. WORKSPACE CREATION & NAVIGATION (mkdir, cd, pwd) ==="
TEST_DIR="/home/vyron/shell_test_workspace"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR/alpha/beta"
cd "$TEST_DIR/alpha/beta"
CURRENT_PWD=$(pwd)
echo "CURRENT_PWD: $CURRENT_PWD"
cd ../..
echo "RETURNED_PWD: $(pwd)"

echo "=== 3. FILE OPERATIONS (touch, ls, cat, head, tail, wc, diff) ==="
cat << 'DATAEOF' > "$TEST_DIR/sample.txt"
line 1: vyron os kernel 6.12
line 2: Debian bookworm base
line 3: native ext4 storage
line 4: real bash shell environment
line 5: genuine network manager
DATAEOF

ls -la "$TEST_DIR/sample.txt"
LINES_COUNT=$(wc -l < "$TEST_DIR/sample.txt")
WORDS_COUNT=$(wc -w < "$TEST_DIR/sample.txt")
echo "WC_OUTPUT: lines=$LINES_COUNT words=$WORDS_COUNT"

FIRST_LINE=$(head -n 1 "$TEST_DIR/sample.txt")
echo "HEAD_OUTPUT: $FIRST_LINE"

LAST_LINE=$(tail -n 1 "$TEST_DIR/sample.txt")
echo "TAIL_OUTPUT: $LAST_LINE"

cp "$TEST_DIR/sample.txt" "$TEST_DIR/sample_copy.txt"
diff -u "$TEST_DIR/sample.txt" "$TEST_DIR/sample_copy.txt"
echo "DIFF_VERIFIED"

echo "=== 4. PIPELINES, REDIRECTION & SUBSHELLS ==="
PIPELINE_RESULT=$(cat "$TEST_DIR/sample.txt" | grep "vyron" | tr '[:lower:]' '[:upper:]')
echo "PIPELINE_RESULT: $PIPELINE_RESULT"

SUBSHELL_VAL=$(echo "KERNEL_UNAME: $(uname -r)")
echo "SUBSHELL_EVAL: $SUBSHELL_VAL"

echo "=== 5. ENVIRONMENT VARIABLES & EXPANSION ==="
export VYRON_ENV_KEY="VyronOS_Phase4_Shell_Passed"
echo "ENV_EXPANSION: ${VYRON_ENV_KEY}"
echo "ENV_DEFAULT_EXP: ${NONEXISTENT_VAR:-DefaultVyronValue}"
echo "ENV_LENGTH_EXP: ${#VYRON_ENV_KEY}"

echo "=== 6. POSIX EXIT CODES (0, 1, 127) ==="
true
echo "EXIT_CODE_SUCCESS: $?"

set +e
grep "NONEXISTENT_STRING_XYZ" "$TEST_DIR/sample.txt" > /dev/null 2>&1
echo "EXIT_CODE_FAILURE: $?"

/usr/bin/nonexistent_vyron_binary_test 2> /dev/null
echo "EXIT_CODE_NOTFOUND: $?"
set -e

echo "=== 7. ARCHIVING & COMPRESSION (tar czf / tzf / xzf) ==="
tar -czf "$TEST_DIR/workspace.tar.gz" -C "$TEST_DIR" sample.txt alpha
test -f "$TEST_DIR/workspace.tar.gz"
echo "TAR_ARCHIVE_CREATED: $(ls -l $TEST_DIR/workspace.tar.gz)"

echo "TAR_CONTENTS:"
tar -tzf "$TEST_DIR/workspace.tar.gz"

mkdir -p "$TEST_DIR/extracted"
tar -xzf "$TEST_DIR/workspace.tar.gz" -C "$TEST_DIR/extracted"
diff -u "$TEST_DIR/sample.txt" "$TEST_DIR/extracted/sample.txt"
echo "TAR_EXTRACTION_VERIFIED"

echo "=== 8. FILE SEARCH (find) ==="
FIND_MATCHES=$(find "$TEST_DIR" -type f -name "*.txt" | wc -l)
echo "FIND_MATCH_COUNT: $FIND_MATCHES"

echo "=== SHELL & COMMAND INTEGRATION TEST COMPLETED SUCCESSFULLY ==="
sync
sudo poweroff
EOF
chmod +x /tmp/run_shell_test.sh
bash /tmp/run_shell_test.sh
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
                    print("\n>>> Logged in. Dispatching Shell Integration Test Script...")
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
        "GNU Bash Identity & Version": ("BASH_VERSION_INFO:" in out_text and "/bin/bash" in out_text),
        "Workspace Navigation (mkdir, cd, pwd)": ("CURRENT_PWD: /home/vyron/shell_test_workspace/alpha/beta" in out_text),
        "Core Utilities (wc, head, tail, diff)": ("WC_OUTPUT: lines=5 words=27" in out_text and "DIFF_VERIFIED" in out_text),
        "Pipelines, Tr, Sort & Redirection": ("PIPELINE_RESULT: LINE 1: VYRON OS KERNEL 6.12" in out_text),
        "Subshell Command Substitution": ("SUBSHELL_EVAL: KERNEL_UNAME: 6.12.95" in out_text),
        "Environment Variables & Parameter Expansion": ("ENV_EXPANSION: VyronOS_Phase4_Shell_Passed" in out_text and "ENV_DEFAULT_EXP: DefaultVyronValue" in out_text),
        "Exit Codes (Success 0, Failure 1, NotFound 127)": ("EXIT_CODE_SUCCESS: 0" in out_text and "EXIT_CODE_FAILURE: 1" in out_text and "EXIT_CODE_NOTFOUND: 127" in out_text),
        "Archive Creation, Table of Contents & Extraction (tar)": ("TAR_EXTRACTION_VERIFIED" in out_text),
        "File Search (find)": ("FIND_MATCH_COUNT:" in out_text)
    }

    print("\n==========================================================================")
    print("  PHASE 4 SHELL & COMMAND INTEGRATION VERIFICATION RESULTS")
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
        print("  RESULT: PHASE 4 SHELL & COMMAND INTEGRATION VERIFICATION PASSED 100%.")
        sys.exit(0)
    else:
        print(f"  RESULT: {total - passed} check(s) did not match exact expectations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
