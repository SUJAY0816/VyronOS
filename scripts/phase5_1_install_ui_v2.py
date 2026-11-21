#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 5.1 Vyron UI V2 Installer
Target Disk: dist/VyronOS-Disk-Phase5.1-Working.qcow2
Deploys:
1. Vyron-V2-Dark and Vyron-V2-Light GTK3 & XFWM4 Themes.
2. Vyron-V2-Icons squircle icon family (SVG + PNGs + index.theme).
3. 1920x1080 flowing gradient wallpapers (Dark, Light, Bootsplash, Logo).
4. Dual-panel XFCE 4.18 layout:
   - 36px clean Top Bar (Vyron logo, workspace pills, active window, centered clock, systray, power).
   - 68px floating Centered Dock (48px squircle icons for all primary apps).
5. Terminalrc with Vyron UI V2 midnight palette.
6. Overhauled Vyron System Monitor (COSMIC-inspired GTK3 cards).
7. Updated Vyron Theme Engine for V2 dual themes.
8. LightDM GTK greeter configuration.
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
WORKING_DISK = os.path.join(DIST_DIR, "VyronOS-Disk-Phase5.1-Working.qcow2")
TARBALL_PATH = os.path.join(BUILD_DIR, "ui_v2_package.tar.gz")
LOG_PATH = os.path.join(BUILD_DIR, "phase5_1-install-serial.log")

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
    print("  VYRON OS — Phase 5.1 Vyron UI V2 Desktop Stack Deployment")
    print("==========================================================================")
    print(f"  Target Disk   : {WORKING_DISK}")
    print(f"  Package Tar   : {TARBALL_PATH}")
    print(f"  UEFI Firmware : {OVMF_CODE}")
    print(f"  Log File      : {LOG_PATH}")
    print("==========================================================================")

    if not os.path.exists(WORKING_DISK):
        print(f"ERROR: Working disk {WORKING_DISK} not found.")
        sys.exit(1)
    if not os.path.exists(TARBALL_PATH):
        print(f"ERROR: UI V2 package tarball {TARBALL_PATH} not found.")
        sys.exit(1)

    with open(TARBALL_PATH, "rb") as f:
        pkg_b64 = base64.b64encode(f.read()).decode("ascii")

    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-P51Install"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-P51Install",
        "-m", "2048",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={WORKING_DISK},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    print(">>> Booting VyronOS to deploy Phase 5.1 Vyron UI V2...")
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
    deploy_started = False

    installer_script = """
cat << 'DEPLOY_SCRIPT' > /tmp/run_p51_deploy.sh
#!/bin/bash
set -e
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "=== 1. DECODING & EXTRACTING UI V2 ASSETS ==="
mkdir -p /tmp/ui_v2_extracted
tar -xzf /tmp/ui_v2_pkg.tar.gz -C /tmp/ui_v2_extracted

echo "=== 2. DEPLOYING GTK3 & XFWM4 THEMES ==="
sudo mkdir -p /usr/share/themes
sudo cp -r /tmp/ui_v2_extracted/themes/Vyron-V2-Dark /usr/share/themes/
sudo cp -r /tmp/ui_v2_extracted/themes/Vyron-V2-Light /usr/share/themes/

echo "=== 3. DEPLOYING VYRON-V2-ICONS THEME ==="
sudo mkdir -p /usr/share/icons
sudo cp -r /tmp/ui_v2_extracted/icons/Vyron-V2-Icons /usr/share/icons/
sudo gtk-update-icon-cache -f /usr/share/icons/Vyron-V2-Icons || true

echo "=== 4. DEPLOYING WALLPAPERS & BRANDING ==="
sudo mkdir -p /usr/share/backgrounds
sudo cp /tmp/ui_v2_extracted/wallpapers/vyron-dark.png /usr/share/backgrounds/
sudo cp /tmp/ui_v2_extracted/wallpapers/vyron-light.png /usr/share/backgrounds/
sudo cp /tmp/ui_v2_extracted/wallpapers/vyron-bootsplash.png /usr/share/backgrounds/
sudo cp /tmp/ui_v2_extracted/wallpapers/vyron-logo.png /usr/share/icons/

echo "=== 5. DEPLOYING SYSTEM MONITOR & THEME ENGINE ==="
sudo cp /tmp/ui_v2_extracted/vyron_sysmon.py /usr/local/bin/vyron-sysmon
sudo chmod 755 /usr/local/bin/vyron-sysmon
sudo cp /tmp/ui_v2_extracted/vyron_theme.py /usr/local/bin/vyron-theme
sudo chmod 755 /usr/local/bin/vyron-theme

echo "=== 6. DEPLOYING DESKTOP APPLICATION SHORTCUTS ==="
sudo cp /tmp/ui_v2_extracted/applications/*.desktop /usr/share/applications/

echo "=== 7. DEPLOYING XFCE 4.18 DUAL-PANEL PROFILE ==="
mkdir -p /home/vyron/.config/xfce4/xfconf/xfce-perchannel-xml
mkdir -p /home/vyron/.config/xfce4/terminal
mkdir -p /home/vyron/.config/gtk-3.0
mkdir -p /home/vyron/.config/vyron

cp /tmp/ui_v2_extracted/xfce4/xfconf/xfce-perchannel-xml/* /home/vyron/.config/xfce4/xfconf/xfce-perchannel-xml/
cp /tmp/ui_v2_extracted/xfce4/terminal/terminalrc /home/vyron/.config/xfce4/terminal/
cp /tmp/ui_v2_extracted/themes/Vyron-V2-Dark/gtk-3.0/gtk.css /home/vyron/.config/gtk-3.0/gtk.css
echo "dark" > /home/vyron/.config/vyron/theme.state

echo "=== 8. CONFIGURING LIGHTDM GREETER ==="
sudo mkdir -p /etc/lightdm
sudo cp /tmp/ui_v2_extracted/lightdm/lightdm-gtk-greeter.conf /etc/lightdm/

chown -R vyron:vyron /home/vyron/.config

echo "=== 9. RE-TESTING LOCAL THEME ENGINE & SYSMON ==="
/usr/local/bin/vyron-theme --json
/usr/local/bin/vyron-sysmon --cli

echo "=== PHASE 5.1 VYRON UI V2 DEPLOYMENT SUCCESSFUL ==="
sync
sudo poweroff
DEPLOY_SCRIPT
chmod +x /tmp/run_p51_deploy.sh
"""

    try:
        while time.time() - start_time < 900:
            r, _, _ = select.select([proc.stdout.fileno()], [], [], 0.1)
            if r:
                chunk = os.read(proc.stdout.fileno(), 4096).decode("utf-8", errors="replace")
                if not chunk:
                    if proc.poll() is not None:
                        break
                    time.sleep(0.05)
                    continue
                sys.stdout.write(chunk)
                sys.stdout.flush()
                buffer += chunk
                full_output.append(chunk)

                # Step 1: Detect username prompt
                if ("login:" in buffer or "vyron-os login:" in buffer) and not login_user_sent:
                    print("\n>>> Detected login prompt! Sending username 'vyron'...")
                    time.sleep(0.5)
                    proc.stdin.write(b"vyron\n")
                    proc.stdin.flush()
                    login_user_sent = True
                    buffer = ""

                # Step 2: Detect password prompt
                elif ("Password:" in buffer or "password:" in buffer) and login_user_sent and not login_pass_sent:
                    print("\n>>> Detected password prompt! Sending password 'vyron'...")
                    time.sleep(0.5)
                    proc.stdin.write(b"vyron\n")
                    proc.stdin.flush()
                    login_pass_sent = True
                    buffer = ""

                # Step 3: Logged in, send deployment package
                elif ("vyron@vyron-os:" in buffer or "$" in buffer) and login_pass_sent and not deploy_started:
                    print("\n>>> Logged in successfully! Uploading UI V2 package base64...")
                    deploy_started = True
                    buffer = ""
                    time.sleep(1)

                    # Stream base64 in 2048-byte chunks
                    proc.stdin.write(b"rm -f /tmp/ui_v2.b64 /tmp/ui_v2_pkg.tar.gz\n")
                    proc.stdin.flush()
                    time.sleep(0.5)

                    chunk_size = 2048
                    total_chunks = (len(pkg_b64) + chunk_size - 1) // chunk_size
                    for idx in range(total_chunks):
                        c = pkg_b64[idx * chunk_size:(idx + 1) * chunk_size]
                        cmd_line = f"cat << 'EOC' >> /tmp/ui_v2.b64\n{c}\nEOC\n"
                        proc.stdin.write(cmd_line.encode("ascii"))
                        proc.stdin.flush()
                        time.sleep(0.02)
                        if idx % 50 == 0:
                            print(f"  Streaming package: {idx+1}/{total_chunks} chunks...")

                    print(">>> Decoding base64 package in guest...")
                    proc.stdin.write(b"base64 -d /tmp/ui_v2.b64 > /tmp/ui_v2_pkg.tar.gz\n")
                    proc.stdin.flush()
                    time.sleep(1)

                    print(">>> Executing deployment script...")
                    proc.stdin.write(installer_script.encode("utf-8"))
                    proc.stdin.write(b"bash /tmp/run_p51_deploy.sh\n")
                    proc.stdin.flush()

        proc.wait(timeout=30)
    except Exception as e:
        print(f"Exception during deployment: {e}")
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)

    with open(LOG_PATH, "w") as f:
        f.write("".join(full_output))

    out_text = "".join(full_output)
    if "PHASE 5.1 VYRON UI V2 DEPLOYMENT SUCCESSFUL" in out_text:
        print("\n==========================================================================")
        print("  SUCCESS: Phase 5.1 Vyron UI V2 Deployed to Working Disk!")
        print("==========================================================================")
        return 0
    else:
        print("\n==========================================================================")
        print("  ERROR: Deployment did not complete successfully. Check log:")
        print(f"  {LOG_PATH}")
        print("==========================================================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())
