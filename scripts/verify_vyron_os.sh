#!/usr/bin/env bash
# ==============================================================================
# VYRON Micro-OS - Automated Verification & Architectural Test Suite
# ==============================================================================
set -euo pipefail

PASS=0
FAIL=0

test_assert() {
    local description="$1"
    local command="$2"
    printf "Testing: %-60s ... " "$description"
    if eval "$command" >/dev/null 2>&1; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL"
        FAIL=$((FAIL + 1))
    fi
}

echo "=========================================================================="
echo "  VYRON Micro-OS Verification & Architectural Self-Test"
echo "=========================================================================="

# 1. Script syntax checks
test_assert "Bash syntax in build_vyron_os.sh" "bash -n build_vyron_os.sh"
test_assert "Bash syntax in run_vyron_m5_qemu.sh" "bash -n run_vyron_m5_qemu.sh"
test_assert "Bash syntax in scripts/vyron-firstboot" "bash -n scripts/vyron-firstboot"
test_assert "Bash syntax in configs/apt/01-aptitude-alias.sh" "bash -n configs/apt/01-aptitude-alias.sh"

# 2. Package Manager & System Configuration
test_assert "Aptitude alias configured for apt and apt-get" "grep -q 'alias apt=' configs/apt/01-aptitude-alias.sh && grep -q 'alias apt-get=' configs/apt/01-aptitude-alias.sh"
test_assert "Aptitude daily background update timers deferred" "grep -q 'OnBootSec=30min' build_vyron_os.sh"
test_assert "APT 99vyron performance config exists" "test -f configs/apt/99vyron.conf"

# 3. Cleanliness & Purge Tests
test_assert "Zero Snap daemon enablement in build_vyron_os.sh" "! grep -E 'systemctl enable snapd|apt-get install.*snapd|snapd\.socket' build_vyron_os.sh"
test_assert "Mac command shims completely removed" "! test -d scripts/mac-commands"
test_assert "First boot script references available commands" "grep -q 'Available Commands:' scripts/vyron-firstboot"

# 4. Hardware Driver & Kernel Integration (Silent & Built-in)
test_assert "VirtIO network and block drivers enabled" "grep -q 'virtio_net' configs/hardware/apple-hardware.conf && grep -q 'virtio_blk' configs/hardware/apple-hardware.conf"
test_assert "Apple SMC and HID hardware modules defined" "grep -q 'applesmc' configs/hardware/apple-hardware.conf"

# 5. Bootloader & Live System
test_assert "GRUB config specifies live boot parameters" "grep -q 'boot=live' configs/grub/grub.cfg"
test_assert "OS identification release file defines VYRON" "grep -q 'ID=vyron' configs/branding/os-release"

# 6. Rust Micro-OS Kernel & Verification Layer
test_assert "Rust Micro-OS Cargo.toml defines vyron-kernel" "grep -q 'name = \"vyron-kernel\"' kernel/Cargo.toml"
test_assert "Rust kernel test cases file exists" "test -f kernel/tests/test_cases.rs"
test_assert "Python trace analysis script exists" "test -f kernel/scripts/analyze_traces.py"
test_assert "VYRON OS Architecture specification exists" "test -f docs/VYRON_OS_ARCHITECTURE.md"

# 7. Bare-Metal UEFI Payload & VirtualBox VM Engine
test_assert "UEFI payload source code exists" "test -f uefi-payload/src/main.rs"
test_assert "VirtualBox disk builder script exists" "test -f vm/build_vyron_vdi.py"
test_assert "VirtualBox VM launcher script exists" "test -f vm/run_vyron_vm.ps1"
test_assert "Bootable VDI virtual disk exists" "test -f vm/Vyron-Boot.vdi"
test_assert "Live VM screen capture exists" "test -f vm/vyron_running_screen.png"

# 8. CA-6 & CA-7 Capstone Deliverables
test_assert "CA-6 Section 22 and 23 technical documentation suite exists" "test -f kernel/docs/technical_report.md && test -f kernel/docs/architecture.md && test -f kernel/docs/design.md && test -f kernel/docs/testing.md && test -f kernel/docs/debugging_log.md && test -f kernel/docs/viva_preparation.md"
test_assert "CA-6 Track A MLFQ scheduler and TC7 exist in kernel" "grep -q 'struct MlfqScheduler' kernel/src/scheduler/mod.rs && grep -q 'test_tc7_mlfq_dynamic_demotion_and_aging' kernel/tests/test_cases.rs"
test_assert "CA-6 telemetry results CSV and SVG charts exist" "test -f kernel/results/scheduler_ticks.csv && test -f kernel/results/task_metrics.csv && test -f kernel/results/scheduler_gantt.svg && test -f kernel/results/fairness_distribution.svg"

echo "=========================================================================="
echo "  SUMMARY: ${PASS} Passed, ${FAIL} Failed"
if [ "$FAIL" -eq 0 ]; then
    echo "  ALL ARCHITECTURAL VERIFICATION GATES PASSED CLEANLY."
    exit 0
else
    echo "  SOME TESTS FAILED. CHECK SYSTEM OUTPUT."
    exit 1
fi
echo "=========================================================================="
