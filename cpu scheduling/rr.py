# 05/18/26
# round robin scheduling with user input time quantum and random process generation

import random
from collections import deque


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
#  ROUND ROBIN ALGORITHM
# ─────────────────────────────────────────────

def run_round_robin(processes: list[dict], quantum: int) -> dict:
    """
    Round Robin Scheduling.
    Each process gets a CPU slice of `quantum` time units.
    If it doesn't finish, it rejoins the back of the ready queue.
    New arrivals are added to the queue as time progresses.
    """
    # Work with copies so we can mutate remaining_time
    procs = sorted(
        [{**p, "remaining_time": p["burst_time"]} for p in processes],
        key=lambda p: p["arrival_time"]
    )

    completed    = {}
    gantt        = []
    ready_queue  = deque()
    current_time = 0
    index        = 0          # pointer into sorted procs for new arrivals

    # Seed the queue with processes that arrive at time 0
    while index < len(procs) and procs[index]["arrival_time"] <= current_time:
        ready_queue.append(procs[index])
        index += 1

    while ready_queue:
        proc = ready_queue.popleft()

        # How long this slice runs
        slice_time = min(quantum, proc["remaining_time"])
        start      = current_time
        end        = current_time + slice_time

        gantt.append({"pid": proc["pid"], "start": start, "end": end})

        proc["remaining_time"] -= slice_time
        current_time = end

        # Enqueue any processes that arrived during this slice
        while index < len(procs) and procs[index]["arrival_time"] <= current_time:
            ready_queue.append(procs[index])
            index += 1

        if proc["remaining_time"] == 0:
            # Process finished
            finish_time     = current_time
            waiting_time    = finish_time - proc["arrival_time"] - proc["burst_time"]
            turnaround_time = finish_time - proc["arrival_time"]

            completed[proc["pid"]] = {
                "pid":              proc["pid"],
                "arrival_time":     proc["arrival_time"],
                "burst_time":       proc["burst_time"],
                "finish_time":      finish_time,
                "waiting_time":     waiting_time,
                "turnaround_time":  turnaround_time,
            }
        else:
            # Not done — goes back to the end of the queue
            ready_queue.append(proc)

        # If queue is empty but processes haven't all arrived yet, jump ahead
        if not ready_queue and index < len(procs):
            current_time = procs[index]["arrival_time"]
            while index < len(procs) and procs[index]["arrival_time"] <= current_time:
                ready_queue.append(procs[index])
                index += 1

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
    bar   = "  |"
    times = f"  {gantt[0]['start']}"

    for seg in gantt:
        width = max((seg["end"] - seg["start"]) * 2, len(seg["pid"]) + 2)
        bar   += f" {seg['pid'].center(width)} |"
        times += f"{str(seg['end']).rjust(width + 3)}"

    print(bar)
    print(times)


def display_results(results: dict, quantum: int):
    """Prints the schedule table and averages."""
    schedule = results["schedule"]

    print("\n" + "=" * 70)
    print(f"   ROUND ROBIN RESULTS  (Quantum = {quantum}s)")
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
    print("   ROUND ROBIN CPU SCHEDULING")
    print("=" * 50)

    # Number of processes
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

    # Time quantum
    while True:
        try:
            quantum = int(input("  Time quantum (in seconds): "))
            if quantum <= 0:
                print("  ⚠  Quantum must be greater than 0.")
            else:
                break
        except ValueError:
            print("  ⚠  Please enter a whole number.")

    # Generate, run, display
    processes = generate_processes(n)
    display_processes(processes)

    results = run_round_robin(processes, quantum)
    display_gantt(results["gantt"])
    display_results(results, quantum)