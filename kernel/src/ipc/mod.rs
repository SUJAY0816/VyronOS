// ==============================================================================
// VYRON Micro-OS - Inter-Process Communication (IPC) Subsystem
// Layer 8: Rendezvous Synchronous Message Passing
//
// Provenance & Attribution:
// - Origin: Adapted from EuraliOS "Merriwig" Kernel (https://github.com/bendudson/euralios)
// - Author: Ben Dudson (with architectural design inspired by Vincent Ollivier / MOROS
//   and Jeremy Soller / Redox OS)
// - License: MIT License (https://opensource.org/licenses/MIT)
//
// Subsystem Description:
// Implements capability-safe rendezvous message passing between tasks.
// Messages can be Short (fixed register values) or Long (transferring communication
// handles, endpoints, or physical memory slices).
// ==============================================================================

use std::collections::VecDeque;

/// Control bitmask constants for message types and capability transfers
/// (Derived from EuraliOS syscall message control layout)
pub const MESSAGE_LONG: u64 = 1 << 8;
pub const MESSAGE_DATA2_RDV: u64 = 1 << 9;
pub const MESSAGE_DATA2_MEM: u64 = 2 << 9;
pub const MESSAGE_DATA2_ERR: u64 = 3 << 9;
pub const MESSAGE_DATA2_TYPE: u64 = MESSAGE_DATA2_RDV | MESSAGE_DATA2_MEM | MESSAGE_DATA2_ERR;

pub const MESSAGE_DATA3_RDV: u64 = 1 << 11;
pub const MESSAGE_DATA3_MEM: u64 = 2 << 11;

/// Payload components that can be transmitted across IPC channels
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MessageData {
    /// Pure scalar value or register data
    Value(u64),
    /// Transferred channel capability handle ID
    Channel(u32),
    /// Transferred memory buffer slice (physical base, length)
    Memory { phys_addr: usize, length: usize },
    /// Error code descriptor
    Error(u32),
}

impl From<u64> for MessageData {
    fn from(value: u64) -> Self {
        MessageData::Value(value)
    }
}

impl From<u32> for MessageData {
    fn from(channel_id: u32) -> Self {
        MessageData::Channel(channel_id)
    }
}

/// Messages in the Vyron microkernel IPC subsystem
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Message {
    /// Fast short message containing 3 register values (command/tag, arg1, arg2)
    Short(u64, u64, u64),
    /// Long message containing capability handles or memory regions
    Long(u64, MessageData, MessageData),
}

impl Message {
    pub fn is_long(&self) -> bool {
        matches!(self, Message::Long(_, _, _))
    }

    pub fn tag(&self) -> u64 {
        match self {
            Message::Short(tag, _, _) => *tag,
            Message::Long(tag, _, _) => *tag,
        }
    }
}

/// Errors returned by IPC rendezvous operations
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IpcError {
    ChannelEmpty,
    ChannelBusy,
    SenderAlreadyWaiting,
    ReceiverAlreadyWaiting,
    MismatchedFilter,
    ChannelNotFound,
    TaskBlocked,
    InvalidPayload,
}

/// Rendezvous internal channel state
#[derive(Debug, Clone)]
enum RendezvousState {
    Empty,
    Sending {
        sender_task: u32,
        message: Message,
        #[allow(dead_code)]
        awaiting_reply: bool,
    },
    Receiving {
        receiver_task: u32,
        filter_task: Option<u32>,
    },
}

/// Synchronous Rendezvous Communication Channel
/// Matches a sending task with a receiving task. If sender arrives first,
/// it buffers until receiver arrives (or blocks); if receiver arrives first,
/// it awaits a sender.
#[derive(Debug, Clone)]
pub struct RendezvousChannel {
    pub id: u32,
    pub name: String,
    state: RendezvousState,
    pub message_log: Vec<(u32, u32, Message)>, // (from_task, to_task, message)
    pending_queue: VecDeque<(u32, Message)>,
}

impl RendezvousChannel {
    pub fn new(id: u32, name: &str) -> Self {
        Self {
            id,
            name: name.to_string(),
            state: RendezvousState::Empty,
            message_log: Vec::new(),
            pending_queue: VecDeque::new(),
        }
    }

    /// Send a message to the channel.
    /// If a receiver is waiting (and passes task filter), delivery occurs immediately.
    /// If no receiver is waiting:
    /// - If `blocking` is true, sender is queued / recorded in `Sending` state.
    /// - If `blocking` is false, message is enqueued into pending buffer.
    pub fn send(&mut self, sender_task: u32, message: Message, blocking: bool) -> Result<Option<u32>, IpcError> {
        match &self.state {
            RendezvousState::Empty => {
                if blocking {
                    self.state = RendezvousState::Sending {
                        sender_task,
                        message,
                        awaiting_reply: false,
                    };
                    Ok(None) // Sender blocked, awaiting receiver
                } else {
                    self.pending_queue.push_back((sender_task, message));
                    Ok(None)
                }
            }
            RendezvousState::Sending { .. } => {
                // If another sender is already waiting, queue into backlog
                self.pending_queue.push_back((sender_task, message));
                Ok(None)
            }
            RendezvousState::Receiving { receiver_task, filter_task } => {
                let rx_task = *receiver_task;
                if let Some(f_task) = filter_task {
                    if *f_task != sender_task {
                        return Err(IpcError::MismatchedFilter);
                    }
                }
                // Match made! Deliver directly
                self.message_log.push((sender_task, rx_task, message));
                self.state = RendezvousState::Empty;
                Ok(Some(rx_task))
            }
        }
    }

    /// Receive a message from the channel.
    /// Returns `Some((sender_task, message))` if a sender is matched, or `None` if blocked.
    pub fn receive(&mut self, receiver_task: u32, filter_task: Option<u32>, blocking: bool) -> Result<Option<(u32, Message)>, IpcError> {
        // First check pending non-blocking queue
        if let Some(pos) = self.pending_queue.iter().position(|(s_task, _)| {
            filter_task.map_or(true, |f| f == *s_task)
        }) {
            let (sender_task, message) = self.pending_queue.remove(pos).unwrap();
            self.message_log.push((sender_task, receiver_task, message.clone()));
            return Ok(Some((sender_task, message)));
        }

        // Check if a sender is currently blocked in `Sending` state
        match &self.state {
            RendezvousState::Sending { sender_task, message, .. } => {
                let s_task = *sender_task;
                if let Some(f_task) = filter_task {
                    if f_task != s_task {
                        return Err(IpcError::MismatchedFilter);
                    }
                }
                let msg = message.clone();
                self.message_log.push((s_task, receiver_task, msg.clone()));
                self.state = RendezvousState::Empty;
                Ok(Some((s_task, msg)))
            }
            RendezvousState::Empty => {
                if blocking {
                    self.state = RendezvousState::Receiving { receiver_task, filter_task };
                    Ok(None) // Receiver blocked, awaiting sender
                } else {
                    Err(IpcError::ChannelEmpty)
                }
            }
            RendezvousState::Receiving { .. } => {
                Err(IpcError::ReceiverAlreadyWaiting)
            }
        }
    }

    pub fn is_empty(&self) -> bool {
        matches!(self.state, RendezvousState::Empty) && self.pending_queue.is_empty()
    }
}

/// Global IPC Hub managing active communication rendezvous endpoints
#[derive(Debug, Default)]
pub struct IpcHub {
    channels: Vec<RendezvousChannel>,
    next_id: u32,
}

impl IpcHub {
    pub fn new() -> Self {
        Self {
            channels: Vec::new(),
            next_id: 1,
        }
    }

    pub fn create_channel(&mut self, name: &str) -> u32 {
        let id = self.next_id;
        self.next_id += 1;
        self.channels.push(RendezvousChannel::new(id, name));
        id
    }

    pub fn get_channel_mut(&mut self, id: u32) -> Option<&mut RendezvousChannel> {
        self.channels.iter_mut().find(|c| c.id == id)
    }

    pub fn find_by_name(&mut self, name: &str) -> Option<&mut RendezvousChannel> {
        self.channels.iter_mut().find(|c| c.name == name)
    }

    pub fn total_messages_delivered(&self) -> usize {
        self.channels.iter().map(|c| c.message_log.len()).sum()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ipc_short_message_rendezvous() {
        let mut hub = IpcHub::new();
        let chan_id = hub.create_channel("sys.service.fs");

        let chan = hub.get_channel_mut(chan_id).unwrap();

        // Task 10 sends a short request (Open file tag = 0x20)
        let msg = Message::Short(0x20, 100, 200);
        let delivery = chan.send(10, msg.clone(), false).unwrap();
        assert!(delivery.is_none());

        // Task 20 (Server) receives the request
        let rx = chan.receive(20, None, false).unwrap();
        assert!(rx.is_some());
        let (sender, received_msg) = rx.unwrap();
        assert_eq!(sender, 10);
        assert_eq!(received_msg, msg);
        assert_eq!(chan.message_log.len(), 1);
    }

    #[test]
    fn test_ipc_long_message_capability_transfer() {
        let mut hub = IpcHub::new();
        let chan_id = hub.create_channel("sys.driver.pci");
        let chan = hub.get_channel_mut(chan_id).unwrap();

        // Pass a memory buffer descriptor through long message
        let mem_payload = MessageData::Memory { phys_addr: 0x8000_1000, length: 4096 };
        let chan_payload = MessageData::Channel(42);
        let long_msg = Message::Long(0x50, mem_payload.clone(), chan_payload.clone());

        chan.send(5, long_msg.clone(), true).unwrap();
        let rx = chan.receive(9, Some(5), true).unwrap().unwrap();

        assert_eq!(rx.0, 5);
        assert_eq!(rx.1, long_msg);
        assert!(rx.1.is_long());
    }
}
