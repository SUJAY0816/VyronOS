# VyronOS Architecture Specification: Phase 5.1 — Vyron UI V2

**Document Version:** 2.0.0  
**Phase:** 5.1 (Visual Refinement & Desktop Modernization)  
**Target Hypervisor:** Oracle VM VirtualBox  
**Base Distribution:** Debian 12 Bookworm (Linux 6.12.95 LTS)  
**Status:** In Progress (Execution & Deployment)

---

## 1. Executive Summary & Review Verdict Alignment

Following the architectural review by ChatGPT, **Phase 5 has been functionally approved (20/20 acceptance gates passed)** with the underlying Linux 6.12 LTS kernel, Xorg, XFCE 4.18, XFWM4, LightDM, GTK3, NetworkManager, and VirtualBox display driver foundation accepted.

However, visual acceptance was deferred pending a dedicated refinement milestone: **Phase 5.1 — Vyron UI V2**. The objective is to elevate VyronOS from a standard Linux desktop configuration into a distinctive, cohesive, modern desktop environment inspired by the uploaded visual direction:

```
Reference Direction: ShedOS / Layan / COSMIC System Monitor
Base Background: Deep Midnight Indigo (#0B071E to #180B33)
Luminous Flow: Electric Magenta / Violet Flowing Ribbon (#EC4899 / #D926A9 / #8B5CF6)
Accents: Electric Violet (#7C3AED), Soft Cyan (#06B6D4)
Window Corners: 10-12px rounded
Top Bar: 36px clean, uncrowded layout (Workspaces pill, active window, centered clock, systray)
Dock: 68px centered floating glassmorphic pill with 48px squircle application icons
```

---

## 2. Golden Master Preservation & Safety Strategy

In strict adherence to the project's golden master preservation rules:

| Master Artifact | Status | SHA256 Checksum |
| :--- | :--- | :--- |
| `dist/VyronOS-Disk-Phase2-Verified.qcow2` | Locked / Preserved | `6614b5fd0f45926859de88d92f168b2653aa25fe7774b6fc906b616aa7547382` |
| `dist/VyronOS-Disk-Phase3-Verified.qcow2` | Locked / Preserved | `04f659634abda1bb25680c0e5f1dc60bd95822ac1fdcd9fe2947b9e90f8253ba` |
| `dist/VyronOS-Disk-Phase4-Verified.qcow2` | Locked / Preserved | `6a0a5539f998d513a97b3e0e20d3445071fdec2d8fcdb2cfc428402927448ba2` |
| **`dist/VyronOS-Disk-Phase5-Verified.qcow2`** | **Locked / Preserved** | **`65b7e2a86dba653d5cfb80a361dae1e763812c92b98b38f9af2e20f7a4576927`** |
| `dist/VyronOS-Disk-Phase5.1-Working.qcow2` | **Active Working Clone** | Cloned from Phase 5 Master; all edits isolated here |

> [!IMPORTANT]
> The Phase 5 Golden Master was set to read-only (`chmod 444`) before Phase 5.1 began. Historical backups and quarantined Rust experiments remain fully intact.

---

## 3. Vyron UI V2 Visual Architecture

### 3.1. Color System

| Role | Dark Mode (Default) | Light Mode Counterpart | Purpose |
| :--- | :--- | :--- | :--- |
| **Base Background** | `#0B071E` (Deep Midnight) | `#F1F5F9` (Warm Slate) | Window & desktop backgrounds |
| **Surface Cards** | `#14102B` (Layered Charcoal) | `#FFFFFF` (Pure Card) | Application content & cards |
| **Primary Accent** | `#7C3AED` (Electric Violet) | `#7C3AED` (Electric Violet) | Selection, active states, focus |
| **Secondary Accent**| `#06B6D4` (Soft Cyan) | `#0284C7` (Sky Cyan) | Telemetry gauges, highlights |
| **Borders** | `rgba(255,255,255,0.12)` | `rgba(0,0,0,0.12)` | 1px subtle separation |
| **Text Primary** | `#F8FAFC` (Crisp Silver) | `#0F172A` (Deep Slate) | Unclipped legible typography |

### 3.2. Top Panel (36px) Specification
* **Height:** 36px, full-width edge-to-edge.
* **Background:** Semi-transparent dark glass `rgba(12, 10, 26, 0.88)` with `1px` subtle bottom border.
* **Left:**
  * Vyron emblem launcher button (`vyron-logo`).
  * Workspace Switcher: Pill capsule containing workspaces `1`, `2`, `3`, `4`, with active workspace highlighted in an electric violet capsule.
  * Active window tasklist / title.
* **Center:**
  * Centered digital clock: `%A  %I:%M %p` (e.g., `Saturday  09:49 AM`) with high-contrast text and zero clipping.
* **Right:**
  * Systray: NetworkManager status (Ethernet / Wi-Fi), PulseAudio volume, Power / Battery indicator, and a sleek circular Power button (`⏻`).

### 3.3. Floating Centered Dock (68px) Specification
* **Height:** 68px, icon size 48px.
* **Geometry:** Floating capsule with `24px` border radius, elevated 12px above bottom screen margin.
* **Background:** Dark glassmorphism `rgba(18, 14, 38, 0.92)` with `1px solid rgba(255,255,255,0.15)` border and smooth box-shadow.
* **Applications (9 Squircles):**
  1. `vyron-browser` — Web Browser (Orange-violet gradient)
  2. `vyron-code` — Code Editor (Cyan-blue gradient)
  3. `thunar` (`vyron-files`) — File Manager (Amber-gold gradient)
  4. `xfce4-terminal` (`vyron-terminal`) — Terminal (Graphite gradient with `>_` glyph)
  5. `vyron-sysmon` (`vyron-system-monitor`) — System Monitor (Indigo gradient with pulse wave)
  6. `mousepad` (`vyron-editor`) — Text Editor (Teal-emerald gradient)
  7. `xcalc` (`vyron-calc`) — Calculator (Electric violet gradient)
  8. `xfce4-settings` (`vyron-settings`) — System Settings (Slate gradient)
  9. `vyron-launcher` — 9-dot App Grid
* **Active Indicators:** 3px electric violet illuminated dot/bar below active running applications.

### 3.4. Overhauled System Monitor (`vyron-sysmon`)
* **Interface:** Modern GTK3 card layout inspired by the COSMIC System Monitor.
* **Telemetry Cards:**
  1. *Processor (CPU):* Real model from `/proc/cpuinfo`, active cores, frequency, and real-time usage gauge.
  2. *Memory (RAM):* Total, used, available MB, and percentage bar from `/proc/meminfo`.
  3. *Storage:* Mounted root partition `/`, used/free GB, ext4 filesystem status.
  4. *Network:* Real NetworkManager device status, connection name, IP address, gateway.
* **Zero Mock Policy:** All telemetry strictly derived from genuine Linux kernel interfaces.

---

## 4. Phase 5.1 Acceptance Criteria

The implementation must satisfy all 10 acceptance gates:

| # | Acceptance Gate | Verification Method | Required Output |
| :-: | :--- | :--- | :--- |
| **1** | **Native Desktop** | Process inspection | Genuine Xorg, XFCE4, XFWM4; no browser wrapper |
| **2** | **Dark Theme Consistency** | Screenshot & GTK query | `Vyron-V2-Dark` applied across all GTK3/XFWM4 apps |
| **3** | **Light Theme Consistency** | `vyron-theme light` | `Vyron-V2-Light` applied cleanly across all windows |
| **4** | **Top Panel Spacing** | Visual inspection | 36px top bar with clean margins, no overlapping text |
| **5** | **Dock Geometry & State** | Visual inspection | Centered floating 68px dock with squircle icons & active indicators |
| **6** | **Window Decorations** | Visual inspection | 10px rounded corners with circular window controls |
| **7** | **Application Integration**| Executable verification | Terminal, Thunar, Sysmon, Editor, Calc open cleanly |
| **8** | **Multi-Resolution** | 800x600, 1280x800, 1080p| Responsive adaptation without clipping |
| **9** | **Reboot Persistence** | Cold reboot test | Theme state and panel configuration survive poweroff |
| **10**| **Regression Safety** | Full test suite | Zero regressions against Phase 1–5 baselines |
