#!/usr/bin/env python3
"""
==============================================================================
VYRON Micro-OS - Telemetry, Trace Analysis & Results Visualizer
Export Engine: CSV Telemetry & Standalone Publication-Grade SVG/PNG Charts
Continuous Assessment CA-6 & CA-7 Verification Layer
==============================================================================
"""

import json
import os
import sys
import csv
import matplotlib
matplotlib.use('Agg') # Headless rendering
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def analyze_and_export(trace_file_path, results_dir):
    if not os.path.exists(trace_file_path):
        print(f"Error: Trace file '{trace_file_path}' not found.")
        return

    os.makedirs(results_dir, exist_ok=True)

    records = []
    with open(trace_file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception as e:
                    continue

    print("================================================================================")
    print("  VYRON Micro-OS: Telemetry, Trace Analysis & Visualizer Engine")
    print("================================================================================")
    print(f"  Parsed {len(records)} execution ticks from: {trace_file_path}")

    # Aggregation
    task_bursts = {}
    task_names = {}
    first_seen = {}
    last_seen = {}

    for r in records:
        tid = r["task_id"]
        task_names[tid] = r["task_name"]
        task_bursts[tid] = task_bursts.get(tid, 0) + 1
        if tid not in first_seen:
            first_seen[tid] = r["tick"]
        last_seen[tid] = r["tick"]

    total_ticks = len(records)
    n = len(task_bursts)
    sum_x = sum(task_bursts.values())
    sum_sq_x = sum(x ** 2 for x in task_bursts.values())
    jains_fairness = (sum_x ** 2) / (n * sum_sq_x) if sum_sq_x > 0 else 1.0

    print("\n--------------------------------------------------------------------------------")
    print(f"  {'PID':<6} {'Task Name':<20} {'CPU Ticks':<12} {'First Run':<12} {'Completion':<12}")
    print("--------------------------------------------------------------------------------")
    for tid in sorted(task_bursts.keys()):
        print(f"  {tid:<6} {task_names[tid]:<20} {task_bursts[tid]:<12} Tick {first_seen[tid]:<7} Tick {last_seen[tid]:<7}")
    print("--------------------------------------------------------------------------------")
    print(f"  Total CPU Active Cycles               : {sum_x} ticks")
    print(f"  Jain's Fairness Index (CPU Allocation): {jains_fairness:.4f} / 1.0000")

    # 1. Export CSV: scheduler_ticks.csv
    csv_ticks_path = os.path.join(results_dir, "scheduler_ticks.csv")
    with open(csv_ticks_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tick", "task_id", "task_name", "state", "remaining_burst"])
        for r in records:
            writer.writerow([r["tick"], r["task_id"], r["task_name"], r["state"], r["remaining"]])
    print(f"  [Exported] Ticks CSV       -> {csv_ticks_path}")

    # 2. Export CSV: task_metrics.csv
    csv_metrics_path = os.path.join(results_dir, "task_metrics.csv")
    with open(csv_metrics_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["task_id", "task_name", "cpu_ticks", "arrival_tick", "completion_tick", "turnaround_time", "waiting_time", "cpu_share_pct"])
        for tid in sorted(task_bursts.keys()):
            tat = last_seen[tid]
            wait = tat - task_bursts[tid]
            share = (task_bursts[tid] / total_ticks) * 100.0
            writer.writerow([tid, task_names[tid], task_bursts[tid], first_seen[tid], last_seen[tid], tat, wait, f"{share:.2f}"])
    print(f"  [Exported] Metrics CSV     -> {csv_metrics_path}")

    # 3. Generate Visual Gantt Chart (SVG + PNG)
    gantt_svg_path = os.path.join(results_dir, "scheduler_gantt.svg")
    gantt_png_path = os.path.join(results_dir, "scheduler_gantt.png")

    fig, ax = plt.subplots(figsize=(12, 4.5), dpi=300)
    colors = {1: "#38bdf8", 2: "#818cf8", 3: "#34d399", 4: "#f59e0b"}

    for r in records:
        tick = r["tick"] - 1 # 0-indexed for horizontal bar
        tid = r["task_id"]
        ax.broken_barh([(tick, 1)], (tid - 0.35, 0.7), facecolors=colors.get(tid, "#94a3b8"), edgecolor="#0f172a", linewidth=0.8)

    ax.set_xlabel("Scheduler Monotonic Ticks", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_ylabel("Task Identifier (PID)", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_title("VYRON Micro-OS: Round-Robin Execution Timeline (Quantum = 3 Ticks)", fontsize=13, fontweight="bold", pad=12)
    ax.set_yticks(sorted(task_bursts.keys()))
    ax.set_yticklabels([f"PID {tid}: {task_names[tid]}" for tid in sorted(task_bursts.keys())], fontsize=10)
    ax.set_xlim(0, total_ticks)
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)

    legend_patches = [mpatches.Patch(color=colors.get(tid, "#94a3b8"), label=f"PID {tid} ({task_names[tid]})") for tid in sorted(task_bursts.keys())]
    ax.legend(handles=legend_patches, loc="upper right", framealpha=0.9)

    plt.tight_layout()
    plt.savefig(gantt_svg_path, format="svg")
    plt.savefig(gantt_png_path, format="png")
    plt.close()
    print(f"  [Exported] Gantt Chart SVG -> {gantt_svg_path}")
    print(f"  [Exported] Gantt Chart PNG -> {gantt_png_path}")

    # 4. Generate Fairness Distribution Chart (SVG + PNG)
    fair_svg_path = os.path.join(results_dir, "fairness_distribution.svg")
    fair_png_path = os.path.join(results_dir, "fairness_distribution.png")

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    tids = sorted(task_bursts.keys())
    ticks = [task_bursts[t] for t in tids]
    labels = [f"PID {t}\n{task_names[t]}" for t in tids]
    bar_colors = [colors.get(t, "#38bdf8") for t in tids]

    bars = ax.bar(labels, ticks, color=bar_colors, edgecolor="#0f172a", width=0.55)
    ideal_ticks = total_ticks / len(tids)
    ax.axhline(ideal_ticks, color="#ef4444", linestyle="--", linewidth=1.5, label=f"Ideal Fair Share ({ideal_ticks:.1f} ticks)")

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.15, f"{int(yval)} ticks", ha="center", va="bottom", fontweight="bold", fontsize=10)

    ax.set_ylabel("Allocated CPU Ticks", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_title(f"VYRON Micro-OS: CPU Allocation Fairness (Jain's Index: {jains_fairness:.4f})", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(0, max(ticks) + 2)
    ax.legend(loc="lower right")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(fair_svg_path, format="svg")
    plt.savefig(fair_png_path, format="png")
    plt.close()
    print(f"  [Exported] Fairness SVG    -> {fair_svg_path}")
    print(f"  [Exported] Fairness PNG    -> {fair_png_path}")

    # Linux vs VYRON Micro-OS Comparison Matrix
    print("\n================================================================================")
    print("  Linux CFS vs VYRON Micro-OS Comparative Architecture Matrix")
    print("================================================================================")
    print(f"  {'Concept':<20} {'Linux 6.x (CFS / EEVDF)':<30} {'VYRON Micro-OS'}")
    print("  ------------------------------------------------------------------------------")
    print(f"  {'Task Abstraction':<20} {'task_struct (complex)':<30} {'Task struct (modular)'}")
    print(f"  {'Scheduler Policy':<20} {'Red-Black Tree vruntime':<30} {'Round Robin + MLFQ with Aging'}")
    print(f"  {'Time Slice':<20} {'Dynamic granularity (sysctl)':<30} {'Configurable Quantum (3 ticks)'}")
    print(f"  {'Memory Allocator':<20} {'Slab / Slub + Buddy System':<30} {'Free-List + Bump Allocator'}")
    print(f"  {'Synchronization':<20} {'Futex, Mutex, RCU, Spinlock':<30} {'AtomicBool Spinlock + Contention'}")
    print(f"  {'System Call Gate':<20} {'x86 SYSCALL / ARM SVC':<30} {'Rust SyscallDispatcher'}")
    print("================================================================================\n")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    trace_path = os.path.join(base_dir, "traces", "scheduler_trace.jsonl")
    results_dir = os.path.join(base_dir, "results")
    analyze_and_export(trace_path, results_dir)
