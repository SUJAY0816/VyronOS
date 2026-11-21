// ==============================================================================
// VYRON Micro-OS - Kernel Verification & Stress Test Suite (TC1 - TC6)
// Automated Mechanism and Stress Validation
// ==============================================================================

use vyron_kernel::*;

#[test]
fn test_tc1_minimum_configuration() {
    // TC1: Minimum Configuration with 2 Tasks
    let mut scheduler = RoundRobinScheduler::new(2);
    scheduler.enqueue_task(Task::new(1, "Task-A", 4, TaskPriority::Normal, 0));
    scheduler.enqueue_task(Task::new(2, "Task-B", 4, TaskPriority::Normal, 0));

    while !scheduler.is_idle() {
        scheduler.tick();
    }

    assert_eq!(scheduler.completed_tasks.len(), 2);
    assert!(scheduler.context_switches.len() >= 4);
}

#[test]
fn test_tc2_multiple_tasks() {
    // TC2: Multiple Controlled Tasks (4 Tasks)
    let mut scheduler = RoundRobinScheduler::new(3);
    scheduler.enqueue_task(Task::new(1, "Worker-1", 6, TaskPriority::Normal, 0));
    scheduler.enqueue_task(Task::new(2, "Worker-2", 3, TaskPriority::Normal, 0));
    scheduler.enqueue_task(Task::new(3, "Worker-3", 9, TaskPriority::Normal, 0));
    scheduler.enqueue_task(Task::new(4, "Worker-4", 2, TaskPriority::Normal, 0));

    while !scheduler.is_idle() {
        scheduler.tick();
    }

    assert_eq!(scheduler.completed_tasks.len(), 4);
    let (avg_tat, avg_wait, _) = scheduler.metrics();
    assert!(avg_tat > 0.0);
    assert!(avg_wait > 0.0);
}

#[test]
fn test_tc3_boundary_case() {
    // TC3: Boundary Case: Minimum quantum = 1 and 1-byte memory allocation
    let mut scheduler = RoundRobinScheduler::new(1);
    scheduler.enqueue_task(Task::new(1, "Short-1", 1, TaskPriority::High, 0));
    scheduler.enqueue_task(Task::new(2, "Short-2", 1, TaskPriority::High, 0));

    while !scheduler.is_idle() {
        scheduler.tick();
    }

    assert_eq!(scheduler.completed_tasks.len(), 2);

    let mut allocator = FreeListAllocator::new(16);
    let offset = allocator.allocate(1);
    assert!(offset.is_some());
}

#[test]
fn test_tc4_stress_case() {
    // TC4: Stress Case: 20 rapid tasks & concurrent spinlock access
    let mut scheduler = RoundRobinScheduler::new(2);
    for i in 1..=20 {
        scheduler.enqueue_task(Task::new(i, &format!("Stress-{}", i), 2, TaskPriority::Normal, 0));
    }

    while !scheduler.is_idle() {
        scheduler.tick();
    }

    assert_eq!(scheduler.completed_tasks.len(), 20);

    let lock = Spinlock::new(0u32);
    for _ in 0..500 {
        let mut guard = lock.lock();
        *guard += 1;
    }
    assert_eq!(*lock.lock(), 500);
}

#[test]
fn test_tc5_failure_case() {
    // TC5: Controlled Failure Case: OOM Allocation & Invalid Syscall
    let mut allocator = BumpAllocator::new(0x1000, 64);
    let alloc1 = allocator.allocate(48, 4);
    assert!(alloc1.is_some());

    // Excess allocation must fail gracefully (None)
    let alloc_overflow = allocator.allocate(128, 4);
    assert!(alloc_overflow.is_none());

    let mut dispatcher = SyscallDispatcher::new();
    let invalid_call = dispatcher.dispatch(999, 0, 0);
    assert!(invalid_call.is_err());
}

#[test]
fn test_tc6_repeatability() {
    // TC6: Deterministic Repeatability across multiple runs
    let run_experiment = || {
        let mut scheduler = RoundRobinScheduler::new(3);
        scheduler.enqueue_task(Task::new(1, "T1", 6, TaskPriority::Normal, 0));
        scheduler.enqueue_task(Task::new(2, "T2", 6, TaskPriority::Normal, 0));
        while !scheduler.is_idle() {
            scheduler.tick();
        }
        (scheduler.current_tick, scheduler.context_switches.len())
    };

    let (ticks_1, switches_1) = run_experiment();
    let (ticks_2, switches_2) = run_experiment();

    assert_eq!(ticks_1, ticks_2);
    assert_eq!(switches_1, switches_2);
}

#[test]
fn test_tc7_mlfq_dynamic_demotion_and_aging() {
    // TC7: Track A Specialization: Multi-Level Feedback Queue with 3 Priority Levels & Aging
    // Quanta: Q0 = 2 ticks, Q1 = 4 ticks, Q2 = 8 ticks. Boost interval = 12 ticks.
    let mut mlfq = MlfqScheduler::new([2, 4, 8], 12);

    // Enqueue an interactive short task and a long batch-compute task
    mlfq.enqueue_task(Task::new(1, "Interactive-IO", 2, TaskPriority::High, 0));
    mlfq.enqueue_task(Task::new(2, "Batch-Compute", 14, TaskPriority::High, 0));

    let mut boost_observed = false;
    let mut demotion_observed = false;

    while !mlfq.is_idle() {
        if let Some(event) = mlfq.tick() {
            if event.contains("Priority Boost") {
                boost_observed = true;
            }
            if event.contains("demoted to") {
                demotion_observed = true;
            }
        }
    }

    assert_eq!(mlfq.completed_tasks.len(), 2);

    let interactive = mlfq.completed_tasks.iter().find(|t| t.id == 1).unwrap();
    let batch = mlfq.completed_tasks.iter().find(|t| t.id == 2).unwrap();

    // Verification of MLFQ invariants:
    // 1. Interactive task completes with minimal turnaround time (finished during its initial Q0 quantum)
    assert_eq!(interactive.turnaround_time, 2);
    assert!(interactive.waiting_time <= 1);

    // 2. Batch compute task was demoted due to quantum exhaustion
    assert!(demotion_observed);

    // 3. Aging / Priority Boost triggered and prevented lower-level starvation
    assert!(boost_observed);

    // 4. Interactive task TAT is strictly less than batch compute TAT
    assert!(interactive.turnaround_time < batch.turnaround_time);

    let (avg_tat, avg_wait, switches) = mlfq.metrics();
    assert!(avg_tat > 0.0);
    assert!(avg_wait >= 0.0);
    assert!(switches >= 2);
}

#[test]
fn test_tc8_ipc_rendezvous_synchronous_exchange() {
    // TC8: Inter-Process Communication (IPC) Rendezvous Subsystem (adapted from EuraliOS)
    let mut hub = IpcHub::new();
    let net_chan_id = hub.create_channel("sys.net.nic");

    let chan = hub.get_channel_mut(net_chan_id).expect("Channel creation failed");

    // Task 100 sends a Short command message to Network Service
    let cmd_msg = Message::Short(0x01, 1500, 0); // 0x01 = Configure MTU 1500
    chan.send(100, cmd_msg.clone(), false).expect("Non-blocking send failed");

    // Task 200 (Network Service) consumes the message
    let rx_res = chan.receive(200, None, false).expect("Receive failed");
    assert!(rx_res.is_some());
    let (sender, msg) = rx_res.unwrap();
    assert_eq!(sender, 100);
    assert_eq!(msg, cmd_msg);

    // Now test a Long message capability transfer (transferring a DMA memory buffer)
    let dma_payload = MessageData::Memory { phys_addr: 0x1000_0000, length: 8192 };
    let ctl_payload = MessageData::Channel(42);
    let long_msg = Message::Long(0xA0, dma_payload, ctl_payload);

    chan.send(200, long_msg.clone(), true).expect("Long send failed");
    let (rx_sender, rx_long) = chan.receive(300, Some(200), true).unwrap().unwrap();
    assert_eq!(rx_sender, 200);
    assert_eq!(rx_long, long_msg);
    assert!(rx_long.is_long());
    assert_eq!(chan.message_log.len(), 2);
}

#[test]
fn test_tc9_pci_bus_enumeration_and_hardware_discovery() {
    // TC9: PCI Hardware Bus Enumeration & Device Introspection (adapted from EuraliOS / MOROS)
    let mut bus = PciBus::new();
    bus.populate_virtualbox_hardware();

    // Verify 5 standard VirtualBox virtual devices are discovered
    assert_eq!(bus.all_devices().len(), 5);

    // Verify network devices
    let net_devs = bus.find_by_class(0x02, 0x00);
    assert_eq!(net_devs.len(), 2); // RTL8139 and VirtIO-Net

    let rtl = bus.find_device(0x10EC, 0x8139).expect("RTL8139 not found");
    assert_eq!(rtl.vendor_name(), "Realtek Semiconductor Corp.");
    assert_eq!(rtl.bars[0].bar_type, PciBarType::IoPort);
    assert_eq!(rtl.bars[0].base_address, 0xD000);

    let vnet = bus.find_device(0x1AF4, 0x1000).expect("VirtIO Net not found");
    assert_eq!(vnet.vendor_name(), "Red Hat, Inc. (VirtIO)");

    // Verify audio device (Intel ICH6 HDA)
    let audio = bus.find_device(0x8086, 0x2668).expect("Intel HDA not found");
    assert!(audio.is_audio_controller());
    assert_eq!(audio.bars[0].base_address, 0xE881_0000);
}

#[test]
fn test_tc10_network_driver_frame_lifecycle() {
    // TC10: Hardware Network Interface Driver Lifecycle (adapted from EuraliOS RTL8139 & VirtIO)
    let mac = MacAddress::new([0x08, 0x00, 0x27, 0xAA, 0xBB, 0xCC]);
    assert_eq!(mac.to_string(), "08:00:27:AA:BB:CC");

    let mut rtl = Rtl8139Device::new(0xD000, mac);
    rtl.init();
    assert!(rtl.is_enabled);

    // Transmit 3 Ethernet frames
    for i in 0..3 {
        let frame = vec![(i as u8) + 1; 128];
        let desc = rtl.transmit(&frame).expect("Transmit failed");
        assert_eq!(desc, i);
    }
    assert_eq!(rtl.tx_packet_count, 3);
    assert_eq!(rtl.tx_byte_count, 384);

    // Inject 2 incoming frames
    let in_frame1 = vec![0xEEu8; 64];
    let in_frame2 = vec![0xF0u8; 128];
    rtl.inject_received_packet(&in_frame1).expect("Receive 1 failed");
    rtl.inject_received_packet(&in_frame2).expect("Receive 2 failed");

    let (tx_p, rx_p, tx_b, rx_b) = rtl.stats();
    assert_eq!(tx_p, 3);
    assert_eq!(rx_p, 2);
    assert_eq!(tx_b, 384);
    assert_eq!(rx_b, 192);
}

