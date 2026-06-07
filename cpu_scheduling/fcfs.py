# 05/17/26
# first come, first served algorithm with random process generation

import random


# ─────────────────────────────────────────────
#  RANDOM PROCESS GENERATOR
# ─────────────────────────────────────────────

def generate_processes(n: int) -> list[dict]:
    """
    Generates n processes with random arrival and burst times.

    Controlled ranges:
      - arrival_time : 0 to 20 (seconds), unique and sorted
      - burst_time   : 1 to 10 (seconds)
    """
    # Generate n unique arrival times so no two processes arrive at the same time
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
#  CORE FCFS ALGORITHM
# ─────────────────────────────────────────────

def run_fcfs(processes: list[dict]) -> dict:
    """
    Runs FCFS scheduling on the process list.
    Processes are sorted by arrival time first.
    """
    sorted_procs = sorted(processes, key=lambda p: p["arrival_time"])

    schedule = []
    gantt    = []
    current_time = 0

    for proc in sorted_procs:
        arrival = proc["arrival_time"]
        burst   = proc["burst_time"]

        # CPU idles if the next process hasn't arrived yet
        if current_time < arrival:
            gantt.append({"pid": "IDLE", "start": current_time, "end": arrival})
            current_time = arrival

        start_time      = current_time
        finish_time     = current_time + burst
        waiting_time    = start_time - arrival
        turnaround_time = finish_time - arrival

        schedule.append({
            "pid":              proc["pid"],
            "arrival_time":     arrival,
            "burst_time":       burst,
            "start_time":       start_time,
            "finish_time":      finish_time,
            "waiting_time":     waiting_time,
            "turnaround_time":  turnaround_time,
        })

        gantt.append({"pid": proc["pid"], "start": start_time, "end": finish_time})
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
#  DISPLAY
# ─────────────────────────────────────────────

def display_processes(processes: list[dict]):
    """Shows the randomly generated processes before running FCFS."""
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
        width  = max((seg["end"] - seg["start"]) * 2, len(seg["pid"]) + 2)
        label  = seg["pid"].center(width)
        bar   += f" {label} |"
        times += f"{str(seg['end']).rjust(width + 3)}"

    print(bar)
    print(times)


def display_results(results: dict):
    """Prints the FCFS schedule and computed times."""
    schedule = results["schedule"]

    print("\n" + "=" * 70)
    print("   FCFS RESULTS")
    print("=" * 70)
    print(f"  {'PID':<8} {'Arrival':>9} {'Burst':>7} {'Start':>7} {'Finish':>8} {'Waiting':>9} {'Turnaround':>12}")
    print("  " + "-" * 64)

    for p in schedule:
        print(
            f"  {p['pid']:<8}"
            f"  {p['arrival_time']:>7}s"
            f"  {p['burst_time']:>5}s"
            f"  {p['start_time']:>5}s"
            f"  {p['finish_time']:>6}s"
            f"  {p['waiting_time']:>7}s"
            f"  {p['turnaround_time']:>10}s"
        )

    print("  " + "-" * 64)
    print(f"\n  Average Waiting Time    :  {results['avg_waiting_time']}s")
    print(f"  Average Turnaround Time :  {results['avg_turnaround_time']}s")
    print("=" * 70)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   FCFS CPU SCHEDULING")
    print("=" * 50)

    # Ask only for the number of processes
    while True:
        try:
            n = int(input("\n  How many processes? "))
            if n <= 0:
                print("  ⚠  Please enter a number greater than 0.")
            elif n > 20:
                print("  ⚠  Maximum is 20 processes (arrival range is 0–20).")
            else:
                break
        except ValueError:
            print("  ⚠  Please enter a whole number.")

    # Generate, run, display
    processes = generate_processes(n)
    display_processes(processes)

    results = run_fcfs(processes)
    display_gantt(results["gantt"])
    display_results(results)