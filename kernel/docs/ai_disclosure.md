# Generative AI Usage Disclosure

**Author:** SREEHARAN  
**Course:** Operating Systems Concepts (25PCCS201)  
**Project:** VYRON Micro-OS Kernel Engineering Project (CA-6 & CA-7)  

---

In compliance with Section 25 of the CA-6 Course Framework and Institutional Academic Integrity Policies, this document details the nature and scope of Generative AI assistance utilized during the engineering of VYRON Micro-OS.

### 1. Permitted Scope of AI Assistance
Generative AI tools (including DeepMind Antigravity and Claude 3.5 Sonnet) were utilized for:
- Syntax assistance and Rust compiler error interpretation (e.g., borrow checker diagnostics for `UnsafeCell` and lifetime annotations).
- Cross-referencing theoretical scheduling formulations (e.g., Jain's Fairness Index mathematical formulation).
- Scaffolding Markdown report structures and Mermaid diagram syntax.
- Drafting initial boilerplate templates for unit tests and Python plotting scripts.

### 2. Critical Human Ownership & Systems Engineering Verification
In accordance with course mandates: **"Students remain responsible for every line of kernel code submitted."**
The author (SREEHARAN) independently engineered, verified, and defends all low-level systems logic:
- **Ownership & Borrowing:** Ensured zero use-after-free and enforced strict compile-time borrow limits across all kernel subsystems.
- **Unsafe Rust & Invariants:** All `unsafe` blocks in `Spinlock` (`UnsafeCell::get()`) were designed with explicit invariants, ensuring that raw pointers are only dereferenced while the atomic lock flag is held by the current thread.
- **Atomic Memory Ordering:** Personally selected `Ordering::Acquire` for lock acquisition and `Ordering::Release` for lock release, preventing memory reordering across critical section boundaries.
- **Kernel State Machine:** Handled all task state transitions (`Ready`, `Running`, `Blocked`, `Terminated`) and context switch accounting by hand.
- **Zero Unverified Code:** No AI-generated code was accepted without manual line-by-line inspection, architectural refactoring, and automated test validation.
