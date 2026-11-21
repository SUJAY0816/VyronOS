# VYRON Micro-OS: Mac Laptop Hardware Compatibility Specification

**Project:** VYRON Micro-OS  
**Author:** SREEHARAN  
**Target Hardware:** Apple Mac Laptops (Intel x86_64 Core 2 Duo / Core i-Series & Apple Silicon M1/M2/M3/M4)  
**Host Firmware:** Apple Proprietary EFI 2.x & EDK2 Virtual UEFI  

---

## 1. Architectural Matrix: Intel Mac vs Apple Silicon

VYRON Micro-OS provides native hardware compatibility across both major Apple hardware eras through a bifurcated driver abstraction layer:

```
                          ┌─────────────────────────────────────┐
                          │         VYRON Micro-OS Base         │
                          └──────────────────┬──────────────────┘
                                             │
                  ┌──────────────────────────┴──────────────────────────┐
                  ▼                                                     ▼
      ┌───────────────────────┐                             ┌───────────────────────┐
      │   Intel Mac x86_64    │                             │  Apple Silicon ARM64  │
      │     (2008–2020)       │                             │     (2020–Present)    │
      ├───────────────────────┤                             ├───────────────────────┤
      │ • Apple EFI Blessing  │                             │ • Bare-Metal: Asahi   │
      │ • SPI Trackpad/Kbd    │                             │   (m1n1 -> U-Boot)    │
      │ • Broadcom STA / BCM  │                             │ • Hypervisor VMs:     │
      │ • mbpfan + Apple SMC  │                             │   UTM / Parallels /   │
      │ • apple_set_os dGPU   │                             │   VMware (VirtIO)     │
      └───────────────────────┘                             └───────────────────────┘
```

---

## 2. Input Hardware: Apple Keyboards & Trackpads

Apple MacBooks transitioned their internal keyboard and trackpad connections across three distinct hardware buses:
1. **USB Bus (Pre-2015):** Uses standard USB HID protocol via `hid-apple`.
2. **Intel LPSS SPI Bus (2015–2017):** Routed through an Intel Low Power Subsystem (LPSS) SPI controller.
3. **Apple T2 BCE Bridge (2018–2020):** Routed through the Apple T2 ARM security co-processor via the Buffer Copy Engine (`apple-bce`).

### 2.1 The SPI Trackpad & Keyboard Stack (`applespi`)
On MacBook 12" Retina and MacBook Pro (2015–2017), the internal keyboard and Force Touch trackpad require a 4-driver module chain:
```text
intel_lpss_pci        --> Intel LPSS PCI host controller driver
spi_pxa2xx_platform   --> Core SPI master controller driver
spi_pxa2xx_pci        --> PCI glue driver for SPI bus
applespi              --> Apple SPI protocol decoder (Trackpad multi-touch & keyboard)
```

> [!IMPORTANT]
> These modules are baked into VYRON's initial ramdisk (`/etc/initramfs-tools/modules`) so that the keyboard is operational before rootfs pivot, allowing user interaction in emergency shells or disk encryption prompts.

### 2.2 Apple Keyboard Ergonomics Tuning (`hid_apple`)
Apple laptop keyboards have unique modifier layouts. VYRON configures `/etc/modprobe.d/hid_apple.conf`:
```ini
# F1-F12 keys behave as standard function keys by default (Fn key accesses media keys)
options hid_apple fnmode=2

# Swap Left Option and Left Command to match standard PC muscle memory (Ctrl - Super - Alt)
options hid_apple swap_opt_cmd=1

# Maintain standard Fn and Left Control placement
options hid_apple swap_fn_leftctrl=0

# Fix non-US keyboard pipe/backslash and tilde key inversion
options hid_apple iso_layout=0
```

### 2.3 Force Touch Trackpad `libinput` Configuration
Placed at `/etc/X11/xorg.conf.d/40-apple-trackpad.conf`:
```ini
Section "InputClass"
    Identifier "Apple SPI / USB Trackpad"
    MatchDriver "libinput"
    MatchIsTouchpad "on"
    Option "Tapping" "on"
    Option "NaturalScrolling" "true"
    Option "ClickMethod" "clickfinger"
    Option "DisableWhileTyping" "true"
EndSection
```

---

## 3. Wireless & Wired Network Compatibility

### 3.1 Broadcom BCM43xx Wi-Fi Driver Strategy
Apple laptops predominantly feature Broadcom Wi-Fi chips requiring non-free microcode firmware:

| Mac Generation | Broadcom Chipset | PCI Device ID | Active Driver | Firmware Package |
|:---|:---|:---|:---|:---|
| MacBook Pro 2008–2010 | BCM4321, BCM4322 | `14e4:4328`, `14e4:432b` | `b43` / `wl` | `firmware-b43-installer` |
| MacBook Pro/Air 2010–2011 | BCM43224, BCM43225 | `14e4:4353` | `brcmsmac` | `firmware-brcm80211` |
| MacBook Pro/Air 2011–2012 | BCM4331 | `14e4:4331` | `b43` or `wl` | `broadcom-sta-dkms` |
| MacBook Retina 2013–2015 | BCM4360 (3x3 802.11ac) | `14e4:43a0` | `wl` (STA) | `broadcom-sta-dkms` |
| MacBook Pro 2015–2017 | BCM43602 (FullMAC) | `14e4:43ba` | `brcmfmac` | `firmware-brcm80211` |

#### Driver Collision Prevention:
Because `b43`, `brcmsmac`, and `wl` conflict if loaded simultaneously, `/etc/modprobe.d/broadcom-sta-dkms.conf` establishes clean blacklisting so that only the optimal driver claims the PCI bus.

### 3.2 Wired LAN & Thunderbolt Adapters
- **Apple Thunderbolt to Gigabit Ethernet Adapter:** Powered by Broadcom NetXtreme **BCM57762** (`14e4:1682`). Managed by `thunderbolt` and `tg3` modules.
- **Apple USB-C Multiport / Thunderbolt Docks:** Powered by Realtek **RTL8152/RTL8153** (`r8152`) or ASIX AX88179 (`ax88179_178a`).
- **USB CDC Ethernet:** Native `cdc_ether` and `cdc_ncm` support.

---

## 4. Power & Thermal Management on Mac Hardware

### 4.1 Apple System Management Controller (`applesmc`)
The Apple SMC hardware manages battery charging curves, ambient light sensors, keyboard backlighting, and fan tachometers.
- **Sysfs Root:** `/sys/devices/platform/applesmc.768/`
- **Keyboard Illumination:** `/sys/class/leds/smc::kbd_backlight/brightness`

### 4.2 MacBook Thermal Daemon (`mbpfan`)
Under standard Linux, MacBooks run dangerously hot because Apple firmware relies on macOS kernel daemons to scale fans. VYRON deploys `mbpfan` configured at `/etc/mbpfan.conf`:
```ini
[general]
min_fan_speed = 2000
max_fan_speed = 6200
low_temp = 55       # Fans start spinning up when CPU exceeds 55°C
high_temp = 78      # Fans run at elevated speed above 78°C
max_temp = 90       # Emergency full RPM speed at 90°C
polling_interval = 2
```

### 4.3 Mobile Power Optimization (`TLP`)
VYRON integrates `tlp` to enforce PCIe Active State Power Management (ASPM), USB autosuspend, and mobile CPU frequency scaling:
- On AC Power: Intel Performance Governor, Turbo Boost Enabled.
- On Battery: Powersave Governor, Energy Performance Bias set to Power, PCIe ASPM `powersupersave`.

---

## 5. Display, Backlight & Dual-GPU Management (`apple-gmux`)

On dual-GPU MacBook Pros (Intel integrated GPU + AMD/NVIDIA discrete GPU):
1. **The gmux Multiplexer:** The display panel is connected to the proprietary Apple gmux chip, not directly to the GPUs. Screen brightness is governed by `/sys/class/backlight/gmux_backlight`.
2. **Firmware Spoofing (`apple_set_os`):**  
   Apple EFI firmware disables the integrated Intel GPU when booting non-macOS operating systems. VYRON's GRUB configuration calls `apple_set_os "Mac OS X"`, tricking the firmware into enabling the power-efficient Intel GPU.

---

## 6. Apple EFI Blessing & Startup Manager Customization

To ensure VYRON appears with an official OS identity when holding the **Option** (Alt) key at startup:
- **Blessing Path:** `/System/Library/CoreServices/boot.efi`
- **Mac Metadata Property List (`SystemVersion.plist`):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>ProductBuildVersion</key>
    <string>10A1</string>
    <key>ProductName</key>
    <string>VYRON OS</string>
    <key>ProductVersion</key>
    <string>1.0</string>
</dict>
</plist>
```
- **Partition Scheme:** Pure GPT with standard protective MBR (`0xEE`). Hybrid MBR is strictly prohibited to prevent tripping Intel Macs into CSM/BIOS mode.

---

## 7. Apple Silicon (ARM64) Support: UTM, Parallels & Asahi

### 7.1 Virtualization Environments (UTM, Parallels Desktop, VMware Fusion)
For running VYRON on Apple Silicon Macs (M1/M2/M3/M4) via hypervisors:
- **Firmware:** EDK2 ARM64 UEFI.
- **Kernel:** `linux-image-arm64` with VirtIO drivers (`virtio_net`, `virtio_blk`, `virtio_gpu`).
- **Guest Integrations:** `qemu-guest-agent`, `spice-vdagent`, and `open-vm-tools`.

### 7.2 Bare-Metal Apple Silicon (Asahi Linux Architecture)
- **Boot Chain:** Apple iBoot -> `m1n1` -> `u-boot` -> `bootaa64.efi` -> Asahi Linux Kernel.
- **Speaker Safety Warning:** Raw ALSA playback is strictly restricted; audio must route through PipeWire with `asahi-audio` convolver limiters to protect hardware speaker voice coils.
