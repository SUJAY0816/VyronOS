// ==============================================================================
// VYRON Micro-OS - PCI Bus Enumeration & Device Discovery
// Layer 9: Hardware Bus Abstraction
//
// Provenance & Attribution:
// - Origin: Adapted from EuraliOS PCI Bus Driver (https://github.com/bendudson/euralios)
// - Upstream References:
//   * MOROS Kernel (Vincent Ollivier: https://github.com/vinc/moros/blob/trunk/src/sys/pci.rs)
//   * Theseus OS (Kevin Boos: https://github.com/theseus-os/Theseus/blob/theseus_main/kernel/pci/src/lib.rs)
//   * OSDev Wiki (PCI Configuration Space Specification)
// - License: MIT License (https://opensource.org/licenses/MIT)
// ==============================================================================

use std::fmt;

/// PCI Hardware Device Location (Bus:Slot:Function)
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct PciLocation {
    pub bus: u16,
    pub slot: u16,
    pub function: u16,
}

impl fmt::Display for PciLocation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:04X}:{:02X}:{:02X}", self.bus, self.slot, self.function)
    }
}

impl fmt::Debug for PciLocation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "PciLocation({:04X}:{:02X}:{:02X})", self.bus, self.slot, self.function)
    }
}

impl PciLocation {
    pub fn new(bus: u16, slot: u16, function: u16) -> Self {
        Self { bus, slot, function }
    }

    /// Decode address into PciLocation structure
    pub fn from_address(address: u32) -> Self {
        Self {
            bus: ((address >> 16) & 0xFF) as u16,
            slot: ((address >> 11) & 0x1F) as u16,
            function: ((address >> 8) & 0x07) as u16,
        }
    }

    /// Return raw x86 PCI configuration space address
    pub fn config_address(&self, offset: u8) -> u32 {
        0x8000_0000
            | ((self.bus as u32) << 16)
            | ((self.slot as u32) << 11)
            | ((self.function as u32) << 8)
            | ((offset as u32) & 0xFC)
    }
}

/// Base Address Register (BAR) Types
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PciBarType {
    Memory32 { prefetchable: bool },
    Memory64 { prefetchable: bool },
    IoPort,
}

/// PCI Base Address Register
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PciBar {
    pub index: u8,
    pub bar_type: PciBarType,
    pub base_address: u64,
    pub size: u64,
}

/// Enumerated PCI Device
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PciDevice {
    pub location: PciLocation,
    pub vendor_id: u16,
    pub device_id: u16,
    pub class_code: u8,
    pub subclass_code: u8,
    pub prog_if: u8,
    pub revision: u8,
    pub bars: Vec<PciBar>,
    pub irq: u8,
}

impl PciDevice {
    pub fn new(
        location: PciLocation,
        vendor_id: u16,
        device_id: u16,
        class_code: u8,
        subclass_code: u8,
        irq: u8,
    ) -> Self {
        Self {
            location,
            vendor_id,
            device_id,
            class_code,
            subclass_code,
            prog_if: 0,
            revision: 1,
            bars: Vec::new(),
            irq,
        }
    }

    pub fn vendor_name(&self) -> &'static str {
        match self.vendor_id {
            0x8086 => "Intel Corporation",
            0x10EC => "Realtek Semiconductor Corp.",
            0x1AF4 => "Red Hat, Inc. (VirtIO)",
            0x80EE => "Oracle VM VirtualBox",
            0x1022 => "Advanced Micro Devices, Inc. [AMD]",
            0x106B => "Apple Inc.",
            _ => "Unknown Vendor",
        }
    }

    pub fn device_name(&self) -> &'static str {
        match (self.vendor_id, self.device_id) {
            (0x10EC, 0x8139) => "RTL-8139 Fast Ethernet NIC",
            (0x1AF4, 0x1000) => "VirtIO Network Adapter",
            (0x1AF4, 0x1001) => "VirtIO Block Device",
            (0x8086, 0x2668) => "82801FB/FBM/FR/FW/FRW (ICH6 Family) High Definition Audio",
            (0x8086, 0x100E) => "82540EM Gigabit Ethernet Controller (Intel PRO/1000)",
            (0x80EE, 0xBEEF) => "VirtualBox Graphics Adapter (VBoxSVGA)",
            (0x80EE, 0xCAFE) => "VirtualBox Guest Integration Subsystem",
            _ => "Generic PCI Device",
        }
    }

    pub fn is_network_controller(&self) -> bool {
        self.class_code == 0x02 // Network Controller class
    }

    pub fn is_display_controller(&self) -> bool {
        self.class_code == 0x03 // Display Controller class
    }

    pub fn is_audio_controller(&self) -> bool {
        self.class_code == 0x04 && self.subclass_code == 0x03 // Audio device
    }
}

/// PCI Bus Management Controller
#[derive(Debug, Default)]
pub struct PciBus {
    devices: Vec<PciDevice>,
}

impl PciBus {
    pub fn new() -> Self {
        Self { devices: Vec::new() }
    }

    /// Register a discovered PCI device
    pub fn register_device(&mut self, device: PciDevice) {
        self.devices.push(device);
    }

    /// Find device by Vendor and Device ID
    pub fn find_device(&self, vendor_id: u16, device_id: u16) -> Option<&PciDevice> {
        self.devices.iter().find(|d| d.vendor_id == vendor_id && d.device_id == device_id)
    }

    /// Find devices matching a specific class and subclass
    pub fn find_by_class(&self, class_code: u8, subclass_code: u8) -> Vec<&PciDevice> {
        self.devices
            .iter()
            .filter(|d| d.class_code == class_code && d.subclass_code == subclass_code)
            .collect()
    }

    /// List all discovered PCI hardware devices
    pub fn all_devices(&self) -> &[PciDevice] {
        &self.devices
    }

    /// Populate standard virtual hardware devices typical in VirtualBox
    pub fn populate_virtualbox_hardware(&mut self) {
        // VirtualBox Host Bridge
        self.register_device(PciDevice::new(
            PciLocation::new(0, 0, 0),
            0x8086, 0x7190, 0x06, 0x00, 0
        ));
        // Intel ICH6 High Definition Audio
        let mut audio = PciDevice::new(
            PciLocation::new(0, 5, 0),
            0x8086, 0x2668, 0x04, 0x03, 14
        );
        audio.bars.push(PciBar {
            index: 0,
            bar_type: PciBarType::Memory32 { prefetchable: false },
            base_address: 0xE881_0000,
            size: 0x4000,
        });
        self.register_device(audio);

        // Realtek RTL8139 Fast Ethernet
        let mut net = PciDevice::new(
            PciLocation::new(0, 8, 0),
            0x10EC, 0x8139, 0x02, 0x00, 10
        );
        net.bars.push(PciBar {
            index: 0,
            bar_type: PciBarType::IoPort,
            base_address: 0xD000,
            size: 0x100,
        });
        self.register_device(net);

        // VirtIO Network Controller
        let mut virtio_net = PciDevice::new(
            PciLocation::new(0, 9, 0),
            0x1AF4, 0x1000, 0x02, 0x00, 11
        );
        virtio_net.bars.push(PciBar {
            index: 0,
            bar_type: PciBarType::IoPort,
            base_address: 0xC000,
            size: 0x40,
        });
        self.register_device(virtio_net);

        // Oracle VirtualBox SVGA Display
        let mut vga = PciDevice::new(
            PciLocation::new(0, 2, 0),
            0x80EE, 0xBEEF, 0x03, 0x00, 9
        );
        vga.bars.push(PciBar {
            index: 0,
            bar_type: PciBarType::Memory32 { prefetchable: true },
            base_address: 0xE000_0000,
            size: 128 * 1024 * 1024,
        });
        self.register_device(vga);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pci_location_addressing() {
        let loc = PciLocation::new(0, 8, 0);
        let addr = loc.config_address(0);
        assert_eq!(addr, 0x8000_0000 | (8 << 11));

        let decoded = PciLocation::from_address(addr);
        assert_eq!(decoded.bus, 0);
        assert_eq!(decoded.slot, 8);
        assert_eq!(decoded.function, 0);
        assert_eq!(format!("{}", loc), "0000:08:00");
    }

    #[test]
    fn test_pci_bus_virtualbox_device_enumeration() {
        let mut bus = PciBus::new();
        bus.populate_virtualbox_hardware();

        assert_eq!(bus.all_devices().len(), 5);

        // Verify Realtek NIC
        let rtl = bus.find_device(0x10EC, 0x8139).expect("RTL8139 missing");
        assert_eq!(rtl.vendor_name(), "Realtek Semiconductor Corp.");
        assert_eq!(rtl.device_name(), "RTL-8139 Fast Ethernet NIC");
        assert!(rtl.is_network_controller());
        assert_eq!(rtl.bars[0].bar_type, PciBarType::IoPort);
        assert_eq!(rtl.bars[0].base_address, 0xD000);

        // Verify VirtIO NIC
        let vnet = bus.find_device(0x1AF4, 0x1000).expect("VirtIO Net missing");
        assert_eq!(vnet.vendor_name(), "Red Hat, Inc. (VirtIO)");
        assert!(vnet.is_network_controller());

        // Verify VBoxSVGA
        let vga = bus.find_device(0x80EE, 0xBEEF).expect("VBoxSVGA missing");
        assert_eq!(vga.vendor_name(), "Oracle VM VirtualBox");
        assert!(vga.is_display_controller());
    }
}
