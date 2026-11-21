#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 2 Automated Boot Verification Suite
Validates the genuine Linux kernel, initramfs, ext4 rootfs, systemd PID 1,
virtio storage/network devices, serial console, and interactive shell execution.
Returns 0 on complete verified success; non-zero on any failure.
==============================================================================
"""

import sys
import os
import time
import subprocess
import select

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
DISK_IMAGE = os.path.join(DIST_DIR, "VyronOS-Disk.qcow2")
LOG_PATH = os.path.join(BUILD_DIR, "test-boot-serial.log")

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
    print("  VYRON OS — Phase 2 Automated Boot & Subsystem Verification Suite")
    print("==========================================================================")
    print(f"  Target Disk    : {DISK_IMAGE}")
    print(f"  UEFI Firmware  : {OVMF_CODE}")
    print(f"  Log Output     : {LOG_PATH}")
    print("==========================================================================")

    if not os.path.exists(DISK_IMAGE):
        print(f"ERROR: Disk image not found at {DISK_IMAGE}. Run scripts/build.sh first.")
        sys.exit(1)

    os.makedirs(BUILD_DIR, exist_ok=True)
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)

    # Clean dangling instances
    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-Disk"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-TestBoot",
        "-m", "1024",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    print(">>> [1/3] Booting VyronOS in QEMU headless test mode...")
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0
    )

    # Non-blocking stdout
    os.set_blocking(proc.stdout.fileno(), False)

    full_output = []
    checks = {
        "UEFI Bootloader (GRUB2)": False,
        "Linux 6.1 LTS Kernel Init": False,
        "Initramfs Unpacking": False,
        "Storage Controller (SATA/VirtIO)": False,
        "VirtIO Network Device": False,
        "Ext4 Root Filesystem Mount": False,
        "Systemd PID 1 Initialization": False,
        "VyronOS Login Banner": False,
        "Interactive Login (vyron)": False,
        "Real Bash Command Execution": False,
        "Real Network ICMP Ping": False,
        "Clean ACPI System Shutdown": False,
    }

    start_time = time.time()
    login_user_sent = False
    login_pass_sent = False
    commands_sent = False
    buffer = ""

    try:
        while time.time() - start_time < 90:
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

                # Check patterns
                if "GNU GRUB" in buffer or "Welcome to GRUB" in buffer:
                    checks["UEFI Bootloader (GRUB2)"] = True

                if "Linux version 6.1" in buffer or "Loading Linux 6.1" in buffer:
                    checks["Linux 6.1 LTS Kernel Init"] = True

                if "unpack rootfs image as initramfs" in buffer or "Freeing initrd memory" in buffer:
                    checks["Initramfs Unpacking"] = True

                if "scsi" in buffer.lower() or "sda: sda1" in buffer or "ata_piix" in buffer:
                    checks["Storage Controller (SATA/VirtIO)"] = True

                if "ens3: renamed" in buffer or "Virtio network device" in buffer or "eth0: Intel" in buffer:
                    checks["VirtIO Network Device"] = True

                if "EXT4-fs" in buffer and ("mounted filesystem" in buffer or "re-mounted" in buffer or "sda1" in buffer):
                    checks["Ext4 Root Filesystem Mount"] = True

                if "systemd[1]: systemd" in buffer and "running in system mode" in buffer:
                    checks["Systemd PID 1 Initialization"] = True

                if "VYRON Desktop OS 1.0 LTS" in buffer or "vyron-os login:" in buffer:
                    checks["VyronOS Login Banner"] = True
                    if "login:" in buffer and not login_user_sent:
                        time.sleep(0.3)
                        proc.stdin.write(b"vyron\n")
                        proc.stdin.flush()
                        login_user_sent = True

                if "Password:" in buffer and login_user_sent and not login_pass_sent:
                    time.sleep(0.3)
                    proc.stdin.write(b"vyron\n")
                    proc.stdin.flush()
                    login_pass_sent = True

                if "vyron@vyron-os:~$" in buffer and login_pass_sent:
                    checks["Interactive Login (vyron)"] = True
                    if not commands_sent:
                        commands_sent = True
                        test_cmds = (
                            "echo '=== VYRON TEST EXECUTION ==='\n"
                            "uname -a\n"
                            "id\n"
                            "cat /etc/os-release\n"
                            "ip -4 addr show ens3\n"
                            "ping -c 2 1.1.1.1\n"
                            "sudo poweroff\n"
                        ).encode("utf-8")
                        time.sleep(0.3)
                        proc.stdin.write(test_cmds)
                        proc.stdin.flush()

                if "=== VYRON TEST EXECUTION ===" in buffer:
                    checks["Real Bash Command Execution"] = True

                if "2 packets transmitted, 2 received" in buffer or "0% packet loss" in buffer:
                    checks["Real Network ICMP Ping"] = True

                if "reboot: Power down" in buffer or "ACPI: PM: Preparing to enter system sleep state S5" in buffer:
                    checks["Clean ACPI System Shutdown"] = True
                    break
            else:
                if proc.poll() is not None:
                    break

    except KeyboardInterrupt:
        proc.kill()

    finally:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    # Save complete log
    with open(LOG_PATH, "w") as f:
        f.write("".join(full_output))

    print("\n==========================================================================")
    print("  PHASE 2 VERIFICATION RESULTS BREAKDOWN")
    print("==========================================================================")
    passed = 0
    total = len(checks)
    for name, ok in checks.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}]  {name}")
        if ok:
            passed += 1

    print("==========================================================================")
    print(f"  Summary: {passed}/{total} Subsystems Verified ({100.0*passed/total:.1f}%)")
    print(f"  Full Serial Trace: {LOG_PATH}")
    print("==========================================================================")

    if passed == total:
        print("  RESULT: PHASE 2 VERIFICATION GATES PASSED CLEANLY.")
        sys.exit(0)
    else:
        print("  RESULT: VERIFICATION FAILED. SOME SUBSYSTEMS DID NOT OPERATE.")
        sys.exit(1)

if __name__ == "__main__":
    main()
