# VYRON Micro-OS: Comprehensive Viva Preparation & CA-7 Defence Guide

**Author:** SREEHARAN  
**Course:** Operating Systems Concepts (25PCCS201)  
**Curriculum Alignment:** Dr. Sujeet Jagtap — Continuous Assessment CA-6 (Section 32) & CA-7 (Sections 1–8)  
**Target:** 20 Core Viva Questions + 7-Level Adaptive Engineering Defence Matrix  

---

## 1. Twenty Core Curriculum Viva Questions & Answers

### Q1: What happens immediately after the kernel starts?
**Answer:** The kernel executes `boot_banner()` in `kernel/mod.rs` to announce its identity (`VYRON Micro-OS Kernel v1.0 LTS x86_64 SMP`), initializes `KernelDiagnostics` capturing monotonic microsecond timestamps via `Instant::now()`, and brings up subsystems in strict order: memory allocators (`FreeListAllocator`), atomic synchronization primitives, the periodic hardware timer, the syscall dispatcher, and finally configures the ready queue and schedules tasks.

### Q2: How is a task represented?
**Answer:** As a `Task` struct in `task/mod.rs`. It encapsulates a complete Process Control Block (PCB): task PID (`u32`), name, `TaskState` (`Ready`, `Running`, `Blocked`, `Terminated`), `TaskPriority` (`Low`, `Normal`, `High`), total burst, remaining burst, arrival tick, completion tick, wait time, turnaround time, and a simulated hardware context (`TaskContext`) containing instruction pointer, stack pointer, and 8 general-purpose registers.

### Q3: How does the scheduler select the next task?
**Answer:** In `RoundRobinScheduler::schedule_next()`, it pops the head task from the FIFO ready queue (`ready_queue.pop_front()`), sets its state to `TaskState::Running`, resets its `current_quantum_remaining` to the global quantum ($q=3$), and appends a `ContextSwitchRecord` to log $(t, \text{prev\_pid}, \text{next\_pid}, \text{reason})$. In the MLFQ scheduler, it scans queues $Q_0 \to Q_1 \to Q_2$, dispatching from the highest non-empty priority tier.

### Q4: Why did you choose Round Robin?
**Answer:** Round Robin provides starvation-free, fair CPU sharing, bounded response times for interactive workloads, and deterministic preemption dynamics. Its mathematical simplicity enables quantifiable evaluation of time-slice behavior and context-switch overhead via Jain's Fairness Index.

### Q5: What triggers a scheduling decision?
**Answer:** Two events:
1. **Time quantum expiration:** When periodic timer ticks decrement `current_quantum_remaining` to 0, forcing preemption.
2. **Voluntary yield or task completion:** When a task terminates (`remaining_burst == 0`) or calls `sys_yield()`, freeing the CPU to dispatch the next ready task immediately.

### Q6: What happens during a timer tick?
**Answer:** The hardware timer fires an interrupt, incrementing `current_tick`. The scheduler:
1. Increments `waiting_time` for every task idling in the ready queue.
2. Decrements `remaining_burst` and steps `instruction_pointer += 4` for the running task.
3. Decrements `current_quantum_remaining`.
4. Checks whether the task finished (triggering termination) or the quantum expired (triggering preemption and re-enqueueing to the tail).

### Q7: How is shared kernel data protected?
**Answer:** Through an atomic spinlock (`Spinlock<T>` in `sync/mod.rs`) wrapping an `UnsafeCell<T>`. Access requires calling `lock()`, which executes an atomic test-and-set via `swap(true, Ordering::Acquire)`. Data is only accessible via the RAII `SpinlockGuard`, which automatically releases the lock upon dropping.

### Q8: Why is synchronization required?
**Answer:** To guarantee mutual exclusion and eliminate race conditions when concurrent tasks, threads, or interrupt handlers access shared kernel structures (such as task tables, memory free-lists, and diagnostic logs) simultaneously on symmetric multiprocessing (SMP) hardware.

### Q9: How does your allocator work?
**Answer:** VYRON implements two allocators:
1. `BumpAllocator`: Fast sequential pointer incrementation with power-of-two alignment for early boot.
2. `FreeListAllocator`: Linked vector of `FreeBlock { offset, size }`. It searches for a block using First-Fit, splits oversized blocks, and on deallocation, sorts blocks by address and coalesces contiguous adjacent blocks into larger spans, eliminating external fragmentation.

### Q10: What happens when allocation fails?
**Answer:** The allocators return `None` rather than panicking or crashing. Kernel callers and system calls receive an Out-Of-Memory indication and return a standard negative error code (`Err(-1)` / `-ENOMEM`) to user space.

### Q11: Where is `unsafe` used and why?
**Answer:** `unsafe` is strictly quarantined in `sync/mod.rs` within `SpinlockGuard`'s `Deref` and `DerefMut` implementations (`unsafe { &*self.lock.data.get() }`). It is required because Rust's borrow checker forbids multiple mutable references to shared data; `UnsafeCell` provides interior mutability, which is safe because our atomic flag guarantees mutual exclusion.

### Q12: What invariant does your `unsafe` code rely on?
**Answer:** That the underlying data inside `UnsafeCell` is *only* accessed while `locked` holds `true`, and that exactly one thread holds the `SpinlockGuard` at any given instant.

### Q13: What happens if two tasks access the same resource?
**Answer:** The first task sets `locked = true` and proceeds. The second task attempts `swap(true)`, reads `true`, and enters a bounded spin loop (`std::hint::spin_loop()`) while incrementing the contention counter in `SpinlockStats`, waiting until the first task drops its guard and resets `locked = false`.

### Q14: How did you test the scheduler?
**Answer:** Through automated unit and mechanism tests in `tests/test_cases.rs`: minimum 2-task alternation (TC1), multi-task interleaving (TC2), quantum boundary values (TC3), stress workloads (TC4), failure cases (TC5), deterministic replayability across runs (TC6), and MLFQ dynamic demotion with anti-starvation aging (TC7).

### Q15: How did you establish that the scheduler is actually working?
**Answer:** By capturing tick-by-tick JSONL execution traces and running the Python analysis engine. The output proves that tasks execute in exact time-sliced order (`[T1][T1][T2][T2][T2][T3]...`), with an average turnaround of 20.25 ticks and an empirical Jain's Fairness Index of 0.9603.

### Q16: How is your Micro-OS different from Linux?
**Answer:** Linux employs the complex Completely Fair Scheduler (CFS/EEVDF) based on red-black trees of virtual runtime, multi-level buddy page allocators with SLUB caching, and hardware MMU paging with ring-3 privilege separation. VYRON Micro-OS simplifies these into a clean 10-layer educational micro-kernel: a FIFO VecDeque Round Robin scheduler with MLFQ extension, first-fit free-list allocator, and single-address-space task model that makes core mechanisms observable and quantifiable.

### Q17: What did CA-5 teach you that helped this project?
**Answer:** CA-5 (Linux Systems Engineering) provided hands-on experience with process lifecycle inspection (`/proc`), `strace` system call tracking, CPU scheduling priorities (`nice`/`chrt`), and kernel ring buffer diagnostics (`dmesg`), which directly guided the design of VYRON's diagnostics, syscall dispatcher, and trace format.

### Q18: What CA-4 research question could be extended into your Micro-OS?
**Answer:** The investigation of time quantum size versus context-switch overhead and CPU fairness. In CA-4, this was analyzed conceptually and via user-space simulation; in CA-6, it is directly implemented and measured in kernel code via `RoundRobinScheduler` and `ContextSwitchRecord`.

### Q19: What would you implement next?
**Answer:** A Multilevel Feedback Queue (MLFQ) scheduler with dynamic priority boosting to reward I/O-bound tasks (already prototyped in Track A), followed by x86_64 CR3 two-level paging for hardware-enforced memory isolation.

### Q20: What is the most important limitation of your current system?
**Answer:** The reliance on a single-threaded cooperative/simulated timer loop in `main.rs` rather than true asynchronous hardware interrupt handling via an APIC timer vector, meaning tasks must yield control at tick boundaries.

---

## 2. CA-7 Adaptive 7-Level Engineering Defence Matrix

| Level | Viva Stage | Examiner Prompt | Candidate Engineering Defence |
| :---: | :--- | :--- | :--- |
| **L1** | **Demonstrate** | *"Run the system and show evidence that tasks are actually switching."* | Execute `cargo run` and `python scripts/analyze_traces.py`. Point to the 22-tick timeline trace, the 9 context switches recorded in telemetry, and the generated SVG Gantt chart in `results/`. |
| **L2** | **Explain** | *"Walk through the code path when a quantum expires."* | Open `scheduler/mod.rs:72-80`. Show how `current_quantum_remaining == 0` causes the task to transition to `TaskState::Ready`, gets appended to `ready_queue.push_back(active)`, and invokes `schedule_next()`. |
| **L3** | **Modify** | *"What happens if we increase quantum $q$ from 3 to 10?"* | Turnaround time for long tasks improves slightly and context switches decrease, but short interactive tasks suffer severe queue latency (waiting time increases significantly), and fairness drops. |
| **L4** | **Break** | *"What happens if a task enters an infinite loop without yielding?"* | In a cooperative system, the kernel hangs. In our timer-driven preemptive design, when APIC interrupts fire, the interrupt handler forces a context switch regardless of user code. |
| **L5** | **Diagnose** | *"Why did Jain's Fairness Index register 0.9603 rather than 1.0000?"* | Because tasks have heterogeneous total burst requirements (Task 1: 7 ticks, Task 4: 4 ticks); tasks finishing earlier stop receiving CPU slices, creating slight natural variance in final tick totals. |
| **L6** | **Justify** | *"Why use `swap(true, Ordering::Acquire)` instead of `compare_exchange` in Spinlock?"* | `swap` provides unconditional atomic exchange with lower instruction overhead on x86 (`XCHG`), which automatically implies locked memory bus semantics without CAS loop retry branches. |
| **L7** | **Extend** | *"How would you implement priority aging in MLFQ?"* | In `increment_wait()`, if a task's `waiting_time` exceeds an aging threshold (e.g., 10 ticks), promote its `TaskPriority` to prevent starvation in priority queues. |
