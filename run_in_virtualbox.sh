#!/usr/bin/env bash
set -e

VM_NAME="vyron os"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_VDI="$SCRIPT_DIR/release_phase7/VyronOS-Phase7-Production.vdi"
VBOXMANAGE="/Applications/VirtualBox.app/Contents/MacOS/VBoxManage"

if [ ! -x "$VBOXMANAGE" ]; then
    VBOXMANAGE="$(which VBoxManage || echo '/usr/local/bin/VBoxManage')"
fi

echo "=========================================================================="
echo "  VYRON OS — Oracle VM VirtualBox Production Launcher (ARM64 Native)"
echo "=========================================================================="

if [ ! -f "$PRODUCTION_VDI" ]; then
    echo "ERROR: Production VDI not found at $PRODUCTION_VDI"
    exit 1
fi

# Ensure production disk is attached to SATA Port 0
echo ">>> Verifying SATA boot drive attachment..."
"$VBOXMANAGE" storageattach "$VM_NAME" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "$PRODUCTION_VDI" 2>/dev/null || true

# Check if already running
if "$VBOXMANAGE" list runningvms | grep -q "$VM_NAME"; then
    echo "VM '$VM_NAME' is already running."
    exit 0
fi

echo ">>> Launching VirtualBox VM '$VM_NAME' in GUI mode..."
"$VBOXMANAGE" startvm "$VM_NAME" --type gui
echo "=========================================================================="
echo "  SUCCESS: VyronOS Desktop is running in Oracle VM VirtualBox."
echo "  SSH NAT Management: ssh -p 2222 vyron@127.0.0.1 (Key: ~/.ssh/vyron_key)"
echo "=========================================================================="
