import random

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

ALGORITHMS = ["First Come First Served", "Shortest Job First", "Round Robin"]

NUM_PROCESSES = 5
MAX_BURST_TIME = 10
MAX_ARRIVAL_TIME = 5
TIME_QUANTUM = 3

# ─────────────────────────────────────────────
#  PROCESS GENERATOR
# ─────────────────────────────────────────────

def generate_processes(num_processes: int) -> list[dict]:
    """
    Generates a list of random processes with arrival and burst times.
    """
    processes = []
    for i in range(num_processes):
        processes.append({
            "pid": f"P{i + 1}",
            "arrival": random.randint(0, MAX_ARRIVAL_TIME),
            "burst": random.randint(1, MAX_BURST_TIME),
        })
    return processes

# ─────────────────────────────────────────────
#  CPU SCHEDULING ALGORITHMS
# ─────────────────────────────────────────────

def calculate_fcfs(processes: list[dict]) -> dict:
    """
    First Come First Served Scheduling
    """
    sorted_procs = sorted(processes, key=lambda x: x["arrival"])
    current_time = 0
    sequence = []
    waiting_times = {}
    turnaround_times = {}

    for p in sorted_procs:
        if current_time < p["arrival"]:
            current_time = p["arrival"]

        start_time = current_time
        current_time += p["burst"]
        end_time = current_time

        turnaround = end_time - p["arrival"]
        waiting = start_time - p["arrival"]

        waiting_times[p["pid"]] = waiting
        turnaround_times[p["pid"]] = turnaround

        sequence.append({
            "pid": p["pid"],
            "start": start_time,
            "end": end_time
        })

    return {
        "algorithm": "First Come First Served",
        "sequence": sequence,
        "waiting_times": waiting_times,
        "turnaround_times": turnaround_times
    }

def calculate_sjf(processes: list[dict]) -> dict:
    """
    Shortest Job First Scheduling 
    """
    pending = sorted(processes, key=lambda x: x["arrival"])
    current_time = 0
    sequence = []
    waiting_times = {}
    turnaround_times = {}

    while pending:
        available = [p for p in pending if p["arrival"] <= current_time]

        if not available:
            next_arrival = min(p["arrival"] for p in pending)
            current_time = next_arrival
            available = [p for p in pending if p["arrival"] <= current_time]

        selected = min(available, key=lambda x: x["burst"])

        start_time = current_time
        current_time += selected["burst"]
        end_time = current_time

        turnaround = end_time - selected["arrival"]
        waiting = start_time - selected["arrival"]

        waiting_times[selected["pid"]] = waiting
        turnaround_times[selected["pid"]] = turnaround

        sequence.append({
            "pid": selected["pid"],
            "start": start_time,
            "end": end_time
        })

        pending.remove(selected)

    return {
        "algorithm": "Shortest Job First",
        "sequence": sequence,
        "waiting_times": waiting_times,
        "turnaround_times": turnaround_times
    }

def calculate_rr(processes: list[dict], quantum: int) -> dict:
    """
    Round Robin Scheduling
    """
    pending = sorted([p.copy() for p in processes], key=lambda x: x["arrival"])
    queue = []
    current_time = 0
    sequence = []
    waiting_times = {p["pid"]: 0 for p in processes}
    turnaround_times = {p["pid"]: 0 for p in processes}

    remaining = {p["pid"]: p["burst"] for p in processes}
    arrivals = {p["pid"]: p["arrival"] for p in processes}

    if pending:
        current_time = pending[0]["arrival"]

    while pending or queue:
        arrived_now = [p for p in pending if p["arrival"] <= current_time]
        for p in arrived_now:
            queue.append(p)
            pending.remove(p)

        if not queue:
            if pending:
                next_arrival = min(p["arrival"] for p in pending)
                current_time = next_arrival
                continue
            else:
                break

        current_process = queue.pop(0)
        pid = current_process["pid"]
        start_time = current_time

        execute_time = min(quantum, remaining[pid])
        current_time += execute_time
        remaining[pid] -= execute_time

        sequence.append({
            "pid": pid,
            "start": start_time,
            "end": current_time
        })

        arrived_during = [p for p in pending if p["arrival"] <= current_time]
        for p in arrived_during:
            queue.append(p)
            pending.remove(p)

        if remaining[pid] > 0:
            queue.append(current_process)
        else:
            turnaround = current_time - arrivals[pid]
            original_burst = next(p["burst"] for p in processes if p["pid"] == pid)
            waiting = turnaround - original_burst

            turnaround_times[pid] = turnaround
            waiting_times[pid] = waiting

    return {
        "algorithm": "Round Robin",
        "sequence": sequence,
        "waiting_times": waiting_times,
        "turnaround_times": turnaround_times
    }

# ─────────────────────────────────────────────
#  MAIN SIMULATION LOOP
# ─────────────────────────────────────────────

def run_simulation(processes: list[dict], algorithm: str, quantum: int) -> dict:
    """
    Routes the execution to the correct algorithm.
    """
    if algorithm == "First Come First Served":
        return calculate_fcfs(processes)
    elif algorithm == "Shortest Job First":
        return calculate_sjf(processes)
    else:
        return calculate_rr(processes, quantum)

# ─────────────────────────────────────────────
#  DISPLAY FUNCTIONS
# ─────────────────────────────────────────────

def display_processes(processes: list[dict]):
    """Displays generated processes."""
    print("\n  Process List:")
    print(f"  {'PID':<6} {'Arrival':<10} {'Burst':<10}")
    print("  " + "═" * 28)
    for p in processes:
        print(f"  {p['pid']:<6} {p['arrival']:<10} {p['burst']:<10}")

def display_results(results: dict, processes: list[dict]):
    """Displays simulation totals and Gantt chart metrics."""
    print("\n" + "═" * 60)
    print(f"   {results['algorithm'].upper()} SIMULATION RESULTS")
    print("═" * 60)

    print("\n  Gantt Chart Execution Sequence:")
    print(f"  {'PID':<8} {'Start Time':<12} {'End Time':<12}")
    print("  " + "─" * 34)
    for step in results["sequence"]:
        print(f"  {step['pid']:<8} {step['start']:<12} {step['end']:<12}")

    print("\n  Performance Metrics:")
    print(f"  {'PID':<6} {'Waiting Time':<15} {'Turnaround Time':<18}")
    print("  " + "─" * 41)

    total_waiting = 0
    total_turnaround = 0

    sorted_pids = sorted(results["waiting_times"].keys(), key=lambda x: int(x[1:]))

    for pid in sorted_pids:
        wt = results["waiting_times"][pid]
        tt = results["turnaround_times"][pid]
        total_waiting += wt
        total_turnaround += tt
        print(f"  {pid:<6} {wt:<15} {tt:<18}")

    avg_wt = total_waiting / len(processes)
    avg_tt = total_turnaround / len(processes)

    print("  " + "─" * 41)
    print(f"  Average Waiting Time    :  {avg_wt:.2f}")
    print(f"  Average Turnaround Time :  {avg_tt:.2f}")

# ─────────────────────────────────────────────
#  USER INPUT
# ─────────────────────────────────────────────

def ask_algorithm() -> str:
    """Handles terminal user selection."""
    print("\n  Available Algorithms:")
    for i, algorithm in enumerate(ALGORITHMS, 1):
        print(f"    {i}. {algorithm}")

    while True:
        try:
            choice = int(input("\n  Select algorithm (1 to 3): "))
            if 1 <= choice <= 3:
                return ALGORITHMS[choice - 1]
            print("  Please enter a number between 1 and 3.")
        except ValueError:
            print("  Please enter a whole number.")

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\n" + "═" * 50)
    print("   CPU SCHEDULING")
    print("═" * 50)

    processes = generate_processes(NUM_PROCESSES)
    
    display_processes(processes)

    algorithm = ask_algorithm()

    results = run_simulation(processes, algorithm, TIME_QUANTUM)

    display_results(results, processes)