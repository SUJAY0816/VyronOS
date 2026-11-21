# VyronOS — Project File Manifest

**Document Version:** 1.0.0  
**Repository Path:** `/Users/sujayv/Downloads/VyronOS`  
**Target Environment:** Oracle VM VirtualBox  

---

## 1. Operating System Disks & Verified Golden Masters (`dist/`)

| File Path | Size | Status | Description |
|---|---|---|---|
| `dist/VyronOS-Disk.qcow2` | 1.85 GB | **Active Production** | Working production disk image containing full Linux 6.12, ext4, XFCE4, LightDM |
| `dist/VyronOS-Disk-Phase5-Verified.qcow2` | 1.85 GB | **Golden Master (P5)** | Verified Phase 5 Master (SHA256: `65b7e2a8...` - Preserved) |
| `dist/VyronOS-Disk-Phase5.1-Verified.qcow2` | 1.85 GB | **Golden Master (P5.1)** | Verified Phase 5.1 Master (SHA256: `4f6d29fb...` - Preserved) |
| `dist/VyronOS-Disk-Phase6-Verified.qcow2` | 1.85 GB | **Golden Master (P6)** | Verified Phase 6 Master (SHA256: `9e758551...`) |
| `dist/VyronOS-Disk-Phase4-Verified.qcow2` | 1.44 GB | **Golden Master (P4)** | Verified Phase 4 Master (SHA256: `6a0a5539...`) |
| `dist/VyronOS-Disk-Phase3-Verified.qcow2` | 1.43 GB | **Golden Master (P3)** | Verified Phase 3 Master (SHA256: `04f65963...`) |
| `dist/VyronOS-Disk-Phase2-Verified.qcow2` | 730 MB | **Golden Master (P2)** | Verified Phase 2 Master (SHA256: `6614b5fd...`) |
| `dist/VyronOS-Live.iso` | 85 MB | **Active Hybrid ISO** | Bootable hybrid live ISO (Debian Bookworm) |

---

## 2. Active VirtualBox Management & OS Utilities (`scripts/`)

| File Path | Status | Purpose |
|---|---|---|
| `scripts/vbox_manager.py` | **Active** | Unified VirtualBox VM management, launch, stop, and screenshot CLI |
| `scripts/vyron_theme.py` | **Active** | Dynamic dual-theme switching engine (`dark`, `light`, `switch`, `status`) |
| `scripts/vyron_sysmon.py` | **Active** | Real-time GTK3 and CLI system telemetry monitor |
| `scripts/vyron_hwinfo.py` | **Active** | Real Linux hardware introspection engine (CLI and JSON) |
| `scripts/vyron_storage.py` | **Active** | Storage device and filesystem introspection utility |
| `scripts/generate_vyron_icons.py` | **Active** | Generator for 22 minimalist SVG icons and 132 PNG raster assets |
| `scripts/generate_wallpapers.py` | **Active** | Generator for dark and light 1920x1080 desktop wallpapers |
| `scripts/chatgpt_bridge.py` | **Active** | Two-agent macOS clipboard collaboration bridge |

---

## 3. Active Verification Test Suites (`scripts/`)

| File Path | Test Target | Status |
|---|---|---|
| `scripts/test-graphics.sh` | VirtualBox VBoxSVGA controller, VRAM, EFI, and KMS | **Active (7/7 PASS)** |
| `scripts/test-desktop.sh` | VirtualBox GUI session boot & live screenshot capture | **Active (7/7 PASS)** |
| `scripts/test-gui-integration.sh` | Applications, theme switcher, and telemetry validation | **Active (6/6 PASS)** |
| `scripts/test-cold-persistence.py` | Cold reboot filesystem and telemetry persistence | **Active (5/5 PASS)** |
| `scripts/test-filesystem.sh` | ext4 nested hierarchy, read/write/append, chmod/chown | **Active (10/10 PASS)** |
| `scripts/test-storage.sh` | Storage discovery, live formatting, mount/unmount | **Active (9/9 PASS)** |
| `scripts/test-shell.sh` | Bash 5.2 pipelines, redirection, subshells, exit codes | **Active (9/9 PASS)** |
| `scripts/test-network.sh` | NetworkManager DHCP, DNS, and honest Wi-Fi reporting | **Active (17/17 PASS)** |
| `scripts/test-hardware.sh` | CPU, RAM, PCI, USB, block devices introspection | **Active (17/17 PASS)** |
| `scripts/test-boot.sh` | GRUB and UEFI boot system verification | **Active (12/12 PASS)** |
| `scripts/test_hardening.py` | Cold double-boot SHA256 persistence verification | **Active (15/15 PASS)** |

---

## 4. Visual Assets & Themes (`assets/`)

| Directory / File Path | Assets Count | Description |
|---|---|---|
| `assets/icons/*.svg` | 22 files | Scalable vector definitions for all Vyron UI V1 icons |
| `assets/icons/16x16/` through `64x64/` | 132 files | Pre-rendered PNG raster icons across 6 standard sizes |
| `assets/wallpapers/vyron-dark.png` | 1 file | 1920x1080 Dark mode geometric slate wallpaper |
| `assets/wallpapers/vyron-light.png` | 1 file | 1920x1080 Light mode geometric silver wallpaper |
| `assets/wallpapers/vyron-logo.png` | 1 file | 64x64 Start menu logo emblem |
| `assets/themes/` | - | Theme styling assets |

---

## 5. Specification & Documentation (`docs/`)

| File Path | Description |
|---|---|
| `VYRON_UI_V1_DESIGN_SPEC.json` | Master project specification and contract |
| `docs/VIRTUALBOX_ENVIRONMENT_INTEGRATION.md` | VirtualBox hypervisor architecture and driver guide |
| `docs/CURRENT_ARCHITECTURE.md` | Complete OS stack and component description |
| `docs/VIRTUALBOX_CONFIGURATION.md` | VBoxManage parameters and setup reference |
| `docs/PROJECT_CLEANUP_PLAN.md` | Staged cleanup plan and risk assessment |
| `docs/PROJECT_FILE_MANIFEST.md` | Comprehensive file inventory and status |
| `docs/VYRON_UI_V1_IMPLEMENTATION_PLAN.md` | Implementation plan for Vyron UI V1 |
| `docs/VYRON_UI_V1_ASSET_MANIFEST.md` | Catalog of icons, wallpapers, and themes |
| `docs/PHASE5_IMPLEMENTATION_REPORT.md` | Complete Phase 5 verification and results report |
| `docs/CHATGPT_PHASE5_REPORT.md` | Two-agent collaboration review package |
| `docs/screenshots/` | Live VirtualBox framebuffer screenshots |
| `docs/evidence/` | Phase verification outputs |
