// ==============================================================================
// VYRON Micro-OS - Kernel Synchronization & Spinlock Abstraction
// Layer 7: Synchronization & Concurrency Engineering (Track C)
// ==============================================================================

use std::cell::UnsafeCell;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};

pub struct SpinlockStats {
    pub total_acquisitions: AtomicU64,
    pub total_contentions: AtomicU64,
}

pub struct Spinlock<T> {
    locked: AtomicBool,
    data: UnsafeCell<T>,
    pub stats: SpinlockStats,
}

unsafe impl<T: Send> Sync for Spinlock<T> {}
unsafe impl<T: Send> Send for Spinlock<T> {}

pub struct SpinlockGuard<'a, T> {
    lock: &'a Spinlock<T>,
}

impl<T> Spinlock<T> {
    pub const fn new(data: T) -> Self {
        Self {
            locked: AtomicBool::new(false),
            data: UnsafeCell::new(data),
            stats: SpinlockStats {
                total_acquisitions: AtomicU64::new(0),
                total_contentions: AtomicU64::new(0),
            },
        }
    }

    pub fn lock(&self) -> SpinlockGuard<'_, T> {
        let mut contended = false;

        while self.locked.swap(true, Ordering::Acquire) {
            if !contended {
                self.stats.total_contentions.fetch_add(1, Ordering::Relaxed);
                contended = true;
            }
            std::hint::spin_loop();
        }

        self.stats.total_acquisitions.fetch_add(1, Ordering::Relaxed);
        SpinlockGuard { lock: self }
    }

    pub fn try_lock(&self) -> Option<SpinlockGuard<'_, T>> {
        if !self.locked.swap(true, Ordering::Acquire) {
            self.stats.total_acquisitions.fetch_add(1, Ordering::Relaxed);
            Some(SpinlockGuard { lock: self })
        } else {
            self.stats.total_contentions.fetch_add(1, Ordering::Relaxed);
            None
        }
    }

    fn unlock(&self) {
        self.locked.store(false, Ordering::Release);
    }
}

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

impl<'a, T> Drop for SpinlockGuard<'a, T> {
    fn drop(&mut self) {
        self.lock.unlock();
    }
}
