// ==============================================================================
// VYRON Micro-OS - Timer Interrupt & Preemption Subsystem
// Layer 6: Timer-Driven Scheduling
// ==============================================================================

pub struct HardwareTimer {
    pub tick_interval_ms: u32,
    pub ticks_fired: u64,
    pub is_enabled: bool,
}

impl HardwareTimer {
    pub fn new(interval_ms: u32) -> Self {
        Self {
            tick_interval_ms: interval_ms,
            ticks_fired: 0,
            is_enabled: true,
        }
    }

    pub fn trigger_interrupt(&mut self) -> u64 {
        if self.is_enabled {
            self.ticks_fired += 1;
        }
        self.ticks_fired
    }

    pub fn disable(&mut self) {
        self.is_enabled = false;
    }

    pub fn enable(&mut self) {
        self.is_enabled = true;
    }
}
