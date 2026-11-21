# VYRON Micro-OS: Design Invariants & Formal Safety Proofs

**Author:** SREEHARAN  
**Curriculum Alignment:** Dr. Sujeet Jagtap — Continuous Assessment CA-6 (Section 7, 26)  
**Scope:** Architectural Design Decisions, Invariant Guarantees, and Mathematical Proofs for `unsafe` Concurrency Primitives  

---

## 1. Architectural Design Decisions

### 1.1 Language Selection: Safe Systems Programming in Rust
- **Decision:** The entire micro-kernel is authored in 100% pure Rust (Edition 2021).
- **Justification:** C and C++ allow silent undefined behavior (data races, use-after-free, double-frees, null pointer dereferences). Rust eliminates entire classes of kernel bugs at compile time via its affine type system, lifetime analysis, and strict ownership rules.
- **Controlled Low-Level Access:** Unsafe pointer manipulation is quarantined behind safe, strictly verified abstractions (`Spinlock`, `UnsafeCell`).

### 1.2 Data Structures for Kernel Queues
- **Decision:** Use `VecDeque<Task>` rather than raw double-linked pointer lists.
- **Justification:** `VecDeque` provides amortized $\mathcal{O}(1)$ push and pop operations with zero manual pointer arithmetic, eliminating dangling pointer bugs during task context switching while retaining maximum hardware cache locality.

### 1.3 Quantum Selection Trade-offs
- **Decision:** Configurable time quantum with a default of $q=3$ ticks.
- **Trade-off Analysis:**
  - If $q \to \infty$: Round Robin degenerates into First-Come-First-Served (FCFS); waiting time and interactive responsiveness degrade significantly.
  - If $q \to 0$: CPU spends the majority of its clock cycles executing context-switch register saves and cache invalidations rather than useful task instructions.
  - $q=3$ strikes the optimal balance between interactive responsiveness and low context-switch overhead ($\approx 9$ switches across 22 ticks).

---

## 2. Formal Invariant Proofs for `src/sync/mod.rs`

The file `src/sync/mod.rs` encapsulates four blocks of `unsafe` Rust code:

```rust
unsafe impl<T: Send> Sync for Spinlock<T> {}
unsafe impl<T: Send> Send for Spinlock<T> {}

impl<'a, T> std::ops::Deref for SpinlockGuard<'a, T> {
    type Target = T;
    fn deref(&self) -> &Self::Target {
        unsafe { &*self.lock.data.get() }
    }
}

impl<'a, T> std::ops::DerefMut for SpinlockGuard<'a, T> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        unsafe { &mut *self.lock.data.get() }
    }
}
```

### Invariant 1: Mutual Exclusion Invariant (Soundness of `UnsafeCell::get`)
- **Theorem:** At any physical timestamp $t$, there exists at most one active `SpinlockGuard<'a, T>` reference associated with a given `Spinlock<T>`.
- **Proof:**
  1. Let $L(t) \in \{0, 1\}$ denote the atomic state of `self.locked` at timestamp $t$, where $0 \equiv \text{false}$ (unlocked) and $1 \equiv \text{true}$ (locked).
  2. Construction of `SpinlockGuard` occurs exclusively inside `Spinlock::lock()` and `Spinlock::try_lock()` when the atomic read-modify-write operation `self.locked.swap(true, Ordering::Acquire)` returns `false`.
  3. By the sequential consistency and total modification order guaranteed by the hardware memory bus on atomic operations for a single memory location (x86 `LOCK CMPXCHG` / `XCHG`), if $k$ threads execute `swap(true)` concurrently on $L = 0$, exactly one thread $T_i$ reads $0$ and transitions the state to $1$. All other $k-1$ threads read $1$.
  4. Any thread observing $1$ remains trapped in the `while self.locked.swap(true, Ordering::Acquire) { spin_loop(); }` loop and cannot instantiate a `SpinlockGuard`.
  5. Destruction of `SpinlockGuard` occurs in `Drop::drop(&mut self)`, invoking `self.lock.unlock()`, which executes `self.locked.store(false, Ordering::Release)`.
  6. Therefore, during the open temporal interval $[t_{\text{acquire}}, t_{\text{release}})$, the number of guards $|G(t)| \le 1$. $\quad\blacksquare$

### Invariant 2: Rust Reference Aliasing Invariant ($\&T \oplus \&\text{mut } T$)
- **Theorem:** The references returned by `Deref::deref` and `DerefMut::deref_mut` never violate Rust's aliasing rules (Aliasing XOR Mutability).
- **Proof:**
  1. `SpinlockGuard` does not implement `Clone` or `Copy`.
  2. By Invariant 1, only one thread $T_{\text{owner}}$ holds the guard instance.
  3. Inside $T_{\text{owner}}$:
     - `deref(&self) -> &T` is bound by the lifetime of `&self`. Multiple shared references can only coexist while `self` is borrowed immutably.
     - `deref_mut(&mut self) -> &mut T` requires an exclusive `&mut self` borrow of the guard. The Rust borrow checker statically forbids any coexisting `&self` or other `&mut self` borrow during this lifetime.
  4. Because no other thread possesses a reference to `self.lock.data.get()`, casting `*mut T` to `&T` or `&mut T` satisfies LLVM's `noalias` criteria and Rust's aliasing model. $\quad\blacksquare$

### Invariant 3: Memory Ordering & Synchronization Invariant (Happens-Before Edge)
- **Theorem:** Any modification made to $T$ by a thread $T_A$ holding the lock is visible to thread $T_B$ when $T_B$ subsequently acquires the lock. No data races occur.
- **Proof:**
  1. Thread $T_A$ releases the lock via `self.locked.store(false, Ordering::Release)` in `unlock()`.
  2. Under the C++20 / Rust memory model (ISO C++ §31.4), a `store-release` on variable $V$ *synchronizes-with* an `acquire-operation` on $V$ that reads the value stored.
  3. Thread $T_B$ acquires the lock via `self.locked.swap(true, Ordering::Acquire)`. When this operation reads the value `false` written by $T_A$, a formal *synchronizes-with* relationship is established:
     $$\text{Write}(T_A) \xrightarrow{\text{sequenced-before}} \text{Store}_{\text{Release}}(L) \xrightarrow{\text{synchronizes-with}} \text{Swap}_{\text{Acquire}}(L) \xrightarrow{\text{sequenced-before}} \text{Read}(T_B)$$
  4. By transitivity, a *happens-before* relation exists between all memory stores made by $T_A$ while holding the guard and all subsequent reads/writes by $T_B$.
  5. Hence, no data race exists under the formal definition of concurrent unsynchronized conflicting accesses. $\quad\blacksquare$

### Invariant 4: Trait Bound Soundness for `unsafe impl<T: Send> Sync for Spinlock<T>`
- **Theorem:** Requiring `T: Send` (and not `T: Sync`) is both necessary and sufficient to implement `Sync` for `Spinlock<T>`.
- **Proof:**
  1. The `Sync` trait denotes that `&Spinlock<T>` is safe to share across threads.
  2. Sharing `&Spinlock<T>` allows thread $T_1$ to acquire the lock, mutate $T$, release the lock, and subsequent thread $T_2$ to acquire the lock and access $T$.
  3. Accessing $T$ sequentially on distinct threads constitutes transferring ownership of access across thread boundaries, which requires `T: Send`.
  4. If $T$ were not `Send` (e.g., `Rc<u32>`), sharing `&Spinlock<Rc<u32>>` across threads would permit thread $T_2$ to mutate non-atomic reference counts originated in thread $T_1$, inducing undefined behavior. Hence `T: Send` is strictly necessary.
  5. `T: Sync` is *not* required because concurrent access to $T$ is impossible due to Invariant 1. Mutual exclusion transforms concurrent access into serialized access. Thus, types like `Cell<T>` (which are `Send` but `!Sync`) can be safely protected by `Spinlock`. Thus, `T: Send` is sufficient. $\quad\blacksquare$

---

## 3. Memory Subsystem Design: Coalescing Mechanics

The `FreeListAllocator` manages dynamic memory chunks using an address-ordered linked vector `Vec<FreeBlock>`.

### Coalescing Algorithm
On deallocation of a block $(\text{offset}, \text{size})$:
1. Append the block to `free_blocks`.
2. Sort `free_blocks` by `offset` ascending: $\mathcal{O}(N \log N)$.
3. Iterate with sliding index $i$:
   $$\text{If } \text{offset}_i + \text{size}_i == \text{offset}_{i+1} \implies \text{size}_i \leftarrow \text{size}_i + \text{size}_{i+1}; \quad \text{remove block } i+1$$
   $$\text{Else } i \leftarrow i + 1$$
4. Invariant: No two contiguous free blocks ever coexist in the free list after `deallocate()`. External fragmentation is eliminated for adjacent allocations.
