# VYRON Micro-OS: Rust Micro-Kernel Architecture

**Author:** SREEHARAN  
**Architecture:** x86_64 SMP Modular Micro-Kernel  
**Core Subsystems:** Round Robin Scheduling ($q=3$), 3-Level MLFQ with Dynamic Demotion & Anti-Starvation Aging, Atomic Spinlock Concurrency, Dual Allocators (Bump & Free-List with Coalescing), POSIX Syscall Dispatcher  
**Curriculum Alignment:** Dr. Sujeet Jagtap — Continuous Assessment CA-6 (15 Marks) & CA-7 (5 Marks)

---

## 1. Architectural Highlights

VYRON Micro-OS is an educational 10-layer micro-kernel constructed from first principles in safe, idiomatic Rust. It isolates hardware primitives beneath safe abstractions and exposes deterministic execution metrics to an external Python telemetry engine.

```
+--------------------------------------------------+
| Layer 10: Integrated Micro-OS Demonstration      |
+--------------------------------------------------+
| Layer 9:  System Call Interface (SYS_WRITE..EXIT)|
+--------------------------------------------------+
| Layer 8:  Memory Management (Bump + Free-List)   |
+--------------------------------------------------+
| Layer 7:  Concurrency & Spinlock Synchronization |
+--------------------------------------------------+
| Layer 6:  Timer-Driven Hardware Interrupt Layer  |
+--------------------------------------------------+
| Layer 5:  Round Robin & Track A MLFQ Scheduler   |
+--------------------------------------------------+
| Layer 4:  Ready Queue Management (VecDeque)      |
+--------------------------------------------------+
| Layer 3:  Task Representation & Hardware Context |
+--------------------------------------------------+
| Layer 2:  Kernel Diagnostics & Monotonic Log     |
+--------------------------------------------------+
| Layer 1:  Boot Entry & Kernel Proclamation       |
+--------------------------------------------------+
```

---

## 2. Directory Layout (CA-6 Section 22 Compliance)

```text
kernel/
├── Cargo.toml                          # Package manifest & metadata
├── Cargo.lock                          # Deterministic dependency tree
├── README.md                           # System overview & execution guide
├── src/
│   ├── lib.rs                          # Exported subsystems and public API
│   ├── main.rs                         # Master runtime & telemetry harness
│   ├── kernel/mod.rs                   # Layer 1 & 2: Boot & Diagnostics
│   ├── task/mod.rs                     # Layer 3: Task & Context Representation
│   ├── scheduler/mod.rs                # Layer 4 & 5: Ready Queue, Round Robin & MLFQ
│   ├── timer/mod.rs                    # Layer 6: Timer Interrupt Preemption
│   ├── sync/mod.rs                     # Layer 7: Atomic Spinlock & Contention
│   ├── memory/mod.rs                   # Layer 8: Bump & Free-List Allocator
│   └── syscall/mod.rs                  # Layer 9: System Call Gateway
├── tests/
│   └── test_cases.rs                   # Layer 10: TC1 - TC7 Verification Suite
├── traces/
│   ├── scheduler_trace.jsonl           # Monotonic JSONL tick event records
│   └── scheduler_metrics.csv           # Telemetry metrics export
├── scripts/
│   └── analyze_traces.py               # Trace parser, fairness engine & plotter
├── results/
│   ├── scheduler_ticks.csv             # Execution trace log
│   ├── task_metrics.csv                # Per-task turnaround and waiting metrics
│   ├── scheduler_gantt.svg             # Vector Gantt chart timeline
│   ├── scheduler_gantt.png             # Raster Gantt chart timeline
│   ├── fairness_distribution.svg       # CPU slice fairness distribution
│   └── fairness_distribution.png       # Raster fairness distribution
└── docs/
    ├── architecture.md                 # Layer-by-layer architectural specification
    ├── design.md                       # Design decisions & unsafe invariant proofs
    ├── testing.md                      # Test matrix & TC1-TC7 empirical results
    ├── debugging_log.md                # 8 case studies (Observe -> Localize -> Fix)
    ├── viva_preparation.md             # 20 curriculum viva Q&A + CA-7 defence matrix
    ├── technical_report.md             # 20-Section Capstone Technical Report
    ├── contribution_statement.md       # SREEHARAN's individual contribution
    └── ai_disclosure.md                # Institutional AI transparency statement
```

---

## 3. Quickstart: Building & Running

### Prerequisites
- Rust stable toolchain with `x86_64-pc-windows-gnu` or `x86_64-unknown-none` target.
- Python 3.10+ with `matplotlib`.

### Commands

1. **Execute the Integrated Micro-OS Kernel:**
   ```bash
   cargo run --manifest-path Cargo.toml --target x86_64-pc-windows-gnu
   ```

2. **Run the Complete Test Suite (TC1 to TC7):**
   ```bash
   cargo test --manifest-path Cargo.toml --target x86_64-pc-windows-gnu
   ```

3. **Generate Telemetry Traces & SVG Plots:**
   ```bash
   python scripts/analyze_traces.py
   ```

---

## 4. Empirical Evaluation Summary

- **Total Execution Ticks:** 22 ticks
- **Context Switches:** 9 switches
- **Average Turnaround Time:** 20.25 ticks
- **Average Waiting Time:** 14.75 ticks
- **Jain's Fairness Index:** 0.9603 / 1.0000 (96.03% optimal fairness)
- **Memory Coalescing:** Verified $\mathcal{O}(N)$ address-sorted defragmentation
- **Test Pass Rate:** 7/7 passed (100% clean)
