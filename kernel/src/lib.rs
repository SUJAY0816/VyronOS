// ==============================================================================
// VYRON Micro-OS Kernel - Library Exports
// Core Kernel Subsystems and Architectural Modules
// ==============================================================================

pub mod kernel;
pub mod task;
pub mod scheduler;
pub mod timer;
pub mod sync;
pub mod memory;
pub mod syscall;

// Enhanced Subsystems Adapted from EuraliOS (MIT License - Ben Dudson)
pub mod ipc;
pub mod drivers;
pub mod vfs;

pub use kernel::{KernelDiagnostics, LogLevel, boot_banner};
pub use task::{Task, TaskState, TaskPriority, TaskContext};
pub use scheduler::{RoundRobinScheduler, MlfqScheduler, ContextSwitchRecord};
pub use timer::HardwareTimer;
pub use sync::{Spinlock, SpinlockGuard};
pub use memory::{BumpAllocator, FreeListAllocator};
pub use syscall::{SyscallDispatcher, SYS_WRITE, SYS_YIELD, SYS_GETPID, SYS_ALLOC, SYS_EXIT};

// IPC Exports
pub use ipc::{IpcHub, RendezvousChannel, Message, MessageData, IpcError};

// Drivers & Hardware Bus Exports
pub use drivers::{PciBus, PciDevice, PciLocation, PciBar, PciBarType};
pub use drivers::net::{MacAddress, Rtl8139Device, VirtioNetDevice, VirtioNetHeader};

// Capability VFS Exports
pub use vfs::{VfsRoot, MemoryDirectory, MemoryFile, FileLike, DirLike};
