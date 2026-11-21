// ==============================================================================
// VYRON Micro-OS - Kernel Memory Allocators
// Layer 8: Memory Management & Specialization Track B
// ==============================================================================

pub struct BumpAllocator {
    heap_start: usize,
    heap_size: usize,
    next: usize,
    allocations: usize,
}

impl BumpAllocator {
    pub fn new(heap_start: usize, heap_size: usize) -> Self {
        Self {
            heap_start,
            heap_size,
            next: heap_start,
            allocations: 0,
        }
    }

    pub fn allocate(&mut self, size: usize, align: usize) -> Option<usize> {
        let alloc_start = (self.next + align - 1) & !(align - 1);
        let alloc_end = alloc_start.checked_add(size)?;

        if alloc_end <= self.heap_start + self.heap_size {
            self.next = alloc_end;
            self.allocations += 1;
            Some(alloc_start)
        } else {
            None // Out of Memory
        }
    }

    pub fn reset(&mut self) {
        self.next = self.heap_start;
        self.allocations = 0;
    }

    pub fn used_bytes(&self) -> usize {
        self.next - self.heap_start
    }

    pub fn free_bytes(&self) -> usize {
        self.heap_size - self.used_bytes()
    }
}

#[derive(Debug, Clone)]
pub struct FreeBlock {
    pub offset: usize,
    pub size: usize,
}

pub struct FreeListAllocator {
    pub total_size: usize,
    pub free_blocks: Vec<FreeBlock>,
    pub allocated_bytes: usize,
    pub peak_allocated_bytes: usize,
}

impl FreeListAllocator {
    pub fn new(total_size: usize) -> Self {
        Self {
            total_size,
            free_blocks: vec![FreeBlock { offset: 0, size: total_size }],
            allocated_bytes: 0,
            peak_allocated_bytes: 0,
        }
    }

    pub fn allocate(&mut self, size: usize) -> Option<usize> {
        // First-fit search
        for i in 0..self.free_blocks.len() {
            if self.free_blocks[i].size >= size {
                let block = self.free_blocks.remove(i);
                let allocated_offset = block.offset;

                if block.size > size {
                    let remainder = FreeBlock {
                        offset: block.offset + size,
                        size: block.size - size,
                    };
                    self.free_blocks.insert(i, remainder);
                }

                self.allocated_bytes += size;
                if self.allocated_bytes > self.peak_allocated_bytes {
                    self.peak_allocated_bytes = self.allocated_bytes;
                }

                return Some(allocated_offset);
            }
        }
        None // Fragmentation or Out of Memory
    }

    pub fn deallocate(&mut self, offset: usize, size: usize) {
        self.free_blocks.push(FreeBlock { offset, size });
        self.free_blocks.sort_by_key(|b| b.offset);

        // Coalesce adjacent free blocks
        let mut i = 0;
        while i + 1 < self.free_blocks.len() {
            if self.free_blocks[i].offset + self.free_blocks[i].size == self.free_blocks[i + 1].offset {
                let next_size = self.free_blocks[i + 1].size;
                self.free_blocks[i].size += next_size;
                self.free_blocks.remove(i + 1);
            } else {
                i += 1;
            }
        }

        self.allocated_bytes = self.allocated_bytes.saturating_sub(size);
    }
}
