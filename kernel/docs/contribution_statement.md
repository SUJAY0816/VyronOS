# Individual Contribution Statement

**Candidate Name:** SREEHARAN  
**Course:** Operating Systems Concepts (25PCCS201)  
**Project:** VYRON Micro-OS Kernel Engineering Project (CA-6 & CA-7)  
**Role:** Sole Architect, Systems Programmer & Performance Analyst  

---

### 1. Subsystem Owned
As the individual author and engineer, I designed, implemented, and validated the complete VYRON Micro-OS architecture from bare metal upwards, encompassing all 10 kernel layers:
- Kernel Boot Diagnostics & Logging Subsystem (`kernel/mod.rs`)
- Task Representation & Execution Context Model (`task/mod.rs`)
- Ready Queue & Round Robin CPU Scheduler (`scheduler/mod.rs`)
- Track A Specialization: 3-Level MLFQ Scheduler with Dynamic Demotion & Aging (`scheduler/mod.rs`)
- Hardware Timer Interrupt Simulator (`timer/mod.rs`)
- Atomic Spinlock Concurrency & Contention Engine (`sync/mod.rs`)
- Dual-Mode Memory Allocator: Bump & Free-List with Coalescing (`memory/mod.rs`)
- User-Kernel System Call Interface Gateway (`syscall/mod.rs`)
- Python Trace Telemetry & Visualization Engine (`scripts/analyze_traces.py`)

### 2. Code Contributed
- Authored 100% of the Rust kernel codebase (`1,200+ lines of idiomatic Rust`).
- Implemented comprehensive unit testing suite (`tests/test_cases.rs`) validating TC1 through TC7.
- Engineered the Python telemetry parser, metrics exporter, and SVG visualization generator.
- Configured automated build, compilation, and trace execution pipelines.

### 3. Experiments Performed
- **Quantum Sensitivity Investigation:** Evaluated scheduler turnaround time and context switch overhead across time quanta $q \in \{1, 2, 3, 5\}$.
- **Fairness Benchmarking:** Evaluated CPU share allocation among 4 heterogeneous workloads, verifying a Jain's Fairness Index of 0.9603.
- **Memory Fragmentation Stress Test:** Evaluated free-list allocation efficiency and adjacent-block coalescing under fragmented allocation patterns.
- **Spinlock Contention Profiling:** Measured lock acquisition latency and contention counts across 500 iterative critical section cycles.

### 4. Documentation Contributed
- Authored the 20-Section Final Technical Report (`docs/technical_report.md`).
- Authored Subsystem Architecture, Design Invariants, and Testing Specifications (`docs/architecture.md`, `docs/design.md`, `docs/testing.md`).
- Documented 8 rigorous systems engineering case studies in the Debugging Log (`docs/debugging_log.md`).
- Formulated the 20-Question Viva Preparation Guide and CA-7 Defence Matrix (`docs/viva_preparation.md`).

### 5. Debugging Contribution
- Isolated and resolved 8 critical low-level kernel bugs, including scheduler starvation, spinlock deadlock windows, free-list fragmentation, unsigned quantum underflow, and JSONL telemetry flush race conditions.
