# VyronOS — Oracle VM VirtualBox Configuration Reference

**Target Hypervisor:** Oracle VM VirtualBox 7.2.22 r175245  
**Host Architecture:** macOS Apple Silicon (ARM64)  
**VM Name:** `vyron os`  
**Configuration File:** `/Users/sujayv/VirtualBox VMs/vyron os/vyron os.vbox`  

---

## 1. Virtual Machine Definition

The VM is configured with the following parameters via `VBoxManage`:

```bash
# General & Platform
VBoxManage modifyvm "vyron os" --ostype "Linux_arm64"
VBoxManage modifyvm "vyron os" --firmware efi
VBoxManage modifyvm "vyron os" --cpus 2
VBoxManage modifyvm "vyron os" --memory 4096

# Graphics & Display
VBoxManage modifyvm "vyron os" --graphicscontroller vboxsvga
VBoxManage modifyvm "vyron os" --vram 128

# Pointing & Input Devices
VBoxManage modifyvm "vyron os" --mouse usbtablet
VBoxManage modifyvm "vyron os" --keyboard usb

# Audio
VBoxManage modifyvm "vyron os" --audio-enabled on
VBoxManage modifyvm "vyron os" --audio-controller hda

# Networking
VBoxManage modifyvm "vyron os" --nic1 nat
VBoxManage modifyvm "vyron os" --nictype1 usbnet

# Storage Controller
VBoxManage storagectl "vyron os" --name "SATA" --add sata --controller IntelAhci --portcount 2 --bootable on
VBoxManage storageattach "vyron os" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "/Users/sujayv/VirtualBox VMs/vyron os/vyron os.vdi"
```

---

## 2. Display Geometry & Extradata Configuration

VirtualBox EFI firmware graphics geometry and UI scaling are managed via extradata keys:

```bash
# Set EFI GOP Resolution (Default 1280x800 or 1920x1080)
VBoxManage setextradata "vyron os" "VBoxInternal2/EfiGraphicsResolution" "1280x800"

# UI Scaling Factor (Optimized for Retina displays)
VBoxManage setextradata "vyron os" "GUI/ScaleFactor" "2.0"

# Dynamic Video Mode Hinting during runtime
VBoxManage controlvm "vyron os" setvideomodehint 1024 768 32
```

---

## 3. Operational CLI Commands (`VBoxManage`)

```bash
# 1. Check VM Hardware Status
VBoxManage showvminfo "vyron os"

# 2. Check if VM is Running
VBoxManage list runningvms

# 3. Launch VM in GUI Mode
VBoxManage startvm "vyron os" --type gui

# 4. Capture Framebuffer Screenshot
VBoxManage controlvm "vyron os" screenshotpng /path/to/capture.png

# 5. Graceful ACPI Shutdown
VBoxManage controlvm "vyron os" acpipowerbutton

# 6. Immediate Poweroff
VBoxManage controlvm "vyron os" poweroff
```

---

## 4. Guest Additions Integration

- **Host ISO Location:** `/Applications/VirtualBox.app/Contents/MacOS/VBoxGuestAdditions.iso` (53,207,040 bytes).
- **Guest Packages:** Debian `virtualbox-guest-utils` and `virtualbox-guest-x11`.
- **KMS Driver:** VirtualBox SVGA graphics channels communicate with the Linux kernel's standard `vmwgfx` DRM driver (`/dev/dri/card0`), providing stable hardware-accelerated 2D blits and composition.
