// ==============================================================================
// VYRON Micro-OS - Kernel Logging, Diagnostics & Initialization
// Layer 1 & 2: Boot Entry, Diagnostics and Structured Logging
// ==============================================================================

use std::time::Instant;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LogLevel {
    Info,
    Warn,
    Error,
    Trace,
}

impl LogLevel {
    pub fn as_str(&self) -> &'static str {
        match self {
            LogLevel::Info => "INFO",
            LogLevel::Warn => "WARN",
            LogLevel::Error => "ERROR",
            LogLevel::Trace => "TRACE",
        }
    }
}

pub struct KernelDiagnostics {
    start_time: Instant,
    log_entries: Vec<String>,
}

impl KernelDiagnostics {
    pub fn new() -> Self {
        Self {
            start_time: Instant::now(),
            log_entries: Vec::new(),
        }
    }

    pub fn log(&mut self, level: LogLevel, subsystem: &str, message: &str) {
        let elapsed = self.start_time.elapsed().as_micros() as f64 / 1_000_000.0;
        let entry = format!("[{:>10.6}] [{:<5}] [{:<10}] {}", elapsed, level.as_str(), subsystem, message);
        println!("{}", entry);
        self.log_entries.push(entry);
    }

    pub fn entries(&self) -> &[String] {
        &self.log_entries
    }
}

pub fn boot_banner() {
    println!("================================================================================");
    println!("  VYRON Micro-OS Kernel v1.0 LTS");
    println!("  Architecture: Modular Rust Micro-Kernel Subsystem (x86_64 SMP)");
    println!("================================================================================");
}
