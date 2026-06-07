# 05/17/26
# priority queue, preemptive and non-preemptive algorithms with random process generation

import random


# ─────────────────────────────────────────────
#  RANDOM PROCESS GENERATOR
# ─────────────────────────────────────────────

def generate_processes(n: int) -> list[dict]:
    """
    Generates n processes with random arrival, burst, and priority.

    Controlled ranges:
      - arrival_time : 0 to 20 (unique, sorted)
      - burst_time   : 1 to 10
      - priority     : 1 to 5  (1 = highest)
    """
    arrival_times = sorted(random.sample(range(0, 21), n))

    processes = []
    for i in range(n):
        processes.append({
            "pid":          f"P{i + 1}",
            "arrival_time": arrival_times[i],
            "burst_time":   random.randint(1, 10),
            "priority":     random.randint(1, 5),
        })

    return processes


# ─────────────────────────────────────────────
#  NON-PREEMPTIVE PRIORITY
# ─────────────────────────────────────────────

def run_priority_np(processes: list[dict]) -> dict:
    """
    Non-Preemptive Priority Scheduling.
    At each decision point, picks the arrived process with the highest priority
    (lowest number). Once it starts, it runs to completion.
    Tie-break: earliest arrival time.
    """
    remaining = [p.copy() for p in processes]
    schedule  = []
    gantt     = []
    current_time = 0

    while remaining:
        available = [p for p in remaining if p["arrival_time"] <= current_time]

        if not available:
            next_arrival = min(p["arrival_time"] for p in remaining)
            gantt.append({"pid": "IDLE", "start": current_time, "end": next_arrival})
            current_time = next_arrival
            continue

        # Lowest priority number = highest priority; tie-break by arrival
        chosen = min(available, key=lambda p: (p["priority"], p["arrival_time"]))
        remaining.remove(chosen)

        start_time      = current_time
        finish_time     = current_time + chosen["burst_time"]
        waiting_time    = start_time - chosen["arrival_time"]
        turnaround_time = finish_time - chosen["arrival_time"]

        schedule.append({
            "pid":              chosen["pid"],
            "arrival_time":     chosen["arrival_time"],
            "burst_time":       chosen["burst_time"],
            "priority":         chosen["priority"],
            "start_time":       start_time,
            "finish_time":      finish_time,
            "waiting_time":     waiting_time,
            "turnaround_time":  turnaround_time,
        })

        gantt.append({"pid": chosen["pid"], "start": start_time, "end": finish_time})
        current_time = finish_time

    n = len(schedule)
    avg_waiting    = round(sum(p["waiting_time"]    for p in schedule) / n, 2)
    avg_turnaround = round(sum(p["turnaround_time"] for p in schedule) / n, 2)

    return {
        "schedule":            schedule,
        "gantt":               gantt,
        "avg_waiting_time":    avg_waiting,
        "avg_turnaround_time": avg_turnaround,
    }


# ─────────────────────────────────────────────
#  PREEMPTIVE PRIORITY
# ─────────────────────────────────────────────

def run_priority_p(processes: list[dict]) -> dict:
    """
    Preemptive Priority Scheduling.
    At every time unit, checks if a newly arrived process has a higher priority
    (lower number) than the currently running one — if so, it preempts.
    Tie-break: earliest arrival time.
    """
    procs = [{**p, "remaining_time": p["burst_time"]} for p in processes]

    completed     = {}
    gantt         = []
    current_time  = 0
    current_proc  = None
    segment_start = 0
    total_time    = max(p["arrival_time"] for p in processes) + sum(p["burst_time"] for p in processes)

    while current_time <= total_time:
        available = [p for p in procs if p["arrival_time"] <= current_time and p["remaining_time"] > 0]

        if not available:
            if current_proc is not None:
                gantt.append({"pid": current_proc["pid"], "start": segment_start, "end": current_time})
                current_proc = None
            if len(completed) == len(procs):
                break
            current_time += 1
            continue

        # Highest priority = lowest number; tie-break by arrival
        next_proc = min(available, key=lambda p: (p["priority"], p["arrival_time"]))

        # Preemption — close current segment if a different process takes over
        if current_proc is None or next_proc["pid"] != current_proc["pid"]:
            if current_proc is not None:
                gantt.append({"pid": current_proc["pid"], "start": segment_start, "end": current_time})
            current_proc  = next_proc
            segment_start = current_time

        current_proc["remaining_time"] -= 1
        current_time += 1

        if current_proc["remaining_time"] == 0:
            gantt.append({"pid": current_proc["pid"], "start": segment_start, "end": current_time})

            finish_time     = current_time
            waiting_time    = finish_time - current_proc["arrival_time"] - current_proc["burst_time"]
            turnaround_time = finish_time - current_proc["arrival_time"]

            completed[current_proc["pid"]] = {
                "pid":              current_proc["pid"],
                "arrival_time":     current_proc["arrival_time"],
                "burst_time":       current_proc["burst_time"],
                "priority":         current_proc["priority"],
                "finish_time":      finish_time,
                "waiting_time":     waiting_time,
                "turnaround_time":  turnaround_time,
            }
            current_proc = None

        if len(completed) == len(procs):
            break

    schedule = sorted(completed.values(), key=lambda p: int(p["pid"][1:]))

    n = len(schedule)
    avg_waiting    = round(sum(p["waiting_time"]    for p in schedule) / n, 2)
    avg_turnaround = round(sum(p["turnaround_time"] for p in schedule) / n, 2)

    return {
        "schedule":            schedule,
        "gantt":               gantt,
        "avg_waiting_time":    avg_waiting,
        "avg_turnaround_time": avg_turnaround,
    }


# ─────────────────────────────────────────────
#  DISPLAY
# ─────────────────────────────────────────────

def display_processes(processes: list[dict]):
    """Shows the randomly generated processes."""
    print("\n  Generated Processes:")
    print(f"  {'PID':<8} {'Arrival':>9} {'Burst':>7} {'Priority':>10}")
    print("  " + "-" * 38)
    for p in processes:
        print(f"  {p['pid']:<8} {p['arrival_time']:>7}s {p['burst_time']:>6}s {p['priority']:>9}")


def display_gantt(gantt: list[dict]):
    """Prints a simple text Gantt chart."""
    print("\n  Gantt Chart:")
    bar   = "  |"
    times = f"  {gantt[0]['start']}"

    for seg in gantt:
        width = max((seg["end"] - seg["start"]) * 2, len(seg["pid"]) + 2)
        bar   += f" {seg['pid'].center(width)} |"
        times += f"{str(seg['end']).rjust(width + 3)}"

    print(bar)
    print(times)


def display_results(results: dict, mode: str):
    """Prints the schedule table and averages."""
    schedule = results["schedule"]

    print("\n" + "=" * 75)
    print(f"   {mode} RESULTS")
    print("=" * 75)
    print(f"  {'PID':<8} {'Arrival':>9} {'Burst':>7} {'Priority':>10} {'Finish':>8} {'Waiting':>9} {'Turnaround':>12}")
    print("  " + "-" * 67)
    for p in schedule:
        print(
            f"  {p['pid']:<8}"
            f"  {p['arrival_time']:>7}s"
            f"  {p['burst_time']:>5}s"
            f"  {p['priority']:>9}"
            f"  {p['finish_time']:>6}s"
            f"  {p['waiting_time']:>7}s"
            f"  {p['turnaround_time']:>10}s"
        )
    print("  " + "-" * 67)
    print(f"\n  Average Waiting Time    :  {results['avg_waiting_time']}s")
    print(f"  Average Turnaround Time :  {results['avg_turnaround_time']}s")
    print("=" * 75)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   PRIORITY CPU SCHEDULING")
    print("=" * 50)

    # Ask for number of processes
    while True:
        try:
            n = int(input("\n  How many processes? "))
            if n <= 0:
                print("  ⚠  Please enter a number greater than 0.")
            elif n > 20:
                print("  ⚠  Maximum is 20 processes.")
            else:
                break
        except ValueError:
            print("  ⚠  Please enter a whole number.")

    # Generate once — both modes use the same data
    processes = generate_processes(n)
    display_processes(processes)

    # ── Non-Preemptive ──
    print("\n" + "─" * 50)
    print("  MODE 1 — Non-Preemptive Priority")
    print("─" * 50)
    np_results = run_priority_np(processes)
    display_gantt(np_results["gantt"])
    display_results(np_results, "NON-PREEMPTIVE PRIORITY")

    # ── Preemptive ──
    print("\n" + "─" * 50)
    print("  MODE 2 — Preemptive Priority")
    print("─" * 50)
    p_results = run_priority_p(processes)
    display_gantt(p_results["gantt"])
    display_results(p_results, "PREEMPTIVE PRIORITY")