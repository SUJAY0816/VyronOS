# VYRON Micro-OS: Verification & Test Engineering Specification

**Author:** SREEHARAN  
**Curriculum Alignment:** Dr. Sujeet Jagtap — Continuous Assessment CA-6 (Section 15, 16)  
**Test Suite:** `tests/test_cases.rs` (TC1 through TC7)  
**Execution Target:** `x86_64-pc-windows-gnu` / `x86_64-unknown-none`  

---

## 1. Testing Strategy Matrix (3 Testing Levels)

```
Level 1: Unit-Level Testing        -> Queue operations, Bump allocator arithmetic, Spinlock lock/unlock.
Level 2: Mechanism-Level Testing   -> Round Robin time slicing, Dynamic quantum preemption, Free-list coalescing.
Level 3: Integrated System Testing -> Boot -> Subsystem Init -> Task Enqueue -> Timer Loop -> Syscall -> Telemetry Trace.
```

---

## 2. Test Case Specifications & Empirical Verification

### TC1: Minimum Configuration (`test_tc1_minimum_configuration`)
- **Objective:** Validate basic task execution and alternating context switching between 2 controlled tasks.
- **Workload:** 2 tasks, burst 4 ticks each, Quantum $q=2$.
- **Expected Outcome:** Both tasks complete in alternating 2-tick slices; $\ge 4$ context switches recorded.
- **Result:** **PASS** (Completed in 8 ticks, 4 context switches).

### TC2: Multiple Controlled Tasks (`test_tc2_multiple_tasks`)
- **Objective:** Validate multi-task interleaving across heterogeneous workloads.
- **Workload:** 4 tasks (bursts: 6, 3, 9, 2 ticks), Quantum $q=3$.
- **Expected Outcome:** All 4 tasks complete; $\overline{\text{TAT}} > 0$ and $\overline{W} > 0$.
- **Result:** **PASS** (Turnaround time mathematically verified against theoretical arrival model).

### TC3: Boundary Case (`test_tc3_boundary_case`)
- **Objective:** Stress the kernel with the smallest meaningful parameters.
- **Workload:** Quantum $q=1$ tick, task burst = 1 tick, heap allocation = 1 byte.
- **Expected Outcome:** Zero unsigned subtraction underflow, zero off-by-one errors.
- **Result:** **PASS** (Immediate 1-tick completions without assertion failures).

### TC4: Stress Case (`test_tc4_stress_case`)
- **Objective:** Evaluate queue stability under rapid task influx and verify mutual exclusion under high lock contention.
- **Workload:** 20 rapid sequential tasks + 500 consecutive spinlock acquisitions.
- **Expected Outcome:** All 20 tasks terminate; protected counter strictly equals 500 with zero data races.
- **Result:** **PASS** (Counter verified at 500; zero atomic contention deadlocks).

### TC5: Controlled Failure & Robustness (`test_tc5_failure_case`)
- **Objective:** Prove the kernel rejects illegal operations gracefully without panicking.
- **Workload:**
  1. Memory Out-Of-Memory: Requesting 128 bytes from a 64-byte heap.
  2. Illegal System Call: Dispatching syscall ID `999`.
- **Expected Outcome:** Allocator returns `None`; syscall returns `Err(-1)` (`ENOSYS`).
- **Result:** **PASS** (Graceful error codes returned; zero kernel panics).

### TC6: Deterministic Repeatability (`test_tc6_repeatability`)
- **Objective:** Verify deterministic execution dynamics across multiple identical runs.
- **Workload:** Execute two identical runs of 2 tasks (burst 6 ticks, quantum 3 ticks) in isolation.
- **Expected Outcome:** $\text{Ticks}_1 == \text{Ticks}_2$ and $\text{Switches}_1 == \text{Switches}_2$.
- **Result:** **PASS** (Both runs execute in exactly 12 ticks with 4 context switches).

### TC7: Specialization Track A MLFQ (`test_tc7_mlfq_dynamic_demotion_and_aging`)
- **Objective:** Validate Multi-Level Feedback Queue with 3 priority tiers, dynamic quantum demotion, and anti-starvation aging.
- **Workload:** Interactive task (`burst = 2`), long batch task (`burst = 14`), Quanta $[2, 4, 8]$, Boost interval $= 12$ ticks.
- **Expected Outcome:**
  1. Interactive task completes in $Q_0$ with minimal turnaround time ($\text{TAT}=2$).
  2. Long batch task demotes to $Q_1$ and $Q_2$.
  3. Priority boost elevates lower queues back to $Q_0$.
  4. $\text{TAT}_{\text{interactive}} < \text{TAT}_{\text{batch}}$.
- **Result:** **PASS** (All 4 MLFQ operational rules empirically verified).

---

## 3. Command Line Execution & Output Log

```text
$ cargo test --manifest-path Cargo.toml --target x86_64-pc-windows-gnu

running 7 tests
test test_tc1_minimum_configuration ... ok
test test_tc2_multiple_tasks ... ok
test test_tc3_boundary_case ... ok
test test_tc4_stress_case ... ok
test test_tc5_failure_case ... ok
test test_tc6_repeatability ... ok
test test_tc7_mlfq_dynamic_demotion_and_aging ... ok

test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```
