// ==============================================================================
// VYRON Micro-OS - Ready Queue & Round Robin CPU Scheduler
// Layer 4 & 5: Ready Queue, Round Robin Scheduling & Specialization Track A
// ==============================================================================

use std::collections::VecDeque;
use crate::task::{Task, TaskState};

#[derive(Debug, Clone)]
pub struct ContextSwitchRecord {
    pub tick: u64,
    pub previous_task_id: Option<u32>,
    pub next_task_id: Option<u32>,
    pub reason: String,
}

pub struct RoundRobinScheduler {
    pub time_quantum: u32,
    pub current_quantum_remaining: u32,
    pub ready_queue: VecDeque<Task>,
    pub current_task: Option<Task>,
    pub completed_tasks: Vec<Task>,
    pub context_switches: Vec<ContextSwitchRecord>,
    pub current_tick: u64,
}

impl RoundRobinScheduler {
    pub fn new(quantum: u32) -> Self {
        Self {
            time_quantum: quantum,
            current_quantum_remaining: quantum,
            ready_queue: VecDeque::new(),
            current_task: None,
            completed_tasks: Vec::new(),
            context_switches: Vec::new(),
            current_tick: 0,
        }
    }

    pub fn enqueue_task(&mut self, task: Task) {
        self.ready_queue.push_back(task);
    }

    pub fn tick(&mut self) -> Option<String> {
        self.current_tick += 1;

        // Increment waiting time for tasks waiting in ready queue
        for task in self.ready_queue.iter_mut() {
            task.increment_wait();
        }

        // If no active task, schedule one
        if self.current_task.is_none() {
            self.schedule_next("Initial dispatch / CPU idle");
        }

        // Step active task
        let mut event_desc = None;
        if let Some(mut active) = self.current_task.take() {
            let finished = active.execute_step(self.current_tick);
            if self.current_quantum_remaining > 0 {
                self.current_quantum_remaining -= 1;
            }

            if finished {
                event_desc = Some(format!(
                    "Task #{} ('{}') terminated at tick {} (TAT: {}, Wait: {})",
                    active.id, active.name, self.current_tick, active.turnaround_time, active.waiting_time
                ));
                self.completed_tasks.push(active);
                self.schedule_next("Task completed");
            } else if self.current_quantum_remaining == 0 {
                event_desc = Some(format!(
                    "Time quantum expired for Task #{} ('{}') at tick {}",
                    active.id, active.name, self.current_tick
                ));
                active.state = TaskState::Ready;
                self.ready_queue.push_back(active);
                self.schedule_next("Time slice expired");
            } else {
                self.current_task = Some(active);
            }
        }

        event_desc
    }

    fn schedule_next(&mut self, reason: &str) {
        let prev_id = self.current_task.as_ref().map(|t| t.id);

        if let Some(mut next_task) = self.ready_queue.pop_front() {
            let next_id = next_task.id;
            next_task.state = TaskState::Running;
            self.current_task = Some(next_task);
            self.current_quantum_remaining = self.time_quantum;

            self.context_switches.push(ContextSwitchRecord {
                tick: self.current_tick,
                previous_task_id: prev_id,
                next_task_id: Some(next_id),
                reason: reason.to_string(),
            });
        } else {
            self.current_task = None;
        }
    }

    pub fn is_idle(&self) -> bool {
        self.current_task.is_none() && self.ready_queue.is_empty()
    }

    pub fn metrics(&self) -> (f64, f64, usize) {
        if self.completed_tasks.is_empty() {
            return (0.0, 0.0, self.context_switches.len());
        }

        let total_tat: u32 = self.completed_tasks.iter().map(|t| t.turnaround_time).sum();
        let total_wait: u32 = self.completed_tasks.iter().map(|t| t.waiting_time).sum();
        let count = self.completed_tasks.len() as f64;

        (
            total_tat as f64 / count,
            total_wait as f64 / count,
            self.context_switches.len(),
        )
    }
}

// ==============================================================================
// Specialization Track A: Multi-Level Feedback Queue (MLFQ) Scheduler
// 3 Priority Levels with Dynamic Demotion, Anti-Starvation Aging & Preemption
// ==============================================================================

pub struct MlfqScheduler {
    /// 3 Priority queues:
    /// Level 0: Highest priority (interactive / short-burst), quantum = quanta[0]
    /// Level 1: Medium priority (normal tasks), quantum = quanta[1]
    /// Level 2: Lowest priority (background / batch compute), quantum = quanta[2]
    pub queues: [VecDeque<Task>; 3],
    pub time_quanta: [u32; 3],
    pub current_quantum_remaining: u32,
    pub current_queue_level: usize,
    pub current_task: Option<Task>,
    pub boost_interval: u64,
    pub ticks_since_boost: u64,
    pub completed_tasks: Vec<Task>,
    pub context_switches: Vec<ContextSwitchRecord>,
    pub current_tick: u64,
}

impl MlfqScheduler {
    pub fn new(quanta: [u32; 3], boost_interval: u64) -> Self {
        Self {
            queues: [VecDeque::new(), VecDeque::new(), VecDeque::new()],
            time_quanta: quanta,
            current_quantum_remaining: quanta[0],
            current_queue_level: 0,
            current_task: None,
            boost_interval,
            ticks_since_boost: 0,
            completed_tasks: Vec::new(),
            context_switches: Vec::new(),
            current_tick: 0,
        }
    }

    /// Enqueue a new task into the highest priority queue (Queue 0)
    pub fn enqueue_task(&mut self, mut task: Task) {
        task.state = TaskState::Ready;
        self.queues[0].push_back(task);
    }

    /// Enqueue a task explicitly into a specific queue level (0, 1, or 2)
    pub fn enqueue_task_with_priority(&mut self, mut task: Task, level: usize) {
        let target_level = level.min(2);
        task.state = TaskState::Ready;
        self.queues[target_level].push_back(task);
    }

    pub fn tick(&mut self) -> Option<String> {
        self.current_tick += 1;
        self.ticks_since_boost += 1;

        // Increment waiting time for all tasks waiting across all queues
        for queue in self.queues.iter_mut() {
            for task in queue.iter_mut() {
                task.increment_wait();
            }
        }

        let mut boost_event = None;
        // Priority Boost (Anti-Starvation Aging)
        if self.boost_interval > 0 && self.ticks_since_boost >= self.boost_interval {
            self.boost_all_tasks();
            self.ticks_since_boost = 0;
            boost_event = Some(format!(
                "Priority Boost (Aging) triggered at tick {}: all tasks promoted to Queue 0",
                self.current_tick
            ));
        }

        // If no active task, schedule the highest priority ready task
        if self.current_task.is_none() {
            self.schedule_next("Initial dispatch / CPU idle");
        }

        // Step active task
        let mut event_desc = None;
        if let Some(mut active) = self.current_task.take() {
            let finished = active.execute_step(self.current_tick);
            if self.current_quantum_remaining > 0 {
                self.current_quantum_remaining -= 1;
            }

            if finished {
                event_desc = Some(format!(
                    "Task #{} ('{}') terminated at tick {} (TAT: {}, Wait: {})",
                    active.id, active.name, self.current_tick, active.turnaround_time, active.waiting_time
                ));
                self.completed_tasks.push(active);
                self.schedule_next("Task completed");
            } else if self.current_quantum_remaining == 0 {
                // Quantum expired: demote task to next lower priority queue
                let old_level = self.current_queue_level;
                let new_level = (old_level + 1).min(2);
                active.state = TaskState::Ready;

                // Sync task priority metadata
                active.priority = match new_level {
                    0 => crate::task::TaskPriority::High,
                    1 => crate::task::TaskPriority::Normal,
                    _ => crate::task::TaskPriority::Low,
                };

                event_desc = Some(format!(
                    "Time quantum expired for Task #{} ('{}') in Q{} at tick {}; demoted to Q{}",
                    active.id, active.name, old_level, self.current_tick, new_level
                ));

                self.queues[new_level].push_back(active);
                self.schedule_next("Time slice expired / Demotion");
            } else {
                // Higher-priority preemption check:
                // If a task arrived in any queue with strictly higher priority than current level, preempt!
                let higher_priority_ready = (0..self.current_queue_level).any(|lvl| !self.queues[lvl].is_empty());
                if higher_priority_ready {
                    event_desc = Some(format!(
                        "Task #{} ('{}') preempted by higher priority queue at tick {}",
                        active.id, active.name, self.current_tick
                    ));
                    active.state = TaskState::Ready;
                    self.queues[self.current_queue_level].push_front(active); // keep at front of its queue
                    self.schedule_next("Preempted by higher-priority task");
                } else {
                    self.current_task = Some(active);
                }
            }
        }

        match (boost_event, event_desc) {
            (Some(b), Some(e)) => Some(format!("{} | {}", b, e)),
            (Some(b), None) => Some(b),
            (None, Some(e)) => Some(e),
            (None, None) => None,
        }
    }

    fn schedule_next(&mut self, reason: &str) {
        let prev_id = self.current_task.as_ref().map(|t| t.id);

        // Strict priority scan: Q0 > Q1 > Q2
        for level in 0..3 {
            if let Some(mut next_task) = self.queues[level].pop_front() {
                let next_id = next_task.id;
                next_task.state = TaskState::Running;
                self.current_task = Some(next_task);
                self.current_queue_level = level;
                self.current_quantum_remaining = self.time_quanta[level];

                self.context_switches.push(ContextSwitchRecord {
                    tick: self.current_tick,
                    previous_task_id: prev_id,
                    next_task_id: Some(next_id),
                    reason: reason.to_string(),
                });
                return;
            }
        }

        self.current_task = None;
    }

    fn boost_all_tasks(&mut self) {
        // Boost active task if running in lower queue
        if let Some(ref mut active) = self.current_task {
            self.current_queue_level = 0;
            self.current_quantum_remaining = self.time_quanta[0];
            active.priority = crate::task::TaskPriority::High;
        }

        // Drain Q1 and Q2 into Q0
        for level in 1..=2 {
            while let Some(mut task) = self.queues[level].pop_front() {
                task.priority = crate::task::TaskPriority::High;
                self.queues[0].push_back(task);
            }
        }
    }

    pub fn is_idle(&self) -> bool {
        self.current_task.is_none() && self.queues.iter().all(|q| q.is_empty())
    }

    pub fn metrics(&self) -> (f64, f64, usize) {
        if self.completed_tasks.is_empty() {
            return (0.0, 0.0, self.context_switches.len());
        }

        let total_tat: u32 = self.completed_tasks.iter().map(|t| t.turnaround_time).sum();
        let total_wait: u32 = self.completed_tasks.iter().map(|t| t.waiting_time).sum();
        let count = self.completed_tasks.len() as f64;

        (
            total_tat as f64 / count,
            total_wait as f64 / count,
            self.context_switches.len(),
        )
    }
}
