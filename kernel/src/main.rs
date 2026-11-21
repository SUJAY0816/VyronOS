// ==============================================================================
// VYRON Micro-OS - Master Kernel Runtime & Integrated Demonstration
// Layer 10: Integrated Execution of All 10 Layers
// ==============================================================================

use vyron_kernel::*;
use std::fs::File;
use std::io::Write;
use std::sync::Arc;

fn main() {
    // Layer 1 & 2: Boot & Kernel Diagnostics
    boot_banner();
    let mut diag = KernelDiagnostics::new();
    diag.log(LogLevel::Info, "BOOT", "Initializing VYRON Micro-OS kernel subsystems...");

    // Layer 8: Memory Allocator Initialization
    let mut free_list = FreeListAllocator::new(1024 * 1024); // 1 MB heap
    let block1 = free_list.allocate(4096).expect("Heap alloc block1 failed");
    let block2 = free_list.allocate(8192).expect("Heap alloc block2 failed");
    diag.log(LogLevel::Info, "MEMORY", &format!("Allocated block1 at 0x{:X} (4KB), block2 at 0x{:X} (8KB)", block1, block2));
    free_list.deallocate(block1, 4096);
    diag.log(LogLevel::Info, "MEMORY", "Deallocated block1; Free-List coalesced adjacent blocks");

    // Layer 7: Concurrency & Synchronization
    diag.log(LogLevel::Info, "SYNC", "Testing Spinlock synchronization primitive...");
    let protected_counter = Arc::new(Spinlock::new(0u32));
    {
        let mut guard = protected_counter.lock();
        *guard += 1;
        diag.log(LogLevel::Info, "SYNC", &format!("Protected counter safely incremented to {}", *guard));
    } // guard drops here

    // Layer 6: Hardware Timer
    let mut timer = HardwareTimer::new(10); // 10ms tick
    diag.log(LogLevel::Info, "TIMER", &format!("Hardware timer initialized (tick: {}ms)", timer.tick_interval_ms));

    // Layer 9: System Call Interface
    let mut syscall_dispatcher = SyscallDispatcher::new();
    let pid_res = syscall_dispatcher.dispatch(SYS_GETPID, 101, 0).unwrap();
    diag.log(LogLevel::Info, "SYSCALL", &format!("sys_getpid returned caller PID {}", pid_res));

    // Layer 10 (New): IPC Rendezvous Subsystem (Adapted from EuraliOS)
    let mut ipc_hub = IpcHub::new();
    let sys_net_channel = ipc_hub.create_channel("sys.net.nic");
    diag.log(LogLevel::Info, "IPC", &format!("Created IPC Rendezvous channel #{} [sys.net.nic]", sys_net_channel));
    {
        let chan = ipc_hub.get_channel_mut(sys_net_channel).unwrap();
        let cmd = Message::Short(0x01, 1500, 0); // Config MTU 1500
        chan.send(1, cmd, false).unwrap();
        let rx = chan.receive(2, None, false).unwrap().unwrap();
        diag.log(LogLevel::Info, "IPC", &format!("Rendezvous delivery matched: Task #{} -> Task #{} (Tag 0x{:X})", rx.0, 2, rx.1.tag()));
    }

    // Layer 11 (New): PCI Bus Hardware Discovery (Adapted from EuraliOS / MOROS)
    let mut pci_bus = PciBus::new();
    pci_bus.populate_virtualbox_hardware();
    diag.log(LogLevel::Info, "PCI", &format!("Enumerated {} virtual hardware devices on PCI bus", pci_bus.all_devices().len()));
    for dev in pci_bus.all_devices() {
        diag.log(LogLevel::Info, "PCI", &format!("Discovered {} [{}] at {}", dev.device_name(), dev.vendor_name(), dev.location));
    }

    // Layer 12 (New): Network Driver Subsystem (Adapted from EuraliOS RTL8139)
    let mac = MacAddress::new([0x08, 0x00, 0x27, 0xC1, 0x7B, 0x86]);
    let mut rtl_nic = Rtl8139Device::new(0xD000, mac);
    rtl_nic.init();
    let test_frame = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x08, 0x00, 0x27, 0xC1, 0x7B, 0x86, 0x08, 0x06];
    rtl_nic.transmit(&test_frame).unwrap();
    diag.log(LogLevel::Info, "NET", &format!("RTL8139 NIC (MAC {}) transmitted ARP frame ({} pkts, {} bytes)", mac, rtl_nic.tx_packet_count, rtl_nic.tx_byte_count));

    // Layer 13 (New): Capability VFS (Adapted from EuraliOS)
    let vfs = VfsRoot::new();
    vfs.populate_default_hierarchy();
    let root_entries = vfs.root.read().unwrap().list_entries();
    diag.log(LogLevel::Info, "VFS", &format!("Capability VFS initialized with root entries: {:?}", root_entries));

    // Layer 4 & 5: Task Management & Round Robin Scheduler
    diag.log(LogLevel::Info, "SCHEDULER", "Configuring Round Robin CPU Scheduler (Quantum = 3 ticks)...");
    let mut scheduler = RoundRobinScheduler::new(3);

    // Enqueue 4 Controlled Tasks (TC2 Workload)
    scheduler.enqueue_task(Task::new(1, "Init-Service", 8, TaskPriority::High, 0));
    scheduler.enqueue_task(Task::new(2, "Network-Worker", 5, TaskPriority::Normal, 0));
    scheduler.enqueue_task(Task::new(3, "Memory-Compactor", 6, TaskPriority::Normal, 0));
    scheduler.enqueue_task(Task::new(4, "Telemetry-Daemon", 4, TaskPriority::Low, 0));

    diag.log(LogLevel::Info, "TASKS", "Enqueued 4 tasks into Ready Queue");

    // Open trace log file for Python analysis layer
    std::fs::create_dir_all("traces").ok();
    let mut trace_file = File::create("traces/scheduler_trace.jsonl").ok();

    println!("\n--------------------------------------------------------------------------------");
    println!("  Executing Scheduler Time-Slice Loop (Timer Interrupt Driven)");
    println!("--------------------------------------------------------------------------------");

    while !scheduler.is_idle() {
        timer.trigger_interrupt();
        if let Some(event) = scheduler.tick() {
            println!("[Tick {:>3}] {}", scheduler.current_tick, event);
        }

        // Emit trace record if active
        if let Some(ref active) = scheduler.current_task {
            if let Some(ref mut f) = trace_file {
                let json = format!(
                    "{{\"tick\":{}, \"task_id\":{}, \"task_name\":\"{}\", \"state\":\"{:?}\", \"remaining\":{}}}\n",
                    scheduler.current_tick, active.id, active.name, active.state, active.remaining_burst
                );
                let _ = f.write_all(json.as_bytes());
            }
        }
    }

    println!("--------------------------------------------------------------------------------");
    diag.log(LogLevel::Info, "SCHEDULER", "All tasks completed execution successfully!");

    // Performance Metrics Output
    let (avg_tat, avg_wait, total_switches) = scheduler.metrics();
    println!("\n================================================================================");
    println!("  VYRON Micro-OS Execution Telemetry & Performance Analysis");
    println!("================================================================================");
    println!("  Total Elapsed Ticks     : {}", scheduler.current_tick);
    println!("  Total Context Switches  : {}", total_switches);
    println!("  Average Turnaround Time : {:.2} ticks", avg_tat);
    println!("  Average Waiting Time    : {:.2} ticks", avg_wait);
    println!("  Peak Memory Allocated   : {} bytes", free_list.peak_allocated_bytes);
    println!("  Total Spinlock Accesses : {}", protected_counter.stats.total_acquisitions.load(std::sync::atomic::Ordering::Relaxed));
    println!("  Total Syscalls Handled  : {}", syscall_dispatcher.call_count);
    println!("================================================================================\n");
}
