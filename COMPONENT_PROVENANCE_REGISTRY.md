# VyronOS Component Provenance Registry

In accordance with the **VyronOS Originality, Independent Identity & Provenance Policy**, this document records the origin, license, modifications, and classification of all core components comprising VyronOS.

---

## Provenance Matrix

| Component | Upstream / Origin | License | Classification | Modifications & Customizations | Attribution / Upstream Repository |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Linux Kernel** | Linux Kernel Organization / Debian | GPL-2.0-only | Upstream Foundation | Standard Debian 12 Bookworm ARM64 kernel (`6.1.0-56-arm64`) with EFI GOP framebuffer support | https://www.kernel.org / https://kernel-team.pages.debian.net |
| **Base Userland & APT** | Debian Project | Multi-license (DFSG, GPL, LGPL, MIT, BSD) | Upstream Foundation | Minimal Debian 12 Bookworm base with hardened sudoers, non-root `vyron` user, and VirtualBox network integration | https://www.debian.org |
| **Display Server (Xorg)** | X.Org Foundation | MIT / X11 | Upstream Subsystem | Xorg 21.1.7 with modesetting and fbdev backends for VirtualBox Apple Silicon display | https://gitlab.freedesktop.org/xorg |
| **Display Manager (LightDM)** | Robert Ancell / LightDM Team | GPL-3.0-or-later / LGPL-3.0 | Upstream Subsystem | Configured for autologin session management to unprivileged `vyron` user | https://github.com/canonical/lightdm |
| **Window Manager (XFWM4)** | XFCE Team (Olivier Fourdan) | GPL-2.0-or-later | Customized Subsystem | Configured with modern titlebars, software compositing, and 5 discrete workspaces | https://gitlab.xfce.org/xfce/xfwm4 |
| **Top Status Panel (xfce4-panel)** | XFCE Development Team | GPL-2.0 / LGPL-2.0 | Substantially Customized | Re-architected top panel layout with minimalist workspace pills, central clock, and custom status indicators via GTK CSS | https://gitlab.xfce.org/xfce/xfce4-panel |
| **Floating Dock (Plank)** | Plank Project (Robert Dyer, Rico Tzschichholz) | GPL-3.0-or-later | Customized Subsystem | Configured with custom `Vyron-Dock` translucent glass theme, zoom animation, and curated application launcher array | https://github.com/ricotz/plank |
| **Application Launcher (Rofi)** | Dave Davenport, Rasmus Steinke | MIT | Customized Subsystem | Configured with custom `vyron.rasi` translucent glass theme, dual-column view, and app categorization | https://github.com/davatorium/rofi |
| **Compositor (Picom)** | Yuxuan Shui / Picom Team | MIT / MPL-2.0 | Customized Subsystem | Tuned for VirtualBox Apple Silicon with rounded window corners, subtle drop shadows, and zero artifacting | https://github.com/yshui/picom |
| **Icon Theme (Papirus & Branded)** | Papirus Development Team & Vyron Team | GPL-3.0-or-later | Hybrid (Upstream + Custom) | Papirus Dark vector iconography integrated with custom Vyron system and launcher marks | https://github.com/PapirusDevelopmentTeam/papirus-icon-theme |
| **Vyron Theme Engine (`vyron-theme`)** | VyronOS Project | MIT | **Original Vyron Component** | Original Python 3 dynamic dual-theme switching engine (`dark`, `light`, `switch`, `status`, `--json`) syncing GTK, XFWM, and wallpapers | VyronOS Internal (`/usr/local/bin/vyron-theme`) |
| **Vyron System Monitor (`vyron-sysmon`)** | VyronOS Project | MIT | **Original Vyron Component** | Original Python/GTK real-time system monitoring tool displaying CPU, RAM, disk, and running process telemetry | VyronOS Internal (`/usr/local/bin/vyron_sysmon.py`) |
| **Vyron Wallpapers (`vyron-dark`, `vyron-light`)** | VyronOS Project | CC-BY-SA-4.0 | **Original Vyron Asset** | Original flowing magenta/purple cyberpunk abstract artwork with dark angular shadow geometry | VyronOS Internal (`/usr/share/backgrounds/`) |
| **Rust Kernel IPC Subsystem (`kernel/src/ipc`)** | EuraliOS (Ben Dudson) / MOROS / Redox | MIT | Adapted Subsystem | Synchronous rendezvous message passing, Short/Long message descriptors, capability handles | https://github.com/bendudson/euralios |
| **Rust Kernel PCI Bus Driver (`kernel/src/drivers/pci.rs`)** | EuraliOS (Ben Dudson) / MOROS / Theseus | MIT | Adapted Subsystem | Hardware PCI location decoding, BAR parsing, VirtualBox device enumeration | https://github.com/bendudson/euralios |
| **Rust Kernel Network Drivers (`kernel/src/drivers/net`)** | EuraliOS (Ben Dudson) / MOROS (Vincent Ollivier) | MIT | Adapted Subsystem | RTL8139 ring buffer driver, VirtIO-Net packet header negotiation, MAC abstractions | https://github.com/bendudson/euralios |
| **Rust Kernel Capability VFS (`kernel/src/vfs`)** | EuraliOS (Ben Dudson) | MIT | Adapted Subsystem | FileLike & DirLike capability traits, in-memory directory hierarchy, path lookup | https://github.com/bendudson/euralios |
| **Rust OS Comparison Reference** | Stefan Schindler (flosse) | CC0 / MIT | Architectural Reference | Comparative taxonomy of Rust operating systems (Redox, Theseus, MOROS, EuraliOS) informing subsystem design | https://github.com/flosse/rust-os-comparison |

---

## Verification & Compliance Check
- [x] All upstream foundations (Debian, Linux Kernel) are transparently attributed with zero misleading claims.
- [x] Legal copyright notices, licenses, and attribution files are strictly preserved in `/usr/share/doc/*/copyright`.
- [x] Independent Vyron components (`vyron-theme`, `vyron-sysmon`, custom artwork, dock themes) are explicitly differentiated.
- [x] Release packages are validated against this registry prior to final distribution.
