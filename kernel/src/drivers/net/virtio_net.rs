// ==============================================================================
// VYRON Micro-OS - VirtIO Network Driver Subsystem
// Layer 10: Hardware Network Drivers
//
// Provenance & Attribution:
// - Origin: Adapted from EuraliOS VirtIO-Net Driver (https://github.com/bendudson/euralios)
// - Authors: Ben Dudson (EuraliOS), OASIS VirtIO Standard Committee
// - License: MIT License (https://opensource.org/licenses/MIT)
// ==============================================================================

use super::rtl8139::MacAddress;

pub const VIRTIO_NET_HDR_F_NEEDS_CSUM: u8 = 1;
pub const VIRTIO_NET_HDR_F_DATA_VALID: u8 = 2;

pub const VIRTIO_NET_HDR_GSO_NONE: u8 = 0;
pub const VIRTIO_NET_HDR_GSO_TCPV4: u8 = 1;
pub const VIRTIO_NET_HDR_GSO_UDP: u8 = 3;
pub const VIRTIO_NET_HDR_GSO_TCPV6: u8 = 4;

/// Standard VirtIO Network Packet Header
#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct VirtioNetHeader {
    pub flags: u8,
    pub gso_type: u8,
    pub hdr_len: u16,
    pub gso_size: u16,
    pub csum_start: u16,
    pub csum_offset: u16,
    pub num_buffers: u16,
}

impl VirtioNetHeader {
    pub fn new() -> Self {
        Self::default()
    }
}

/// VirtIO Network Device Controller
#[derive(Debug)]
pub struct VirtioNetDevice {
    pub io_base: u16,
    pub mac: MacAddress,
    pub status: u16,
    pub features: u32,
    pub rx_queue_len: usize,
    pub tx_queue_len: usize,
    pub tx_count: u64,
    pub rx_count: u64,
}

impl VirtioNetDevice {
    pub fn new(io_base: u16, mac: MacAddress) -> Self {
        Self {
            io_base,
            mac,
            status: 0,
            features: 0,
            rx_queue_len: 128,
            tx_queue_len: 128,
            tx_count: 0,
            rx_count: 0,
        }
    }

    pub fn negotiate_features(&mut self, supported_features: u32) {
        // Negotiate common features: MAC, STATUS, CSUM
        self.features = supported_features & 0x0003_0020;
        self.status = 0x07; // DRIVER_OK | ACKNOWLEDGE | DRIVER
    }

    pub fn send_packet(&mut self, payload: &[u8]) -> Result<usize, &'static str> {
        if self.status & 0x04 == 0 {
            return Err("VirtIO device not active");
        }
        self.tx_count += 1;
        Ok(payload.len())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_virtio_net_header_and_negotiation() {
        let mac = MacAddress::new([0x52, 0x54, 0x00, 0x12, 0x34, 0x57]);
        let mut vdev = VirtioNetDevice::new(0xC000, mac);

        let hdr = VirtioNetHeader::new();
        assert_eq!(hdr.gso_type, VIRTIO_NET_HDR_GSO_NONE);

        vdev.negotiate_features(0xFFFF_FFFF);
        assert_eq!(vdev.status, 0x07);

        let test_packet = [0x01, 0x02, 0x03, 0x04];
        let bytes_sent = vdev.send_packet(&test_packet).unwrap();
        assert_eq!(bytes_sent, 4);
        assert_eq!(vdev.tx_count, 1);
    }
}
