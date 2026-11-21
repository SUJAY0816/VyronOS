# VyronOS Project Cleanup Plan & Deletion Safety Audit

**Date:** 2026-11-18  
**Author:** Senior Linux OS Architect & Repository Maintenance Engineer (Antigravity CLI)  
**Target Virtualization:** Oracle VM VirtualBox ONLY  
**Review Status:** Awaiting User Approval  

---

## 1. Safety Directives & Protection Rules

In accordance with strict safety mandates:
1. **NEVER DELETE OR ALTER Golden Masters:**
   - `dist/VyronOS-Disk-Phase4-Verified.qcow2` (SHA256: `6a0a5539f998d513a97b3e0e20d3445071fdec2d8fcdb2cfc428402927448ba2`)
   - `dist/VyronOS-Disk-Phase3-Verified.qcow2` (SHA256: `04f659634abda1bb25680c0e5f1dc60bd95822ac1fdcd9fe2947b9e90f8253ba`)
   - `dist/VyronOS-Disk-Phase2-Verified.qcow2` (SHA256: `6614b5fd0f45926859de88d92f168b2653aa25fe7774b6fc906b616aa7547382`)
   - `dist/VyronOS-Disk-Phase5-Verified.qcow2` (SHA256: `65b7e2a86dba653d5cfb80a361dae1e763812c92b98b38f9af2e20f7a4576927`)
   - `/Users/sujayv/Downloads/VyronOS_BACKUP_PHASE1`
2. **Never delete the active VirtualBox production disk** (`dist/VyronOS-Disk.qcow2` / `vyron os.vdi`).
3. **No broad or destructive commands** (e.g. `rm -rf *`, `rm -rf dist`, `rm -rf kernel`).
4. **Staged Execution:** All uncertain historical experiments will be moved to `quarantine/` rather than permanently destroyed.
5. **Approval Gate:** No files will be permanently deleted without explicit user confirmation.

---

## 2. Inventory of Proposed Removals & Quarantines

### Group 1: Confirmed Obsolete Files (Proposed for Permanent Deletion)

| Item Path | Size | Reason Obsolete | Dependencies Checked | Risk Level | Proposed Action |
|---|---|---|---|---|---|
| `desktop-gui/` | 1.2 MB | Obsolete HTML/CSS/JS browser-based desktop mockup from pre-Linux concept stage. Replaced by real XFCE/Xorg/LightDM desktop. | None. No Linux components depend on it. | **NONE** | Delete |
| `vm/Vyron-Micro-OS.vmwarevm/` | 2.2 GB | Obsolete VMware Fusion VM folder and logs. VirtualBox is the sole hypervisor. | None. | **NONE** | Delete |
| `Vyron-OS.utm/` | 65 MB | Obsolete UTM wrapper bundle from prior experiment. | None. | **NONE** | Delete |
| `Vyron-Desktop-OS.utm/` | 0 B | Empty UTM bundle wrapper. | None. | **NONE** | Delete |
| `vm/Vyron-VM.utm/` | 0 B | Empty UTM bundle wrapper. | None. | **NONE** | Delete |
| `download_fusion.sh` | 11 KB | Script to download VMware Fusion (retired hypervisor). | None. | **NONE** | Delete |
| `install_and_run_fusion.sh` | 1.4 KB | Script to install VMware Fusion. | None. | **NONE** | Delete |
| `run_vyron_m5_qemu.sh` | 1.8 KB | Retired QEMU Apple Silicon launch script. | None. VirtualBox manager is active. | **NONE** | Delete |
| `run_live_vm.sh` | 4.6 KB | Retired QEMU VirtIO launch script. | None. | **NONE** | Delete |
| `start_live_vm.py` | 837 B | Retired QEMU Python launcher. | None. | **NONE** | Delete |
| `scripts/run-qemu.sh` | 1.8 KB | Retired QEMU launcher in scripts directory. | None. | **NONE** | Delete |
| `scripts/run_qemu_test.sh` | 1.5 KB | Retired QEMU test runner script. | None. | **NONE** | Delete |
| `build/boot_export.raw` | 128 MB | Temporary raw disk export generated during Phase 2 ISO build. | Transient build artifact. | **NONE** | Delete |
| `build/boot_fat32.raw` | 128 MB | Temporary raw FAT32 partition generated during Phase 2 ISO build. | Transient build artifact. | **NONE** | Delete |
| `build/secondary_test.raw` | 64 MB | Disposable 64 MB scratch volume created for Phase 4 storage tests. | None. Recreated on-demand if test reruns. | **NONE** | Delete |
| `build/debs_uris.txt` | 0 B | Empty temporary apt file. | None. | **NONE** | Delete |
| `245eea35-ab5f-4a67-8c67-08adcd6db731.png` | 215 KB | Stray screenshot in root directory. Genuine screenshots are in `docs/screenshots/`. | None. | **NONE** | Delete |
| `vm/run_vyron_vm.ps1` | 4.9 KB | Windows-only PowerShell script with hardcoded `C:\Program Files\` paths. | Replaced by `scripts/vbox_manager.py`. | **NONE** | Delete |

**Total Space to be Reclaimed by Group 1:** **~2.54 GB**

---

### Group 2: Historical Early Experiments (Proposed for Quarantine into `quarantine/`)

These files represent the original Phase 1 custom Rust micro-kernel experiments. While no longer part of the active Debian/Linux production OS, moving them into `quarantine/historical_rust_experiments/` preserves historical artifacts safely without cluttering the clean repository:

| Item Path | Size | Reason for Quarantine | Safe to Quarantine? |
|---|---|---|---|
| `kernel/` | 117 MB | Rust micro-kernel experiment (`Cargo.toml`, `main.rs`, `scheduler`, `syscall`). Superceded by Debian Linux 6.12.95 LTS. | **YES** (Move to `quarantine/`) |
| `uefi-payload/` | 14 MB | Rust UEFI kernel experiment (`gui.rs`, `main.rs`). Superceded by GRUB 2.06 and Linux EFI stub. | **YES** (Move to `quarantine/`) |
| `vm/build_vyron_vdi.py` | 10 KB | Python script that packaged `uefi-payload` into `Vyron-Boot.vdi`. | **YES** (Move to `quarantine/`) |
| `vm/Vyron-Boot.raw` | 67 MB | Raw image of the Rust UEFI boot experiment. | **YES** (Move to `quarantine/`) |
| `vm/Vyron-Boot.vdi` | 4.2 MB | VirtualBox VDI of the Rust UEFI boot experiment. | **YES** (Move to `quarantine/`) |
| `Vyron-Micro-OS.iso` (root) | 36 MB | Standalone ISO of the Rust micro-kernel. | **YES** (Move to `quarantine/`) |
| `vm/Vyron-Micro-OS.iso` | 36 MB | Duplicate copy of the Rust micro-kernel ISO in `vm/`. | **YES** (Move to `quarantine/`) |
| `Vyron OS.app` | 300 KB | Legacy macOS `.app` bundle from early GUI prototyping. | **YES** (Move to `quarantine/`) |

**Total Space to be Moved to Quarantine:** **~284 MB**

---

### Group 3: Preserved Production Files (EXPLICITLY KEPT)

The following components represent the active, verified, working VyronOS implementation and will **never be touched or removed**:

1. **Operating System Disk & Masters:**
   - `dist/VyronOS-Disk.qcow2` (Active production disk with Linux 6.12, ext4, XFCE4, LightDM)
   - `dist/VyronOS-Disk-Phase5-Verified.qcow2` (Phase 5 Golden Master)
   - `dist/VyronOS-Disk-Phase4-Verified.qcow2` (Phase 4 Golden Master)
   - `dist/VyronOS-Disk-Phase3-Verified.qcow2` (Phase 3 Golden Master)
   - `dist/VyronOS-Disk-Phase2-Verified.qcow2` (Phase 2 Golden Master)
   - `dist/VyronOS-Live.iso` (Verified bootable hybrid live ISO)
   - `/Users/sujayv/Downloads/VyronOS_BACKUP_PHASE1` (Intact initial state)
2. **VirtualBox Integration & Management:**
   - `/Users/sujayv/VirtualBox VMs/vyron os/` (Configured VirtualBox VM)
   - `scripts/vbox_manager.py` (Unified VirtualBox CLI management tool)
   - `scripts/chatgpt_bridge.py` (Two-agent collaboration bridge)
3. **Core OS Custom Utilities:**
   - `scripts/vyron_theme.py` (Dynamic dark/light mode switching engine)
   - `scripts/vyron_sysmon.py` (Real GTK3 & CLI system telemetry monitor)
   - `scripts/vyron_hwinfo.py` (Hardware introspection engine)
   - `scripts/vyron_storage.py` (Storage management engine)
   - `scripts/generate_vyron_icons.py` (Geometric icon family generator)
   - `scripts/generate_wallpapers.py` (Wallpaper generator)
4. **Active Test & Validation Suites:**
   - `scripts/test-graphics.sh` (VirtualBox VBoxSVGA & KMS validation)
   - `scripts/test-desktop.sh` (VirtualBox GUI session & framebuffer validation)
   - `scripts/test-gui-integration.sh` (GUI application integration validation)
   - `scripts/test-filesystem.sh` (ext4 nested filesystem verification)
   - `scripts/test-storage.sh` (Block device formatting & mounting verification)
   - `scripts/test-shell.sh` (GNU Bash pipeline & command verification)
   - `scripts/test-cold-persistence.py` (Cold reboot state verification)
   - `scripts/test-network.sh` (NetworkManager connectivity verification)
   - `scripts/test-hardware.sh` (Hardware discovery verification)
   - `scripts/test-boot.sh` (UEFI bootloader verification)
   - `scripts/test_hardening.py` (Cold boot persistence verification)
5. **Assets & Documentation:**
   - `assets/icons/` (22 minimalist SVGs + 132 PNGs)
   - `assets/wallpapers/` (Dual 1920x1080 wallpapers + logo)
   - `assets/themes/`
   - `docs/VIRTUALBOX_ENVIRONMENT_INTEGRATION.md`
   - `docs/VYRON_UI_V1_IMPLEMENTATION_PLAN.md`
   - `docs/VYRON_UI_V1_ASSET_MANIFEST.md`
   - `docs/PHASE5_IMPLEMENTATION_REPORT.md`
   - `docs/CHATGPT_PHASE5_REPORT.md`
   - `docs/PHASE4_IMPLEMENTATION_REPORT.md`
   - `docs/CHATGPT_PHASE4_REPORT.md`
   - `docs/PHASE3_IMPLEMENTATION_REPORT.md`
   - `docs/CHATGPT_PHASE3_REPORT.md`
   - `docs/PHASE2_HARDENING_REPORT.md`
   - `docs/REAL_IMPLEMENTATION_AUDIT.md`
   - `docs/VYRON_OS_ARCHITECTURE.md`
   - `docs/screenshots/` (All verified VirtualBox framebuffer screenshots)
   - `docs/evidence/`

---

## 3. Post-Cleanup Target Project Directory Structure

```
VyronOS/
├── assets/
│   ├── icons/          # 22 SVGs and 132 PNGs (16x16 through 64x64)
│   ├── wallpapers/     # vyron-dark.png, vyron-light.png, vyron-logo.png
│   └── themes/         # GTK and XFWM4 theme overrides
├── configs/            # System configuration templates (apt, grub, branding)
├── dist/               # Production disk and verified golden masters
│   ├── VyronOS-Disk.qcow2
│   ├── VyronOS-Disk-Phase5-Verified.qcow2
│   ├── VyronOS-Disk-Phase4-Verified.qcow2
│   ├── VyronOS-Disk-Phase3-Verified.qcow2
│   ├── VyronOS-Disk-Phase2-Verified.qcow2
│   └── VyronOS-Live.iso
├── docs/               # Engineering documentation and visual evidence
│   ├── screenshots/    # Live VirtualBox framebuffer captures
│   ├── evidence/       # Phase-specific test verification outputs
│   └── *.md            # Architecture, reports, and manifests
├── scripts/            # Active OS utilities, VirtualBox manager, and test suites
│   ├── vbox_manager.py
│   ├── vyron_theme.py
│   ├── vyron_sysmon.py
│   ├── vyron_hwinfo.py
│   ├── vyron_storage.py
│   ├── test-*.sh
│   └── test_*.py
├── quarantine/         # Isolated legacy experiments (preserved, not active)
│   └── historical_rust_experiments/
└── VYRON_UI_V1_DESIGN_SPEC.json
```

---

## 4. Verification Checkpoint

Before performing any destructive actions:
- [x] Phase 4 Golden Master SHA256 verified: `6a0a5539f998d513a97b3e0e20d3445071fdec2d8fcdb2cfc428402927448ba2`
- [x] Phase 5 Golden Master SHA256 verified: `65b7e2a86dba653d5cfb80a361dae1e763812c92b98b38f9af2e20f7a4576927`
- [x] All 20 Phase 5 acceptance gates verified in Oracle VM VirtualBox
- [ ] User review and approval of this plan
