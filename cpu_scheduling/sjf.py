# 05/17/26
# shortest job first algorithm with random process generation

import random


# ─────────────────────────────────────────────
#  RANDOM PROCESS GENERATOR
# ─────────────────────────────────────────────

def generate_processes(n: int) -> list[dict]:
    """
    Generates n processes with random arrival and burst times.

    Controlled ranges:
      - arrival_time : 0 to 20 (unique, sorted)
      - burst_time   : 1 to 10
    """
    arrival_times = sorted(random.sample(range(0, 21), n))

    processes = []
    for i in range(n):
        processes.append({
            "pid":          f"P{i + 1}",
            "arrival_time": arrival_times[i],
            "burst_time":   random.randint(1, 10),
        })

    return processes


# ─────────────────────────────────────────────
#  NON-PREEMPTIVE SJF
# ─────────────────────────────────────────────

def run_sjf(processes: list[dict]) -> dict:
    """
    Non-Preemptive Shortest Job First.
    At each decision point, picks the arrived process with the shortest burst.
    Once a process starts, it runs until completion — no interruptions.
    """
    remaining = [p.copy() for p in processes]
    schedule  = []
    gantt     = []
    current_time = 0

    while remaining:
        # All processes that have arrived by current_time
        available = [p for p in remaining if p["arrival_time"] <= current_time]

        if not available:
            # CPU idle — jump to the next arrival
            current_time = min(p["arrival_time"] for p in remaining)
            continue

        # Pick the one with the shortest burst time (tie-break: earliest arrival)
        chosen = min(available, key=lambda p: (p["burst_time"], p["arrival_time"]))
        remaining.remove(chosen)

        start_time      = current_time
        finish_time     = current_time + chosen["burst_time"]
        waiting_time    = start_time - chosen["arrival_time"]
        turnaround_time = finish_time - chosen["arrival_time"]

        schedule.append({
            "pid":              chosen["pid"],
            "arrival_time":     chosen["arrival_time"],
            "burst_time":       chosen["burst_time"],
            "start_time":       start_time,
            "finish_time":      finish_time,
            "waiting_time":     waiting_time,
            "turnaround_time":  turnaround_time,
        })

        gantt.append({
            "pid":   chosen["pid"],
            "start": start_time,
            "end":   finish_time,
        })

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
#  PREEMPTIVE SRTF
# ─────────────────────────────────────────────

def run_srtf(processes: list[dict]) -> dict:
    """
    Preemptive Shortest Remaining Time First (SRTF).
    At every time unit, checks if a newly arrived process has a shorter
    remaining time than the current one — if so, it preempts.
    Tracks Gantt chart segments each time the running process changes.
    """
    # Work with copies so we can mutate remaining_time freely
    procs = [{**p, "remaining_time": p["burst_time"]} for p in processes]

    completed   = {}   # pid -> result dict
    gantt       = []   # list of { pid, start, end }
    current_time = 0
    total_burst  = sum(p["burst_time"] for p in processes)

    current_proc  = None
    segment_start = 0

    while current_time < total_burst + max(p["arrival_time"] for p in processes):
        # Processes available at this moment
        available = [p for p in procs if p["arrival_time"] <= current_time and p["remaining_time"] > 0]

        if not available:
            # Record any running segment, then idle
            if current_proc is not None:
                gantt.append({"pid": current_proc["pid"], "start": segment_start, "end": current_time})
                current_proc = None
            current_time += 1
            continue

        # Shortest remaining time (tie-break: earliest arrival)
        next_proc = min(available, key=lambda p: (p["remaining_time"], p["arrival_time"]))

        # Preemption check — if a different process takes over, close the current segment
        if current_proc is None or next_proc["pid"] != current_proc["pid"]:
            if current_proc is not None:
                gantt.append({"pid": current_proc["pid"], "start": segment_start, "end": current_time})
            current_proc  = next_proc
            segment_start = current_time

        # Run for 1 time unit
        current_proc["remaining_time"] -= 1
        current_time += 1

        # Check if this process just finished
        if current_proc["remaining_time"] == 0:
            gantt.append({"pid": current_proc["pid"], "start": segment_start, "end": current_time})

            finish_time     = current_time
            waiting_time    = finish_time - current_proc["arrival_time"] - current_proc["burst_time"]
            turnaround_time = finish_time - current_proc["arrival_time"]

            completed[current_proc["pid"]] = {
                "pid":              current_proc["pid"],
                "arrival_time":     current_proc["arrival_time"],
                "burst_time":       current_proc["burst_time"],
                "finish_time":      finish_time,
                "waiting_time":     waiting_time,
                "turnaround_time":  turnaround_time,
            }

            current_proc = None

        # Stop once all processes are done
        if len(completed) == len(procs):
            break

    # Sort results by PID order for clean display
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
    print(f"  {'PID':<8} {'Arrival Time':>14} {'Burst Time':>12}")
    print("  " + "-" * 36)
    for p in processes:
        print(f"  {p['pid']:<8} {p['arrival_time']:>12}s {p['burst_time']:>11}s")


def display_gantt(gantt: list[dict]):
    """Prints a simple text Gantt chart."""
    print("\n  Gantt Chart:")
    bar = "  |"
    times = f"  {gantt[0]['start']}"

    for seg in gantt:
        width  = max((seg["end"] - seg["start"]) * 2, len(seg["pid"]) + 2)
        label  = seg["pid"].center(width)
        bar   += f" {label} |"
        times += f"{str(seg['end']).rjust(width + 3)}"

    print(bar)
    print(times)


def display_results(results: dict, mode: str):
    """Prints the schedule table and averages."""
    schedule = results["schedule"]

    print("\n" + "=" * 70)
    print(f"   {mode} RESULTS")
    print("=" * 70)
    print(f"  {'PID':<8} {'Arrival':>9} {'Burst':>7} {'Finish':>8} {'Waiting':>9} {'Turnaround':>12}")
    print("  " + "-" * 57)

    for p in schedule:
        print(
            f"  {p['pid']:<8}"
            f"  {p['arrival_time']:>7}s"
            f"  {p['burst_time']:>5}s"
            f"  {p['finish_time']:>6}s"
            f"  {p['waiting_time']:>7}s"
            f"  {p['turnaround_time']:>10}s"
        )

    print("  " + "-" * 57)
    print(f"\n  Average Waiting Time    :  {results['avg_waiting_time']}s")
    print(f"  Average Turnaround Time :  {results['avg_turnaround_time']}s")
    print("=" * 70)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   SJF / SRTF CPU SCHEDULING")
    print("=" * 50)

    # Ask only for the number of processes
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

    # ── Non-Preemptive SJF ──
    print("\n" + "─" * 50)
    print("  MODE 1 — Non-Preemptive SJF")
    print("─" * 50)
    sjf_results = run_sjf(processes)
    display_gantt(sjf_results["gantt"])
    display_results(sjf_results, "NON-PREEMPTIVE SJF")

    # ── Preemptive SRTF ──
    print("\n" + "─" * 50)
    print("  MODE 2 — Preemptive SRTF")
    print("─" * 50)
    srtf_results = run_srtf(processes)
    display_gantt(srtf_results["gantt"])
    display_results(srtf_results, "PREEMPTIVE SRTF")