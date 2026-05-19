# 05/19/26

import random


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

ALGORITHMS = ["FCFS", "SJF", "Priority", "Round Robin"]


# ─────────────────────────────────────────────
#  RANDOM PROCESS GENERATOR
# ─────────────────────────────────────────────

def generate_processes(n: int) -> list[dict]:
    """
    Generates n processes with random values.

    Controlled ranges:
      - arrival_time : 0 to 20 (unique, sorted)
      - burst_time   : 1 to 10
      - priority     : 1 to 5  (1 = highest)
      - queue        : 0, 1, or 2  (Q1, Q2, Q3) — randomly assigned
    """
    arrival_times = sorted(random.sample(range(0, 21), n))

    processes = []
    for i in range(n):
        processes.append({
            "pid":            f"P{i + 1}",
            "arrival_time":   arrival_times[i],
            "burst_time":     random.randint(1, 10),
            "priority":       random.randint(1, 5),
            "queue":          random.randint(0, 2),   # 0=Q1, 1=Q2, 2=Q3
            "remaining_time": 0,                       # filled at runtime
        })

    return processes


# ─────────────────────────────────────────────
#  PICK NEXT PROCESS (per algorithm)
# ─────────────────────────────────────────────

def pick_next(queue: list, algorithm: str) -> dict:
    """
    Selects next process from a queue based on its algorithm.
    Does NOT remove — caller handles removal.
    """
    if algorithm == "FCFS":
        return min(queue, key=lambda p: p["arrival_time"])

    elif algorithm == "SJF":
        return min(queue, key=lambda p: (p["remaining_time"], p["arrival_time"]))

    elif algorithm == "Priority":
        return min(queue, key=lambda p: (p["priority"], p["arrival_time"]))

    elif algorithm == "Round Robin":
        return queue[0]   # FIFO order within queue

    return queue[0]


# ─────────────────────────────────────────────
#  MLQ ALGORITHM
# ─────────────────────────────────────────────

def run_mlq(processes: list[dict], queue_configs: list[dict]) -> dict:
    """
    Runs Multilevel Queue scheduling.

    queue_configs: list of 3 dicts
      { "algorithm": "Round Robin", "quantum": 2 }
      { "algorithm": "FCFS",        "quantum": None }

    Rules:
      - Processes stay in their assigned queue permanently
      - Higher-priority queues (lower index) always preempt lower ones
        when a new process arrives (inter-queue preemption)
      - Within a queue, the chosen algorithm decides the order
      - Round Robin queues cycle; others run to completion within the queue
    """
    # Work with copies, initialize remaining_time
    procs = []
    for p in processes:
        cp = p.copy()
        cp["remaining_time"] = p["burst_time"]
        procs.append(cp)

    procs.sort(key=lambda p: p["arrival_time"])

    # Separate into 3 queue buckets (will hold processes as they arrive)
    queues       = [[], [], []]
    completed    = {}
    gantt        = []
    current_time = 0
    arrival_idx  = 0

    def enqueue_arrivals(up_to):
        nonlocal arrival_idx
        while arrival_idx < len(procs) and procs[arrival_idx]["arrival_time"] <= up_to:
            p = procs[arrival_idx]
            queues[p["queue"]].append(p)
            arrival_idx += 1

    enqueue_arrivals(current_time)

    while len(completed) < len(procs):

        # Find the highest-priority non-empty queue
        active_q = None
        for i in range(3):
            if queues[i]:
                active_q = i
                break

        if active_q is None:
            # CPU idle — jump to next arrival
            if arrival_idx < len(procs):
                next_arr = procs[arrival_idx]["arrival_time"]
                gantt.append({"pid": "IDLE", "queue": "IDLE", "start": current_time, "end": next_arr})
                current_time = next_arr
                enqueue_arrivals(current_time)
            continue

        config    = queue_configs[active_q]
        algorithm = config["algorithm"]
        quantum   = config.get("quantum")

        proc = pick_next(queues[active_q], algorithm)
        queues[active_q].remove(proc)

        # Determine slice
        if algorithm == "Round Robin":
            slice_time = min(quantum, proc["remaining_time"])
        else:
            slice_time = proc["remaining_time"]

        # Check if a higher-priority queue gets a process mid-slice
        # Find next arrival that could interrupt
        slice_end = current_time + slice_time
        interrupt_at = slice_end

        for future in procs[arrival_idx:]:
            if future["queue"] < active_q and future["arrival_time"] < slice_end:
                interrupt_at = future["arrival_time"]
                break

        actual_slice = interrupt_at - current_time

        start = current_time
        end   = current_time + actual_slice
        gantt.append({"pid": proc["pid"], "queue": f"Q{active_q + 1}", "start": start, "end": end})

        proc["remaining_time"] -= actual_slice
        current_time = end

        enqueue_arrivals(current_time)

        if proc["remaining_time"] <= 0:
            finish_time     = current_time
            waiting_time    = finish_time - proc["arrival_time"] - proc["burst_time"]
            turnaround_time = finish_time - proc["arrival_time"]

            completed[proc["pid"]] = {
                "pid":              proc["pid"],
                "arrival_time":     proc["arrival_time"],
                "burst_time":       proc["burst_time"],
                "priority":         proc["priority"],
                "queue":            f"Q{proc['queue'] + 1}",
                "finish_time":      finish_time,
                "waiting_time":     max(0, waiting_time),
                "turnaround_time":  turnaround_time,
            }
        else:
            # Put back in its own queue (not finished)
            queues[active_q].append(proc)

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
    print("\n  Generated Processes:")
    print(f"  {'PID':<8} {'Queue':>6} {'Arrival':>9} {'Burst':>7} {'Priority':>10}")
    print("  " + "-" * 44)
    for p in processes:
        print(
            f"  {p['pid']:<8}"
            f"  Q{p['queue'] + 1:>4}"
            f"  {p['arrival_time']:>7}s"
            f"  {p['burst_time']:>5}s"
            f"  {p['priority']:>9}"
        )


def display_queue_config(queue_configs: list[dict]):
    print("\n  Queue Configuration:")
    print("  " + "-" * 48)
    labels = ["highest priority", "", "lowest priority — runs only when Q1 & Q2 empty"]
    for i, cfg in enumerate(queue_configs):
        algo  = cfg["algorithm"]
        extra = f"  (quantum = {cfg['quantum']}s)" if algo == "Round Robin" else ""
        note  = f"  ← {labels[i]}" if labels[i] else ""
        print(f"  Q{i + 1}  {algo}{extra}{note}")
    print("  " + "-" * 48)


def display_gantt(gantt: list[dict]):
    print("\n  Gantt Chart:")
    bar   = "  |"
    times = f"  {gantt[0]['start']}"

    for seg in gantt:
        label = seg["pid"] if seg["pid"] == "IDLE" else f"{seg['pid']}({seg['queue']})"
        width = max((seg["end"] - seg["start"]) * 2, len(label) + 2)
        bar   += f" {label.center(width)} |"
        times += f"{str(round(seg['end'])).rjust(width + 3)}"

    print(bar)
    print(times)


def display_results(results: dict):
    schedule = results["schedule"]

    print("\n" + "=" * 80)
    print("   MULTILEVEL QUEUE RESULTS")
    print("=" * 80)
    print(f"  {'PID':<8} {'Queue':>6} {'Arrival':>9} {'Burst':>7} {'Priority':>10} {'Finish':>8} {'Waiting':>9} {'Turnaround':>12}")
    print("  " + "-" * 73)

    for p in schedule:
        print(
            f"  {p['pid']:<8}"
            f"  {p['queue']:>5}"
            f"  {p['arrival_time']:>7}s"
            f"  {p['burst_time']:>5}s"
            f"  {p['priority']:>9}"
            f"  {p['finish_time']:>6}s"
            f"  {p['waiting_time']:>7}s"
            f"  {p['turnaround_time']:>10}s"
        )

    print("  " + "-" * 73)
    print(f"\n  Average Waiting Time    :  {results['avg_waiting_time']}s")
    print(f"  Average Turnaround Time :  {results['avg_turnaround_time']}s")
    print("=" * 80)


# ─────────────────────────────────────────────
#  USER INPUT
# ─────────────────────────────────────────────

def ask_number_of_processes() -> int:
    while True:
        try:
            n = int(input("\n  How many processes? "))
            if n <= 0:
                print("  ⚠  Please enter a number greater than 0.")
            elif n > 20:
                print("  ⚠  Maximum is 20 processes.")
            else:
                return n
        except ValueError:
            print("  ⚠  Please enter a whole number.")


def ask_queue_config() -> list[dict]:
    configs = []

    print("\n" + "─" * 50)
    print("  Queue Setup")
    print("─" * 50)
    print("  Assign a scheduling algorithm to each queue.")
    print("  Q1 = highest priority, Q3 = lowest priority.\n")
    print("  Available algorithms:")
    for i, algo in enumerate(ALGORITHMS, 1):
        print(f"    {i}. {algo}")

    for q_num in range(1, 4):
        print(f"\n  [ Q{q_num} ]")
        while True:
            try:
                choice = int(input(f"    Choose algorithm for Q{q_num} (1–4): "))
                if 1 <= choice <= 4:
                    algorithm = ALGORITHMS[choice - 1]
                    break
                print("  ⚠  Please enter a number between 1 and 4.")
            except ValueError:
                print("  ⚠  Please enter a whole number.")

        quantum = None
        if algorithm == "Round Robin":
            while True:
                try:
                    quantum = int(input(f"    Time quantum for Q{q_num} (in seconds): "))
                    if quantum <= 0:
                        print("  ⚠  Quantum must be greater than 0.")
                    else:
                        break
                except ValueError:
                    print("  ⚠  Please enter a whole number.")

        configs.append({"algorithm": algorithm, "quantum": quantum})
        print(f"  ✔  Q{q_num} → {algorithm}" + (f" (quantum = {quantum}s)" if quantum else ""))

    return configs


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   MULTILEVEL QUEUE SCHEDULING")
    print("=" * 50)

    n             = ask_number_of_processes()
    queue_configs = ask_queue_config()
    processes     = generate_processes(n)

    display_processes(processes)
    display_queue_config(queue_configs)

    results = run_mlq(processes, queue_configs)
    display_gantt(results["gantt"])
    display_results(results)