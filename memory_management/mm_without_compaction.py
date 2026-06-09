# 6/2/2026
# Memory Management without compaction

import random


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

ALGORITHMS = ["First-Fit", "Best-Fit", "Worst-Fit"]

MEMORY_SIZE = 1024  # Total memory in KB (arbitrary units)

MIN_PROCESS_SIZE = 64
MAX_PROCESS_SIZE = 256

NUM_PROCESSES = 20


# ─────────────────────────────────────────────
#  PROCESS GENERATOR
# ─────────────────────────────────────────────

def generate_processes(num_processes: int) -> list[dict]:
    """
    Generates a list of random processes.
    
    Each process has:
      - pid: unique identifier
      - size: memory requirement in KB
      - duration: time units (1-10)
    """

    processes = []

    for i in range(num_processes):
        processes.append({
            "pid":      f"P{i + 1}",
            "size":     random.randint(MIN_PROCESS_SIZE, MAX_PROCESS_SIZE),
            "duration": random.randint(1, 10),
        })

    return processes


# ─────────────────────────────────────────────
#  INITIALIZE MEMORY
# ─────────────────────────────────────────────

def initialize_memory() -> list[dict]:
    """
    Initializes memory as a single free block.
    """

    return [{
        "type":  "FREE",
        "pid":   None,
        "size":  MEMORY_SIZE,
    }]


# ─────────────────────────────────────────────
#  MEMORY ALLOCATION ALGORITHMS
# ─────────────────────────────────────────────

def allocate_first_fit(process: dict, memory: list[dict]) -> bool:
    """
    First-Fit: Allocates the first block that is large enough.
    """

    for block in memory:
        if block["type"] == "FREE" and block["size"] >= process["size"]:
            allocate_block(process, memory, memory.index(block))
            return True

    return False


def allocate_best_fit(process: dict, memory: list[dict]) -> bool:
    """
    Best-Fit: Allocates the smallest block that is large enough.
    """

    best_index = -1
    best_size = float("inf")

    for i, block in enumerate(memory):
        if block["type"] == "FREE" and block["size"] >= process["size"]:
            if block["size"] < best_size:
                best_size = block["size"]
                best_index = i

    if best_index != -1:
        allocate_block(process, memory, best_index)
        return True

    return False


def allocate_worst_fit(process: dict, memory: list[dict]) -> bool:
    """
    Worst-Fit: Allocates the largest available block.
    """

    worst_index = -1
    worst_size = -1

    for i, block in enumerate(memory):
        if block["type"] == "FREE" and block["size"] >= process["size"]:
            if block["size"] > worst_size:
                worst_size = block["size"]
                worst_index = i

    if worst_index != -1:
        allocate_block(process, memory, worst_index)
        return True

    return False


def allocate_block(process: dict, memory: list[dict], index: int):
    """
    Helper: Splits a free block and allocates to a process.
    """

    free_size = memory[index]["size"]
    process_size = process["size"]

    if free_size == process_size:
        memory[index]["type"] = "ALLOCATED"
        memory[index]["pid"] = process["pid"]

    else:
        # Split: Allocate process, keep remainder as free
        memory[index]["type"] = "ALLOCATED"
        memory[index]["pid"] = process["pid"]
        memory[index]["size"] = process_size

        # Insert new free block after the allocated block
        memory.insert(index + 1, {
            "type":  "FREE",
            "pid":   None,
            "size":  free_size - process_size,
        })


def deallocate_block(memory: list[dict], pid: str):
    """
    Deallocates a process block.
    
    NOTE: Without compaction, we simply mark the block as FREE.
    We do NOT merge adjacent free blocks.
    """

    for block in memory:
        if block["type"] == "ALLOCATED" and block["pid"] == pid:
            block["type"] = "FREE"
            block["pid"] = None
            return True

    return False


# ─────────────────────────────────────────────
#  MAIN SIMULATION LOOP
# ─────────────────────────────────────────────

def run_simulation(processes: list[dict], algorithm: str) -> dict:
    """
    Runs the memory management simulation.
    """

    memory = initialize_memory()

    history = []
    allocated_pids = set()

    allocated_count = 0
    rejected_count = 0

    for step, process in enumerate(processes):
        pid = process["pid"]
        size = process["size"]

        # Try to allocate
        if pid in allocated_pids:
            # Process already in memory, skip allocation
            pass

        elif algorithm == "First-Fit":
            success = allocate_first_fit(process, memory)

        elif algorithm == "Best-Fit":
            success = allocate_best_fit(process, memory)

        else:  # Worst-Fit
            success = allocate_worst_fit(process, memory)

        if success:
            allocated_pids.add(pid)
            allocated_count += 1
            status = "ALLOCATED"
        else:
            rejected_count += 1
            status = "REJECTED"

        # Simulate time passing: reduce duration for allocated processes
        for block in memory:
            if block["type"] == "ALLOCATED" and block["pid"]:
                # Find corresponding process
                for p in processes:
                    if p["pid"] == block["pid"]:
                        p["duration"] -= 1
                        # Process finished?
                        if p["duration"] <= 0:
                            deallocate_block(memory, block["pid"])
                            allocated_pids.discard(block["pid"])
                        break

        # Record history
        history.append({
            "step":      step + 1,
            "pid":       pid,
            "size":      size,
            "status":    status,
            "memory":    count_memory_usage(memory),
        })

    total = len(processes)

    return {
        "history":          history,
        "allocated":        allocated_count,
        "rejected":         rejected_count,
        "allocation_rate": round((allocated_count / total) * 100, 2),
    }


def count_memory_usage(memory: list[dict]) -> dict:
    """
    Counts allocated vs free memory.
    """

    allocated = sum(b["size"] for b in memory if b["type"] == "ALLOCATED")
    free = sum(b["size"] for b in memory if b["type"] == "FREE")

    return {
        "allocated": allocated,
        "free":      free,
        "total":     allocated + free,
    }


# ─────────────────────────────────────────────
#  DISPLAY FUNCTIONS
# ─────────────────────────────────────────────

def display_processes(processes: list[dict]):
    """Displays generated processes."""

    print("\n  Process List:")
    print(f"  {'PID':<6} {'Size (KB)':<12} {'Duration':<10}")
    print("  " + "-" * 32)

    for p in processes:
        print(f"  {p['pid']:<6} {p['size']:<12} {p['duration']:<10}")


def display_memory_state(memory: list[dict]):
    """Visualizes memory blocks."""

    print("\n  Memory State:")
    print(f"  {'Block':<10} {'PID':<8} {'Size (KB)':<12}")
    print("  " + "-" * 35)

    allocated_size = 0
    free_size = 0

    for i, block in enumerate(memory):
        block_type = f"B#{i + 1}"
        pid = block["pid"] if block["pid"] else "-"
        size = block["size"]

        print(f"  {block_type:<10} {pid:<8} {size:<12}")

        if block["type"] == "ALLOCATED":
            allocated_size += size
        else:
            free_size += size

    print("  " + "-" * 35)
    print(f"  Allocated: {allocated_size} KB | Free: {free_size} KB | Total: {MEMORY_SIZE} KB")


def display_results(results: dict, algorithm: str):
    """Displays simulation results."""

    print("\n" + "=" * 60)
    print(f"   {algorithm} SIMULATION RESULTS")
    print("=" * 60)

    print(f"\n  Allocated Processes :  {results['allocated']}")
    print(f"  Rejected Processes:  {results['rejected']}")

    print(f"\n  Allocation Rate   :  {results['allocation_rate']}%")

    print("=" * 60)


def display_history(results: dict):
    """Displays step-by-step history."""

    print("\n  Simulation History:")
    print(f"  {'Step':<6} {'PID':<6} {'Size':<8} {'Status':<12} {'Memory':<20}")
    print("  " + "-" * 60)

    for step in results["history"]:
        mem = f"A:{step['memory']['allocated']} F:{step['memory']['free']}"

        print(
            f"  {step['step']:<6}"
            f"  {step['pid']:<6}"
            f"  {step['size']:<8}"
            f"  {step['status']:<12}"
            f"  {mem:<20}"
        )


# ─────────────────────────────────────────────
#  USER INPUT
# ─────────────────────────────────────────────

def ask_algorithm() -> str:

    print("\n  Available Algorithms:")

    for i, algorithm in enumerate(ALGORITHMS, 1):
        print(f"    {i}. {algorithm}")

    while True:
        try:
            choice = int(input("\n  Select algorithm (1–3): "))

            if 1 <= choice <= 3:
                return ALGORITHMS[choice - 1]

            print("  ⚠  Please enter a number between 1 and 3.")

        except ValueError:
            print("  ⚠  Please enter a whole number.")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\n" + "=" * 50)
    print("   MEMORY MANAGEMENT (WITHOUT COMPACTION)")
    print("=" * 50)

    print(f"\n  Memory Size       :  {MEMORY_SIZE} KB")
    print(f"  Total Processes   :  {NUM_PROCESSES}")
    print(f"  Process Size Range:  {MIN_PROCESS_SIZE} - {MAX_PROCESS_SIZE} KB")

    processes = generate_processes(NUM_PROCESSES)

    display_processes(processes)

    algorithm = ask_algorithm()

    results = run_simulation(processes, algorithm)

    print("\n" + "- " * 25)
    display_results(results, algorithm)
    display_history(results)


# ─────────────────────────────────────────────
#  NOTES
# ─────────────────────────────────────────────
#
#  Without Compaction:
#    - Free blocks are NOT merged together.
#    - External fragmentation increases over time.
#    - A process may be rejected even if total free
#      memory > process size (because no single block
#      is large enough).
#
#  Algorithms:
#    - First-Fit : Scans from beginning, takes first fit.
#    - Best-Fit  : Chooses smallest block that fits.
#    - Worst-Fit : Chooses largest block (leaves large remains).