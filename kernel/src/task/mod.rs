// ==============================================================================
// VYRON Micro-OS - Task Abstraction & State Machine
// Layer 3: Task Representation
// ==============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskState {
    Ready,
    Running,
    Blocked,
    Terminated,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum TaskPriority {
    Low = 1,
    Normal = 2,
    High = 3,
}

#[derive(Debug, Clone)]
pub struct TaskContext {
    pub instruction_pointer: usize,
    pub stack_pointer: usize,
    pub registers: [u64; 8],
}

impl TaskContext {
    pub fn new(entry_point: usize, stack_top: usize) -> Self {
        Self {
            instruction_pointer: entry_point,
            stack_pointer: stack_top,
            registers: [0; 8],
        }
    }
}

#[derive(Debug, Clone)]
pub struct Task {
    pub id: u32,
    pub name: String,
    pub state: TaskState,
    pub priority: TaskPriority,
    pub total_burst: u32,
    pub remaining_burst: u32,
    pub waiting_time: u32,
    pub turnaround_time: u32,
    pub arrival_time: u64,
    pub completion_time: Option<u64>,
    pub context: TaskContext,
}

impl Task {
    pub fn new(id: u32, name: &str, burst_ticks: u32, priority: TaskPriority, arrival: u64) -> Self {
        Self {
            id,
            name: name.to_string(),
            state: TaskState::Ready,
            priority,
            total_burst: burst_ticks,
            remaining_burst: burst_ticks,
            waiting_time: 0,
            turnaround_time: 0,
            arrival_time: arrival,
            completion_time: None,
            context: TaskContext::new(0x1000 + (id as usize * 0x100), 0x8000),
        }
    }

    pub fn execute_step(&mut self, current_tick: u64) -> bool {
        if self.state != TaskState::Running {
            self.state = TaskState::Running;
        }

        if self.remaining_burst > 0 {
            self.remaining_burst -= 1;
            self.context.instruction_pointer += 4;
        }

        if self.remaining_burst == 0 {
            self.state = TaskState::Terminated;
            self.completion_time = Some(current_tick);
            self.turnaround_time = (current_tick - self.arrival_time) as u32;
            true // Task completed
        } else {
            false // Still has work
        }
    }

    pub fn increment_wait(&mut self) {
        if self.state == TaskState::Ready {
            self.waiting_time += 1;
        }
    }
}
