// ==============================================================================
// VYRON Micro-OS - System Call Interface & Kernel Boundary
// Layer 9: System Interface & Specialization Track D
// ==============================================================================

pub const SYS_WRITE: usize = 1;
pub const SYS_YIELD: usize = 2;
pub const SYS_GETPID: usize = 3;
pub const SYS_ALLOC: usize = 4;
pub const SYS_EXIT: usize = 5;

pub struct SyscallDispatcher {
    pub call_count: usize,
}

impl SyscallDispatcher {
    pub fn new() -> Self {
        Self { call_count: 0 }
    }

    pub fn dispatch(&mut self, syscall_id: usize, arg1: usize, _arg2: usize) -> Result<u64, i64> {
        self.call_count += 1;
        match syscall_id {
            SYS_WRITE => {
                // Simulated console write
                Ok(arg1 as u64)
            }
            SYS_YIELD => {
                // Yield voluntary quantum
                Ok(0)
            }
            SYS_GETPID => {
                // Return caller PID (arg1 as current PID)
                Ok(arg1 as u64)
            }
            SYS_ALLOC => {
                // Simulated allocation of arg1 bytes
                Ok(0x20000 + (arg1 as u64))
            }
            SYS_EXIT => {
                // Terminate caller
                Ok(0)
            }
            _ => Err(-1), // ENOSYS: Function not implemented
        }
    }
}
