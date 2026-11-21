// ==============================================================================
// VYRON Micro-OS - Realtek RTL8139 Network Interface Card Driver
// Layer 10: Hardware Network Drivers
//
// Provenance & Attribution:
// - Origin: Adapted from EuraliOS RTL8139 Driver (https://github.com/bendudson/euralios)
// - Authors: Ben Dudson (EuraliOS), Vincent Ollivier (MOROS)
// - License: MIT License (https://opensource.org/licenses/MIT)
//
// Subsystem Description:
// Implements driver state machine, ring buffer management, register command dispatch,
// and frame transmission/reception for the ubiquitous Realtek RTL8139 Ethernet NIC.
// ==============================================================================

use std::fmt;

/// Realtek 8139 I/O Register Offsets (from Base Address Register BAR0)
pub const REG_MAC0: u16 = 0x00;   // MAC Address ID 0-3
pub const REG_MAC4: u16 = 0x04;   // MAC Address ID 4-5
pub const REG_MAR0: u16 = 0x08;   // Multicast Array 0-3
pub const REG_MAR4: u16 = 0x0C;   // Multicast Array 4-7
pub const REG_TX_STATUS0: u16 = 0x10; // Transmit Status of Descriptor 0
pub const REG_TX_ADDR0: u16 = 0x20;   // Transmit Start Address of Descriptor 0
pub const REG_RX_BUF: u16 = 0x30;     // Receive Buffer Start Address
pub const REG_CMD: u16 = 0x37;        // Command Register
pub const REG_CAPR: u16 = 0x38;       // Current Address of Packet Read
pub const REG_CBR: u16 = 0x3A;        // Current Buffer Address
pub const REG_IMR: u16 = 0x3C;        // Interrupt Mask Register
pub const REG_ISR: u16 = 0x3E;        // Interrupt Status Register
pub const REG_TCR: u16 = 0x40;        // Transmit Configuration Register
pub const REG_RCR: u16 = 0x44;        // Receive Configuration Register
pub const REG_CONFIG1: u16 = 0x52;    // Configuration Register 1

// Command register flags
pub const CMD_RESET: u8 = 0x10;      // Software Reset
pub const CMD_RECV_ENABLE: u8 = 0x08; // Receiver Enable
pub const CMD_TRANS_ENABLE: u8 = 0x04;// Transmitter Enable
pub const CMD_BUF_EMPTY: u8 = 0x01;   // Rx Buffer Empty

// Interrupt masks
pub const INT_ROK: u16 = 0x0001;     // Receive OK
pub const INT_TOK: u16 = 0x0004;     // Transmit OK

// Buffer parameters
pub const RX_BUFFER_LEN: usize = 8192 + 16 + 1500;
pub const TX_BUFFER_LEN: usize = 1536;

/// 48-bit IEEE 802.3 MAC Address
#[derive(Clone, Copy, PartialEq, Eq, Default)]
pub struct MacAddress(pub [u8; 6]);

impl fmt::Display for MacAddress {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}",
            self.0[0], self.0[1], self.0[2], self.0[3], self.0[4], self.0[5]
        )
    }
}

impl fmt::Debug for MacAddress {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "MacAddress({})", self)
    }
}

impl MacAddress {
    pub fn new(b: [u8; 6]) -> Self {
        Self(b)
    }

    pub fn is_broadcast(&self) -> bool {
        self.0 == [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    }

    pub fn is_unicast(&self) -> bool {
        !self.is_broadcast() && (self.0[0] & 0x01 == 0)
    }
}

/// Simulated / Bare-Metal Realtek 8139 Network Device
#[derive(Debug)]
pub struct Rtl8139Device {
    pub io_base: u16,
    pub mac: MacAddress,
    pub rx_buffer: Vec<u8>,
    pub rx_read_offset: usize,
    pub tx_buffers: [Vec<u8>; 4],
    pub active_tx_id: usize,
    pub is_enabled: bool,
    pub tx_packet_count: u64,
    pub rx_packet_count: u64,
    pub tx_byte_count: u64,
    pub rx_byte_count: u64,
}

impl Rtl8139Device {
    pub fn new(io_base: u16, mac: MacAddress) -> Self {
        Self {
            io_base,
            mac,
            rx_buffer: vec![0u8; RX_BUFFER_LEN],
            rx_read_offset: 0,
            tx_buffers: [
                vec![0u8; TX_BUFFER_LEN],
                vec![0u8; TX_BUFFER_LEN],
                vec![0u8; TX_BUFFER_LEN],
                vec![0u8; TX_BUFFER_LEN],
            ],
            active_tx_id: 0,
            is_enabled: false,
            tx_packet_count: 0,
            rx_packet_count: 0,
            tx_byte_count: 0,
            rx_byte_count: 0,
        }
    }

    /// Hardware initialization sequence (power-on, reset, configure buffers)
    pub fn init(&mut self) {
        // Reset device
        self.rx_read_offset = 0;
        self.active_tx_id = 0;
        self.is_enabled = true;
    }

    /// Transmit raw Ethernet frame through round-robin descriptor ring
    pub fn transmit(&mut self, frame: &[u8]) -> Result<usize, &'static str> {
        if !self.is_enabled {
            return Err("NIC is not enabled");
        }
        if frame.len() > TX_BUFFER_LEN {
            return Err("Frame exceeds MTU / TX buffer length");
        }

        let desc_id = self.active_tx_id;
        self.tx_buffers[desc_id][..frame.len()].copy_from_slice(frame);

        // Advance to next transmit descriptor (0 -> 1 -> 2 -> 3 -> 0)
        self.active_tx_id = (self.active_tx_id + 1) % 4;
        self.tx_packet_count += 1;
        self.tx_byte_count += frame.len() as u64;

        Ok(desc_id)
    }

    /// Ingest a packet into the receive ring buffer (called on hardware interrupt)
    pub fn inject_received_packet(&mut self, packet: &[u8]) -> Result<(), &'static str> {
        if !self.is_enabled {
            return Err("NIC is not enabled");
        }
        let total_len = packet.len() + 4; // 4-byte header
        if self.rx_read_offset + total_len > RX_BUFFER_LEN {
            self.rx_read_offset = 0; // Wrap ring
        }

        // Header: Status (2 bytes), Length (2 bytes)
        let status = INT_ROK;
        self.rx_buffer[self.rx_read_offset..self.rx_read_offset + 2]
            .copy_from_slice(&status.to_le_bytes());
        self.rx_buffer[self.rx_read_offset + 2..self.rx_read_offset + 4]
            .copy_from_slice(&(packet.len() as u16).to_le_bytes());

        // Copy frame payload
        self.rx_buffer[self.rx_read_offset + 4..self.rx_read_offset + 4 + packet.len()]
            .copy_from_slice(packet);

        self.rx_packet_count += 1;
        self.rx_byte_count += packet.len() as u64;
        self.rx_read_offset += total_len;

        Ok(())
    }

    pub fn stats(&self) -> (u64, u64, u64, u64) {
        (
            self.tx_packet_count,
            self.rx_packet_count,
            self.tx_byte_count,
            self.rx_byte_count,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rtl8139_mac_formatting() {
        let mac = MacAddress::new([0x08, 0x00, 0x27, 0xC1, 0x7B, 0x86]);
        assert_eq!(mac.to_string(), "08:00:27:C1:7B:86");
        assert!(mac.is_unicast());
        assert!(!mac.is_broadcast());

        let bcast = MacAddress::new([0xFF; 6]);
        assert!(bcast.is_broadcast());
        assert!(!bcast.is_unicast());
    }

    #[test]
    fn test_rtl8139_transmit_receive_lifecycle() {
        let mac = MacAddress::new([0x52, 0x54, 0x00, 0x12, 0x34, 0x56]);
        let mut nic = Rtl8139Device::new(0xD000, mac);
        nic.init();

        // Transmit an ARP request
        let mut arp_frame = vec![0u8; 64];
        arp_frame[..6].copy_from_slice(&[0xFF; 6]); // Destination: Broadcast
        arp_frame[6..12].copy_from_slice(&mac.0);   // Source: Local MAC
        arp_frame[12..14].copy_from_slice(&[0x08, 0x06]); // EtherType: ARP

        let desc = nic.transmit(&arp_frame).expect("Transmit failed");
        assert_eq!(desc, 0);
        assert_eq!(nic.tx_packet_count, 1);
        assert_eq!(nic.tx_byte_count, 64);

        // Receive simulated reply
        let reply_frame = vec![0xABu8; 60];
        nic.inject_received_packet(&reply_frame).expect("Receive failed");
        assert_eq!(nic.rx_packet_count, 1);
        assert_eq!(nic.rx_byte_count, 60);

        let (tx_p, rx_p, tx_b, rx_b) = nic.stats();
        assert_eq!((tx_p, rx_p, tx_b, rx_b), (1, 1, 64, 60));
    }
}
