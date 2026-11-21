# Vyron UI V1 Asset Manifest

This document records all graphical assets, icon definitions, theme configurations, and supporting assets implemented for Vyron UI V1 according to [`VYRON_UI_V1_DESIGN_SPEC.json`](file:///Users/sujayv/Downloads/VyronOS/VYRON_UI_V1_DESIGN_SPEC.json).

---

## 1. Wallpapers

All wallpapers are generated at 1920x1080 (16:9 reference resolution) and stored in `assets/wallpapers/`:

| Filename | Resolution | Description | Intended Theme |
|---|---|---|---|
| [`vyron-dark.png`](file:///Users/sujayv/Downloads/VyronOS/assets/wallpapers/vyron-dark.png) | 1920x1080 | Deep charcoal gradient (`#111318` to `#1A1E26`) with electric blue (`#7C8CFF`) geometric V emblem | Dark Mode (Default) |
| [`vyron-light.png`](file:///Users/sujayv/Downloads/VyronOS/assets/wallpapers/vyron-light.png) | 1920x1080 | Clean warm silver/white gradient (`#F3F5F8` to `#E4E7ED`) with slate blue (`#596BEB`) geometric V emblem | Light Mode |
| [`vyron-logo.png`](file:///Users/sujayv/Downloads/VyronOS/assets/wallpapers/vyron-logo.png) | 64x64 | Transparent PNG of the Vyron geometric emblem for Start menu button and branding | Both |

---

## 2. Geometric Icon System

The icon family is designed on a **24x24 grid**, with **2px nominal stroke width**, **round line caps**, and **round line joins**. Each icon exists as both scalable vector (`.svg`) and pre-rendered raster PNGs across 6 standard desktop sizes (`16x16`, `22x22`, `24x24`, `32x32`, `48x48`, `64x64`).

Total Icons: **22 unique icons** x (1 SVG + 6 PNGs) = **154 total asset files**.

### Icon Catalog

| Icon Name | Category | Primary Purpose | Vector Path |
|---|---|---|---|
| `vyron-logo` | Branding | Desktop Start button, about dialog, system branding | `assets/icons/vyron-logo.svg` |
| `vyron-files` | Application | Thunar File Manager application launcher | `assets/icons/vyron-files.svg` |
| `vyron-folder` | Filesystem | Directory representation in desktop & file browser | `assets/icons/vyron-folder.svg` |
| `vyron-home` | Filesystem | User `/home/vyron` home folder shortcut | `assets/icons/vyron-home.svg` |
| `vyron-terminal` | Application | XFCE Terminal application launcher | `assets/icons/vyron-terminal.svg` |
| `vyron-settings` | Application | System Settings / XFCE Settings Manager | `assets/icons/vyron-settings.svg` |
| `vyron-system-monitor` | Application | Vyron Live System Telemetry application | `assets/icons/vyron-system-monitor.svg` |
| `vyron-network` | Status / System | Generic network interface status | `assets/icons/vyron-network.svg` |
| `vyron-ethernet` | Status / System | VirtIO wired Ethernet active indicator | `assets/icons/vyron-ethernet.svg` |
| `vyron-wifi` | Status / System | Honest 802.11 wireless indicator (inactive in QEMU) | `assets/icons/vyron-wifi.svg` |
| `vyron-audio` | Status / Tray | Audio volume / speaker indicator | `assets/icons/vyron-audio.svg` |
| `vyron-display` | Status / System | Display resolution and monitor settings | `assets/icons/vyron-display.svg` |
| `vyron-notifications` | Status / Tray | Notification area bell icon | `assets/icons/vyron-notifications.svg` |
| `vyron-search` | UI Element | Whisker Menu search bar / Spotlight find | `assets/icons/vyron-search.svg` |
| `vyron-power` | Session | Top-bar and launcher power action menu | `assets/icons/vyron-power.svg` |
| `vyron-restart` | Session | System reboot action | `assets/icons/vyron-restart.svg` |
| `vyron-shutdown` | Session | System shutdown action | `assets/icons/vyron-shutdown.svg` |
| `vyron-lock` | Session | Lock screen action | `assets/icons/vyron-lock.svg` |
| `vyron-trash` | Desktop | Desktop trash bin / deleted files | `assets/icons/vyron-trash.svg` |
| `vyron-usb` | Hardware | External USB block storage indicator | `assets/icons/vyron-usb.svg` |
| `vyron-theme-dark` | Customizer | Dark theme switcher (crescent moon) | `assets/icons/vyron-theme-dark.svg` |
| `vyron-theme-light` | Customizer | Light theme switcher (sun) | `assets/icons/vyron-theme-light.svg` |

### Raster Icon Directories

```
assets/icons/
├── *.svg (22 vector files)
├── 16x16/ (22 PNG files)
├── 22x22/ (22 PNG files)
├── 24x24/ (22 PNG files)
├── 32x32/ (22 PNG files)
├── 48x48/ (22 PNG files)
└── 64x64/ (22 PNG files)
```

---

## 3. Themes & Color Palette

### Dark Theme (Default)
- **GTK Theme:** `Greybird-dark`
- **Window Manager (XFWM4):** `Greybird-dark`
- **Background Color:** `#111318`
- **Surface Color:** `#1A1E26`
- **Raised Surface:** `#232936`
- **Border Color:** `#343B49`
- **Text Color:** `#F2F4F8`
- **Muted Text:** `#A6AFBE`
- **Accent Color:** `#7C8CFF` (Electric Blue)
- **Wallpaper:** `/usr/share/backgrounds/vyron/vyron-dark.png`

### Light Theme
- **GTK Theme:** `Greybird`
- **Window Manager (XFWM4):** `Greybird`
- **Background Color:** `#F3F5F8`
- **Surface Color:** `#FFFFFF`
- **Raised Surface:** `#FFFFFF`
- **Border Color:** `#DCE1E9`
- **Text Color:** `#202633`
- **Muted Text:** `#667085`
- **Accent Color:** `#596BEB` (Slate Blue)
- **Wallpaper:** `/usr/share/backgrounds/vyron/vyron-light.png`

---

## 4. Custom Utilities & Executables

| Utility | Installed Path | Source | Purpose |
|---|---|---|---|
| `vyron-theme` | `/usr/local/bin/vyron-theme` | [`scripts/vyron_theme.py`](file:///Users/sujayv/Downloads/VyronOS/scripts/vyron_theme.py) | Dynamic switching between dark and light themes without session restart |
| `vyron-sysmon` | `/usr/local/bin/vyron-sysmon` | [`scripts/vyron_sysmon.py`](file:///Users/sujayv/Downloads/VyronOS/scripts/vyron_sysmon.py) | Real-time GTK3 and CLI telemetry reader for CPU, RAM, storage, and NetworkManager |

---

## 5. Desktop Application Shortcuts (`.desktop`)

| Name | File | Executable | Icon |
|---|---|---|---|
| Vyron System Monitor | `/usr/share/applications/vyron-sysmon.desktop` | `/usr/local/bin/vyron-sysmon` | `vyron-system-monitor` |
| Files | `/usr/share/applications/thunar.desktop` | `thunar` | `vyron-files` |
| Terminal | `/usr/share/applications/xfce4-terminal.desktop` | `xfce4-terminal` | `vyron-terminal` |
| Settings | `/usr/share/applications/xfce4-settings-manager.desktop` | `xfce4-settings-manager` | `vyron-settings` |
| Switch Theme | `/usr/share/applications/vyron-theme-switch.desktop` | `/usr/local/bin/vyron-theme switch` | `vyron-theme-dark` |
