# VYRON Micro-OS: Low-Level Debugging Log

**Author:** SREEHARAN  
**Curriculum Alignment:** Dr. Sujeet Jagtap — Continuous Assessment CA-6 (Section 21)  
**Methodology:** Scientific Debugging Workflow:  
**Observe $\to$ Localize $\to$ Hypothesize $\to$ Instrument $\to$ Modify $\to$ Test $\to$ Reproduce**

---

### Case Study 1: Scheduler Starvation from Dropped Preempted Tasks
- **Observe:** After enqueuing 4 tasks, Task #1 executed for 3 ticks, after which the CPU went idle despite other tasks having non-zero remaining burst times.
- **Localize:** `scheduler/mod.rs` inside the `tick()` time-slice expiry condition.
- **Hypothesize:** When `current_quantum_remaining == 0`, the task was removed from `current_task` but omitted from `ready_queue.push_back()`, causing it to be dropped.
- **Instrument:** Added debug logging: `diag.log(LogLevel::Warn, "SCHEDULER", &format!("Preempting task {}, queue len before push: {}", active.id, self.ready_queue.len()))`.
- **Modify:** Re-inserted `self.ready_queue.push_back(active)` before calling `schedule_next()`.
- **Test:** Executed `test_tc2_multiple_tasks`; all 4 tasks now interleave properly through time slices.
- **Reproduce:** Re-ran with varying quanta ($q=1, 2, 4$); verified 100% task completion across all runs.

---

### Case Study 2: Spinlock Double-Acquisition Deadlock
- **Observe:** During concurrent simulation tests, a worker thread hung indefinitely when attempting to log within a locked critical section.
- **Localize:** `sync/mod.rs` and calling code in `main.rs`.
- **Hypothesize:** The `SpinlockGuard` was held across an invocation that internally attempted to acquire the same spinlock, leading to an infinite spin loop on `locked.swap()`.
- **Instrument:** Added an atomic thread-id tracker and acquisition counter in `SpinlockStats`.
- **Modify:** Enclosed critical section manipulations in explicit lexical blocks `{ let mut guard = lock.lock(); ... }` so the guard drops and releases the lock prior to subsequent calls.
- **Test:** Added `test_tc4_stress_case` executing 500 consecutive lock/unlock operations; passed in under 2ms.
- **Reproduce:** Verified lock statistics show 500 acquisitions and 0 unresolved deadlocks.

---

### Case Study 3: Free-List Allocator External Fragmentation & False OOM
- **Observe:** Allocating 8KB, 16KB, and 8KB, then freeing all three, followed by a request for 24KB failed with `None` despite 32KB of total heap space available.
- **Localize:** `memory/mod.rs` in `FreeListAllocator::deallocate()`.
- **Hypothesize:** Deallocated blocks were appended to `free_blocks` without coalescing contiguous address spans, leaving three disconnected 8KB/16KB fragments.
- **Instrument:** Logged free-block spans before and after deallocation: `offset: {}, size: {}`.
- **Modify:** Implemented address-sorted coalescing: after pushing a freed block, sort by `offset` and iterate with a sliding window, merging blocks where `b[i].offset + b[i].size == b[i+1].offset`.
- **Test:** Tested allocating 24KB after coalescing; allocation succeeded at offset `0x0`.
- **Reproduce:** Added automated allocation-deallocation-reallocation sequences in `test_tc3_boundary_case`.

---

### Case Study 4: Syscall Panic on Unimplemented Opcode
- **Observe:** Invoking a system call with an invalid ID caused a kernel panic instead of returning an error code.
- **Localize:** `syscall/mod.rs` `dispatch()` match arm.
- **Hypothesize:** The wildcard arm used `panic!("Unknown syscall")` instead of returning a `Result<u64, i64>`.
- **Instrument:** Wrapped syscall invocations in unit tests expecting error return codes.
- **Modify:** Changed return type to `Result<u64, i64>` and returned `Err(-1)` (POSIX `ENOSYS`) on undefined IDs.
- **Test:** Validated in `test_tc5_failure_case` asserting `dispatcher.dispatch(999, 0, 0).is_err()`.
- **Reproduce:** Verified graceful rejection across boundary syscall IDs (-1, 0, 100, 999).

---

### Case Study 5: Instruction Pointer Drift on Preempted Tasks
- **Observe:** Instruction pointers advanced even when tasks were waiting in the ready queue.
- **Localize:** `task/mod.rs` in `Task::increment_wait()`.
- **Hypothesize:** `increment_wait()` inadvertently modified `context.instruction_pointer` instead of strictly incrementing `waiting_time`.
- **Instrument:** Logged context registers on context switch.
- **Modify:** Isolated `instruction_pointer += 4` strictly inside `execute_step()` when `state == Running`.
- **Test:** Verified IP remains invariant while a task transitions between `Ready` and `Blocked`.
- **Reproduce:** Confirmed deterministic instruction pointer values at task termination in TC6.

---

### Case Study 6: Round Robin Quantum Underflow
- **Observe:** A task with 1 remaining burst tick executing in a 3-tick quantum resulted in `current_quantum_remaining` wrapping around to `u32::MAX`.
- **Localize:** `scheduler/mod.rs` during task step evaluation.
- **Hypothesize:** Decrementing `current_quantum_remaining` unconditionally without checking `remaining_burst == 0` allowed unsigned subtraction underflow.
- **Instrument:** Added assertion `debug_assert!(self.current_quantum_remaining <= self.time_quantum)`.
- **Modify:** Used `saturating_sub(1)` and reset `current_quantum_remaining` on task completion before dispatching the next task.
- **Test:** Verified with burst sizes smaller than quantum ($b=1, q=3$); quantum resets cleanly to 3.
- **Reproduce:** Ran TC3 (quantum=1 boundary) without assertion failures.

---

### Case Study 7: Free-List Double Free Block Corruption
- **Observe:** Deallocating the same memory block twice corrupted the free-list block count, inflating apparent total free memory beyond physical heap size.
- **Localize:** `memory/mod.rs` `deallocate()`.
- **Hypothesize:** `deallocate()` lacked sanity validation to check if the offset was already contained in a free block.
- **Instrument:** Checked if the target offset overlaps any existing block in `free_blocks`.
- **Modify:** Added guard check: if overlap detected, early return or ignore, preventing list duplication.
- **Test:** Tested duplicate deallocation calls; free list maintained correct total heap capacity.
- **Reproduce:** Confirmed heap invariants hold under stress tests.

---

### Case Study 8: JSONL Telemetry Trace Parsing Error in Python Engine
- **Observe:** `analyze_traces.py` failed with `JSONDecodeError: Unterminated string` when reading active traces.
- **Localize:** `main.rs` file write flushing and `analyze_traces.py` line parsing.
- **Hypothesize:** Trace records were buffered in memory and partially written before process exit.
- **Instrument:** Checked trace file size on disk before and after kernel shutdown.
- **Modify:** Added explicit file write flushing on every tick and filtered out blank/whitespace lines in `analyze_traces.py`.
- **Test:** Ran kernel followed immediately by Python analysis; parsed 22/22 ticks with 0 decode errors.
- **Reproduce:** Repeated 10 times consecutively in automated verification script.
