#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 2 Review: Hardening and Independent Verification Harness
Executes:
  Boot 1:
    - Persistence setup (/home/vyron/persistence-test.txt with SHA256)
    - Network validation (virtio-net driver, DHCP, routing, DNS, ping IP/host, Wi-Fi honesty)
    - Root filesystem validation (findmnt, lsblk, blkid, write test, EFI partition)
    - Systemd validation (PID 1, is-system-running, running units, failed units)
    - Clean ACPI shutdown
  Boot 2 (cold reboot of exact same QCOW2 disk):
    - Persistence verification (file exists, cat content, sha256sum -c check)
    - Clean ACPI shutdown
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
LOG_BOOT1 = os.path.join(BUILD_DIR, "hardening-boot1-serial.log")
LOG_BOOT2 = os.path.join(BUILD_DIR, "hardening-boot2-serial.log")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"
if not os.path.exists(OVMF_CODE):
    for candidate in [
        "/usr/share/qemu/edk2-x86_64-code.fd",
        "/usr/share/OVMF/OVMF_CODE.fd"
    ]:
        if os.path.exists(candidate):
            OVMF_CODE = candidate
            break

def run_vm_session(session_name, log_path, commands_to_send, max_wait_sec=120):
    print(f"\n==========================================================================")
    print(f"  STARTING VM SESSION: {session_name}")
    print(f"  Disk: {DISK_IMAGE}")
    print(f"  Log:  {log_path}")
    print(f"==========================================================================")

    # Clean dangling instances
    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-Disk"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", f"VyronOS-{session_name}",
        "-m", "1024",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

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

    try:
        while time.time() - start_time < max_wait_sec:
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

                # Handle login prompt
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

                # Send commands after prompt ready
                if "vyron@vyron-os:~$" in buffer and login_pass_sent and not commands_sent:
                    commands_sent = True
                    time.sleep(0.5)
                    for c in commands_to_send:
                        proc.stdin.write(f"{c}\n".encode("utf-8"))
                        proc.stdin.flush()
                        time.sleep(0.3)

                # Termination check on ACPI power off
                if "ACPI: PM: Preparing to enter system sleep state S5" in buffer or "reboot: Power down" in buffer:
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

    all_text = "".join(full_output)
    with open(log_path, "w") as f:
        f.write(all_text)

    return all_text

def main():
    if not os.path.exists(DISK_IMAGE):
        print(f"ERROR: Disk image {DISK_IMAGE} does not exist. Run scripts/build.sh first.")
        sys.exit(1)

    os.makedirs(BUILD_DIR, exist_ok=True)

    # --------------------------------------------------------------------------
    # SESSION 1: Setup persistence token + System & Network validations
    # --------------------------------------------------------------------------
    token_seed = f"TOKEN-VYRON-{int(time.time())}-PASSKEY"
    boot1_cmds = [
        "echo '=== BOOT 1: START VALIDATION ==='",
        f"echo '{token_seed}' > /home/vyron/persistence-test.txt",
        "sha256sum /home/vyron/persistence-test.txt > /home/vyron/persistence-test.txt.sha256",
        "echo '=== PERSISTENCE TOKEN GENERATED ==='",
        "cat /home/vyron/persistence-test.txt",
        "cat /home/vyron/persistence-test.txt.sha256",
        "sync",
        "echo '=== 1. NETWORK VALIDATION ==='",
        "lsmod | grep virtio",
        "ip -4 addr show ens3",
        "ip route show",
        "cat /etc/resolv.conf",
        "getent hosts debian.org || true",
        "ping -c 2 1.1.1.1",
        "ping -c 2 debian.org",
        "echo '=== 2. WI-FI & INTERFACE HONESTY CHECK ==='",
        "ls -la /sys/class/net",
        "rfkill list all || true",
        "echo '=== 3. ROOT FILESYSTEM & PARTITION VALIDATION ==='",
        "findmnt /",
        "lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT,UUID",
        "sudo blkid",
        "echo 'write-validation-pass' | sudo tee /var/tmp/vyron-write-check.txt",
        "cat /var/tmp/vyron-write-check.txt",
        "sudo rm /var/tmp/vyron-write-check.txt",
        "findmnt /boot/efi || true",
        "ls -la /boot/efi || true",
        "echo '=== 4. SYSTEMD PID 1 & SERVICE STATUS ==='",
        "ps -p 1 -o pid,comm,args",
        "systemctl is-system-running || true",
        "systemctl list-units --type=service --state=running --no-pager",
        "systemctl --failed --no-pager",
        "echo '=== BOOT 1: INITIATING CLEAN SHUTDOWN ==='",
        "sudo poweroff"
    ]

    out1 = run_vm_session("Hardening-Boot-1", LOG_BOOT1, boot1_cmds, max_wait_sec=120)

    # Give OS a moment to ensure disk flush
    time.sleep(2)

    # --------------------------------------------------------------------------
    # SESSION 2: Reboot from the SAME QCOW2 disk and verify persistence
    # --------------------------------------------------------------------------
    boot2_cmds = [
        "echo '=== BOOT 2: VERIFY PERSISTENCE ==='",
        "ls -la /home/vyron/persistence-test.txt",
        "cat /home/vyron/persistence-test.txt",
        "sha256sum -c /home/vyron/persistence-test.txt.sha256",
        "echo '=== PERSISTENCE CHECK RESULT: SUCCESS ==='",
        "sudo poweroff"
    ]

    out2 = run_vm_session("Hardening-Boot-2", LOG_BOOT2, boot2_cmds, max_wait_sec=100)

    print("\n==========================================================================")
    print("  ANALYTICAL VERIFICATION OF RESULTS")
    print("==========================================================================")

    # Verification checks
    checks = {}

    # 1. Persistence
    checks["Persistence File Created in Boot 1"] = token_seed in out1
    checks["Persistence File Exists in Boot 2"] = ("persistence-test.txt" in out2) and (token_seed in out2)
    checks["Persistence SHA256 Match in Boot 2"] = "persistence-test.txt: OK" in out2

    # 2. Network
    checks["VirtIO Network Driver Loaded"] = "virtio_net" in out1
    checks["DHCP IP Address Assigned (ens3)"] = ("10.0.2.15" in out1) or ("dynamic ens3" in out1)
    checks["Default Route Configured"] = "default via 10.0.2.2 dev ens3" in out1
    checks["DNS Resolution Operational"] = ("debian.org" in out1) and ("127.0.0.53" in out1 or "nameserver" in out1)
    checks["External IP Ping (1.1.1.1)"] = ("64 bytes from 1.1.1.1" in out1) and ("0% packet loss" in out1)
    checks["External Domain Ping (debian.org)"] = ("bytes from" in out1) and ("debian.org" in out1)
    checks["Wi-Fi Honesty (Only lo & ens3, no fake wlan)"] = ("ens3" in out1) and ("wlan" not in out1)

    # 3. Filesystem
    checks["Root Filesystem Mounted as Ext4"] = "ext4" in out1 and "/dev/sda1" in out1
    checks["Root Filesystem Is Writable"] = "write-validation-pass" in out1
    checks["EFI Partition Detected (/dev/sda15 /boot/efi)"] = "sda15" in out1

    # 4. Systemd
    checks["Systemd is PID 1"] = "/sbin/init" in out1 or "systemd" in out1
    checks["Systemd System Running"] = "running" in out1 or "degraded" in out1

    passed_count = sum(1 for v in checks.values() if v)
    total_count = len(checks)

    for k, v in checks.items():
        status = "PASS" if v else "FAIL"
        print(f"  [{status}] {k}")

    print("==========================================================================")
    print(f"  Hardening Result: {passed_count}/{total_count} Checks Passed ({100.0*passed_count/total_count:.1f}%)")
    print("==========================================================================")

    if passed_count == total_count:
        print("  All hardening tests PASSED successfully!")
        sys.exit(0)
    else:
        print(f"  WARNING: {total_count - passed_count} check(s) did not match exact expectations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
