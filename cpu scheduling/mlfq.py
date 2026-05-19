# 05/18/26
# multilevel queue scheduling with user input queue algorithms and random process generation

import random
from collections import deque


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
            "pid":              f"P{i + 1}",
            "arrival_time":     arrival_times[i],
            "burst_time":       random.randint(1, 10),
            "priority":         random.randint(1, 5),
            "remaining_time":   0,   # filled at runtime
            "queue_path":       [],  # tracks which queues it passed through
        })
    return processes


# ─────────────────────────────────────────────
#  QUEUE SELECTOR — picks next process per algorithm
# ─────────────────────────────────────────────

def pick_next(queue: list, algorithm: str) -> dict:
    """
    Selects the next process from the queue based on the queue's algorithm.
    Does NOT remove it — caller handles removal.
    """
    if algorithm == "FCFS":
        return min(queue, key=lambda p: p["arrival_time"])

    elif algorithm == "SJF":
        return min(queue, key=lambda p: (p["remaining_time"], p["arrival_time"]))

    elif algorithm == "Priority":
        return min(queue, key=lambda p: (p["priority"], p["arrival_time"]))

    elif algorithm == "Round Robin":
        return queue[0]   # RR is FIFO within the queue

    return queue[0]


# ─────────────────────────────────────────────
#  MFQ ALGORITHM
# ─────────────────────────────────────────────

def run_mfq(processes: list[dict], queue_configs: list[dict]) -> dict:
    """
    Runs Multilevel Feedback Queue scheduling.

    queue_configs is a list of 3 dicts:
      { "algorithm": "Round Robin", "quantum": 2 }
      { "algorithm": "FCFS",        "quantum": None }
      ...

    Process flow:
      - All processes start in Q1 when they arrive
      - Each queue gives the process a time slice based on its algorithm
        - RR:       slice = quantum
        - FCFS/SJF/Priority: slice = full remaining burst (runs to completion within the queue)
      - If the process finishes → done
      - If not finished and queue < Q3 → demoted to next queue
      - If not finished and already in Q3 → stays in Q3 until done
    """

    # Work with copies, initialize remaining_time
    procs = []
    for p in processes:
        cp = p.copy()
        cp["remaining_time"] = p["burst_time"]
        cp["queue_path"]     = []
        procs.append(cp)

    # Sort by arrival time
    procs.sort(key=lambda p: p["arrival_time"])

    # Three queues (lists, not deques — easier to reorder by algorithm)
    queues      = [[], [], []]
    completed   = {}
    gantt       = []
    current_time = 0
    arrival_idx  = 0   # pointer into sorted procs

    def enqueue_arrivals(up_to_time):
        nonlocal arrival_idx
        while arrival_idx < len(procs) and procs[arrival_idx]["arrival_time"] <= up_to_time:
            p = procs[arrival_idx]
            p["queue_path"].append("Q1")
            queues[0].append(p)
            arrival_idx += 1

    # Seed initial arrivals
    enqueue_arrivals(current_time)

    while len(completed) < len(procs):

        # Find the highest-priority non-empty queue
        active_q = None
        for i in range(3):
            if queues[i]:
                active_q = i
                break

        if active_q is None:
            # All queues empty — idle until next arrival
            if arrival_idx < len(procs):
                next_arr = procs[arrival_idx]["arrival_time"]
                gantt.append({"pid": "IDLE", "queue": "IDLE", "start": current_time, "end": next_arr})
                current_time = next_arr
                enqueue_arrivals(current_time)
            continue

        config    = queue_configs[active_q]
        algorithm = config["algorithm"]
        quantum   = config.get("quantum")

        # Pick next process using this queue's algorithm
        proc = pick_next(queues[active_q], algorithm)
        queues[active_q].remove(proc)

        # Determine slice length
        if algorithm == "Round Robin":
            slice_time = min(quantum, proc["remaining_time"])
        else:
            # FCFS / SJF / Priority: runs to completion in this queue
            slice_time = proc["remaining_time"]

        start        = current_time
        end          = current_time + slice_time
        gantt.append({"pid": proc["pid"], "queue": f"Q{active_q + 1}", "start": start, "end": end})

        proc["remaining_time"] -= slice_time
        current_time = end

        # Let newly arrived processes in during this slice
        enqueue_arrivals(current_time)

        if proc["remaining_time"] == 0:
            # Finished
            finish_time     = current_time
            waiting_time    = finish_time - proc["arrival_time"] - proc["burst_time"]
            turnaround_time = finish_time - proc["arrival_time"]
            completed[proc["pid"]] = {
                "pid":              proc["pid"],
                "arrival_time":     proc["arrival_time"],
                "burst_time":       proc["burst_time"],
                "priority":         proc["priority"],
                "finish_time":      finish_time,
                "waiting_time":     waiting_time,
                "turnaround_time":  turnaround_time,
                "queue_path":       " → ".join(proc["queue_path"]),
            }
        else:
            # Not finished — demote or stay in Q3
            next_q = min(active_q + 1, 2)
            q_label = f"Q{next_q + 1}"
            if q_label not in proc["queue_path"]:
                proc["queue_path"].append(q_label)
            queues[next_q].append(proc)

    # Sort by PID for display
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

ALGORITHMS = ["FCFS", "SJF", "Priority", "Round Robin"]


def display_processes(processes: list[dict]):
    print("\n  Generated Processes:")
    print(f"  {'PID':<8} {'Arrival':>9} {'Burst':>7} {'Priority':>10}")
    print("  " + "-" * 38)
    for p in processes:
        print(f"  {p['pid']:<8} {p['arrival_time']:>7}s {p['burst_time']:>6}s {p['priority']:>9}")


def display_queue_config(queue_configs: list[dict]):
    print("\n  Queue Configuration:")
    print("  " + "-" * 40)
    for i, cfg in enumerate(queue_configs):
        algo = cfg["algorithm"]
        extra = f"  (quantum = {cfg['quantum']}s)" if algo == "Round Robin" else ""
        priority_note = "← highest priority" if i == 0 else ("← lowest priority" if i == 2 else "")
        print(f"  Q{i + 1}  {algo}{extra}  {priority_note}")
    print("  " + "-" * 40)


def display_gantt(gantt: list[dict]):
    print("\n  Gantt Chart:")
    bar   = "  |"
    times = f"  {gantt[0]['start']}"

    for seg in gantt:
        label = seg["pid"] if seg["pid"] == "IDLE" else f"{seg['pid']}({seg['queue']})"
        width = max((seg["end"] - seg["start"]) * 2, len(label) + 2)
        bar   += f" {label.center(width)} |"
        times += f"{str(seg['end']).rjust(width + 3)}"

    print(bar)
    print(times)


def display_results(results: dict):
    schedule = results["schedule"]

    print("\n" + "=" * 82)
    print("   MULTILEVEL FEEDBACK QUEUE RESULTS")
    print("=" * 82)
    print(f"  {'PID':<8} {'Arrival':>9} {'Burst':>7} {'Priority':>10} {'Finish':>8} {'Waiting':>9} {'Turnaround':>12}  {'Path'}")
    print("  " + "-" * 78)

    for p in schedule:
        print(
            f"  {p['pid']:<8}"
            f"  {p['arrival_time']:>7}s"
            f"  {p['burst_time']:>5}s"
            f"  {p['priority']:>9}"
            f"  {p['finish_time']:>6}s"
            f"  {p['waiting_time']:>7}s"
            f"  {p['turnaround_time']:>10}s"
            f"  {p['queue_path']}"
        )

    print("  " + "-" * 78)
    print(f"\n  Average Waiting Time    :  {results['avg_waiting_time']}s")
    print(f"  Average Turnaround Time :  {results['avg_turnaround_time']}s")
    print("=" * 82)


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
    """
    Asks the user to pick an algorithm for each of the 3 queues.
    If Round Robin is chosen, also asks for the quantum.
    """
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
    print("   MULTILEVEL FEEDBACK QUEUE SCHEDULING")
    print("=" * 50)

    n            = ask_number_of_processes()
    queue_configs = ask_queue_config()
    processes    = generate_processes(n)

    display_processes(processes)
    display_queue_config(queue_configs)

    results = run_mfq(processes, queue_configs)
    display_gantt(results["gantt"])
    display_results(results)