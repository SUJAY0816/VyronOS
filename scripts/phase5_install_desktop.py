#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — Phase 5 Desktop & GUI Stack Installer
Location: scripts/phase5_install_desktop.py
Installs Xorg, LightDM, XFCE4, Thunar, XFCE Terminal, Greybird themes.
Deploys custom Vyron wallpapers, icons, vyron-theme, and vyron-sysmon.
Configures LightDM autologin and hybrid macOS+Windows panel layout.
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
LOG_PATH = os.path.join(BUILD_DIR, "phase5-install-serial.log")

DARK_WP_SRC = os.path.join(BUILD_DIR, "wallpapers", "vyron-dark.png")
LIGHT_WP_SRC = os.path.join(BUILD_DIR, "wallpapers", "vyron-light.png")
LOGO_SRC = os.path.join(BUILD_DIR, "wallpapers", "vyron-logo.png")
THEME_PY_SRC = os.path.join(SCRIPT_DIR, "vyron_theme.py")
SYSMON_PY_SRC = os.path.join(SCRIPT_DIR, "vyron_sysmon.py")

OVMF_CODE = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"
if not os.path.exists(OVMF_CODE):
    for candidate in [
        "/usr/share/qemu/edk2-x86_64-code.fd",
        "/usr/share/OVMF/OVMF_CODE.fd"
    ]:
        if os.path.exists(candidate):
            OVMF_CODE = candidate
            break

def b64_file(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

def main():
    print("==========================================================================")
    print("  VYRON OS — Phase 5 Desktop Environment & GUI Installer")
    print("==========================================================================")
    print(f"  Target Disk   : {DISK_IMAGE}")
    print(f"  UEFI Firmware : {OVMF_CODE}")
    print(f"  Log File      : {LOG_PATH}")
    print("==========================================================================")

    if not os.path.exists(DISK_IMAGE):
        print(f"ERROR: Disk image {DISK_IMAGE} not found.")
        sys.exit(1)

    dark_b64 = b64_file(DARK_WP_SRC)
    light_b64 = b64_file(LIGHT_WP_SRC)
    logo_b64 = b64_file(LOGO_SRC)
    theme_b64 = b64_file(THEME_PY_SRC)
    sysmon_b64 = b64_file(SYSMON_PY_SRC)

    os.makedirs(BUILD_DIR, exist_ok=True)
    subprocess.run(["pkill", "-f", "qemu-system-x86_64.*VyronOS-P5Install"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    cmd = [
        "/opt/homebrew/bin/qemu-system-x86_64",
        "-name", "VyronOS-P5Install",
        "-m", "2048",
        "-smp", "2",
        "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
        "-drive", f"file={DISK_IMAGE},format=qcow2,file.locking=off",
        "-netdev", "user,id=net0,hostname=vyron-os",
        "-device", "virtio-net-pci,netdev=net0",
        "-display", "none",
        "-serial", "stdio"
    ]

    print(">>> Booting VyronOS in QEMU to execute Desktop Stack Installation...")
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

    installer_script = f'''
cat << 'EOF' > /tmp/run_p5_install.sh
#!/bin/bash
set -e
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

echo "=== 1. VERIFYING INTERNET CONNECTIVITY ==="
for i in {{1..15}}; do
    if ping -c 1 1.1.1.1 >/dev/null 2>&1; then
        echo "NETWORK_ONLINE_CONFIRMED"
        break
    fi
    sleep 1
done

echo "=== ENSURING CLEAN DPKG STATE ==="
sudo rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock
sudo dpkg --configure -a || true

echo "=== 2. UPDATING APT PACKAGE REPOSITORIES ==="
sudo apt-get update

echo "=== 3. INSTALLING XORG, LIGHTDM, XFCE4 & CORE GUI PACKAGES ==="
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    xserver-xorg-core \
    xserver-xorg-video-all \
    xserver-xorg-input-all \
    xinit \
    x11-xserver-utils \
    lightdm \
    lightdm-gtk-greeter \
    xfce4-session \
    xfwm4 \
    xfce4-panel \
    xfdesktop4 \
    xfce4-settings \
    xfce4-terminal \
    thunar \
    xfce4-whiskermenu-plugin \
    greybird-gtk-theme \
    adwaita-icon-theme \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    libglib2.0-bin \
    xdotool \
    xterm \
    dbus-x11

echo "=== 4. CLEANING APT CACHE ==="
sudo apt-get clean
df -h /

echo "=== 5. DEPLOYING WALLPAPERS & BRANDING ==="
sudo mkdir -p /usr/share/backgrounds /usr/share/icons
echo "{dark_b64}" | base64 -d | sudo tee /usr/share/backgrounds/vyron-dark.png > /dev/null
echo "{light_b64}" | base64 -d | sudo tee /usr/share/backgrounds/vyron-light.png > /dev/null
echo "{logo_b64}" | base64 -d | sudo tee /usr/share/icons/vyron-logo.png > /dev/null

echo "=== 6. DEPLOYING VYRON-THEME ENGINE ==="
echo "{theme_b64}" | base64 -d | sudo tee /usr/local/bin/vyron-theme > /dev/null
sudo chmod 755 /usr/local/bin/vyron-theme

echo "=== 7. DEPLOYING VYRON-SYSMON UTILITY ==="
echo "{sysmon_b64}" | base64 -d | sudo tee /usr/local/bin/vyron-sysmon > /dev/null
sudo chmod 755 /usr/local/bin/vyron-sysmon

echo "=== 8. REGISTERING DESKTOP APPLICATION SHORTCUTS ==="
sudo tee /usr/share/applications/vyron-sysmon.desktop << 'DESK1'
[Desktop Entry]
Version=1.0
Type=Application
Name=Vyron System Monitor
Comment=Real-time CPU, RAM, Storage and Network Telemetry
Exec=/usr/local/bin/vyron-sysmon
Icon=utilities-system-monitor
Categories=System;Monitor;
Terminal=false
DESK1

sudo tee /usr/share/applications/vyron-theme.desktop << 'DESK2'
[Desktop Entry]
Version=1.0
Type=Application
Name=Toggle Dark/Light Mode
Comment=Switch between Vyron UI Dark and Light Mode
Exec=/usr/local/bin/vyron-theme switch
Icon=preferences-desktop-theme
Categories=Settings;DesktopSettings;
Terminal=false
DESK2

echo "=== 9. CONFIGURING LIGHTDM AUTOLOGIN ==="
sudo mkdir -p /etc/lightdm/lightdm.conf.d
sudo tee /etc/lightdm/lightdm.conf.d/01-vyron-autologin.conf << 'LCONF'
[Seat:*]
autologin-user=vyron
autologin-user-timeout=0
user-session=xfce
greeter-session=lightdm-gtk-greeter
LCONF

echo "=== 10. CONFIGURING DEFAULT VYRON UI V1 XFCE PROFILE ==="
mkdir -p /home/vyron/.config/xfce4/xfconf/xfce-perchannel-xml
mkdir -p /home/vyron/.config/vyron
echo "dark" > /home/vyron/.config/vyron/theme.state

# Default xsettings (Greybird-dark, Adwaita icons)
cat << 'XSET' > /home/vyron/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xsettings" version="1.0">
  <property name="Net" type="empty">
    <property name="ThemeName" type="string" value="Greybird-dark"/>
    <property name="IconThemeName" type="string" value="Adwaita"/>
    <property name="DoubleClickTime" type="int" value="400"/>
    <property name="DoubleClickDistance" type="int" value="5"/>
    <property name="DndDragThreshold" type="int" value="8"/>
    <property name="CursorThemeName" type="string" value="Adwaita"/>
    <property name="CursorThemeSize" type="int" value="24"/>
    <property name="SoundThemeName" type="string" value="default"/>
    <property name="EnableEventSounds" type="bool" value="false"/>
    <property name="EnableInputFeedbackSounds" type="bool" value="false"/>
  </property>
  <property name="Xft" type="empty">
    <property name="DPI" type="int" value="-1"/>
    <property name="Antialias" type="int" value="1"/>
    <property name="Hinting" type="int" value="1"/>
    <property name="HintStyle" type="string" value="hintslight"/>
    <property name="RGBA" type="string" value="rgb"/>
  </property>
</channel>
XSET

# Default xfwm4 (Greybird-dark theme)
cat << 'XFWM' > /home/vyron/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="theme" type="string" value="Greybird-dark"/>
    <property name="title_alignment" type="string" value="left"/>
    <property name="title_font" type="string" value="Sans Bold 9"/>
    <property name="button_layout" type="string" value="O|HMC"/>
    <property name="box_resize" type="bool" value="false"/>
    <property name="box_move" type="bool" value="false"/>
    <property name="double_click_action" type="string" value="maximize"/>
    <property name="scroll_workspaces" type="bool" value="true"/>
    <property name="workspace_count" type="int" value="2"/>
    <property name="use_compositing" type="bool" value="true"/>
  </property>
</channel>
XFWM

# Default xfce4-desktop (Dark wallpaper)
cat << 'DESKCONF' > /home/vyron/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitor0" type="empty">
        <property name="workspace0" type="empty">
          <property name="color-style" type="int" value="0"/>
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="/usr/share/backgrounds/vyron-dark.png"/>
        </property>
      </property>
    </property>
  </property>
  <property name="desktop-icons" type="empty">
    <property name="style" type="int" value="2"/>
    <property name="file-icons" type="empty">
      <property name="show-home" type="bool" value="true"/>
      <property name="show-filesystem" type="bool" value="true"/>
      <property name="show-trash" type="bool" value="true"/>
      <property name="show-removable" type="bool" value="true"/>
    </property>
  </property>
</channel>
DESKCONF

# Set ownership to vyron
chown -R vyron:vyron /home/vyron/.config

echo "=== 11. ENABLING GRAPHICAL TARGET IN SYSTEMD ==="
sudo systemctl set-default graphical.target
sudo systemctl enable lightdm

echo "=== PHASE 5 DESKTOP STACK INSTALLATION COMPLETED SUCCESSFULLY ==="
sync
sudo poweroff
EOF
chmod +x /tmp/run_p5_install.sh
bash /tmp/run_p5_install.sh
'''

    try:
        while time.time() - start_time < 1800:
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
                    print("\n>>> Logged in. Dispatching Phase 5 Desktop Installer Script...")
                    time.sleep(0.5)
                    proc.stdin.write(f"{installer_script.strip()}\n".encode("utf-8"))
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

    if "PHASE 5 DESKTOP STACK INSTALLATION COMPLETED SUCCESSFULLY" in out_text:
        print("\n>>> SUCCESS: Phase 5 desktop stack installed cleanly!")
        sys.exit(0)
    else:
        print("\n>>> FAILED or INCOMPLETE: Review log at " + LOG_PATH)
        sys.exit(1)

if __name__ == "__main__":
    main()
