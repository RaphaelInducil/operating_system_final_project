 # 6/21/26
 # MFT - Memory Management with Fixed Partitions

import random


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

ALGORITHMS = ["First Fit", "Best Fit", "Worst Fit"]


# ─────────────────────────────────────────────
#  RANDOM PROCESS STREAM GENERATOR
# ─────────────────────────────────────────────

def generate_process_sizes(length: int) -> list[int]:
    """
    Generates a random sequence of process sizes.

    Controlled ranges:
      - size : 50 to 500 KB
    """

    return [random.randint(50, 500) for _ in range(length)]


def generate_fixed_partitions(count: int) -> list[int]:
    """
    Generates a random set of fixed memory partitions.
    """
    
    return [random.randint(100, 600) for _ in range(count)]


# ─────────────────────────────────────────────
#  FIRST FIT ALLOCATION
# ─────────────────────────────────────────────

def run_first_fit(processes: list[int], partitions: list[int]) -> dict:
    """
    First Fit Allocation.

    Allocates the first available partition that is
    large enough to hold the process.
    """

    memory = [{"size": p, "process": None, "frag": 0} for p in partitions]
    history = []

    allocated_count = 0
    unallocated_count = 0
    total_frag = 0

    for i, process in enumerate(processes):
        process_id = f"P{i+1}"
        status = "UNALLOCATED"
        
        for block in memory:
            if block["process"] is None and block["size"] >= process:
                block["process"] = process_id
                block["frag"] = block["size"] - process
                
                allocated_count += 1
                total_frag += block["frag"]
                status = "ALLOCATED"
                break
                
        if status == "UNALLOCATED":
            unallocated_count += 1

        history.append({
            "process":    f"{process_id} ({process}k)",
            "memory":     [{'p': b['process'], 'f': b['frag']} for b in memory],
            "status":     status,
        })

    total = allocated_count + unallocated_count

    return {
        "history":      history,
        "allocated":    allocated_count,
        "unallocated":  unallocated_count,
        "total_frag":   total_frag,
        "alloc_rate":   round((allocated_count / total) * 100, 2),
    }


# ─────────────────────────────────────────────
#  BEST FIT ALLOCATION
# ─────────────────────────────────────────────

def run_best_fit(processes: list[int], partitions: list[int]) -> dict:
    """
    Best Fit Allocation.

    Allocates the smallest available partition that
    is large enough to hold the process.
    """

    memory = [{"size": p, "process": None, "frag": 0} for p in partitions]
    history = []

    allocated_count = 0
    unallocated_count = 0
    total_frag = 0

    for i, process in enumerate(processes):
        process_id = f"P{i+1}"
        status = "UNALLOCATED"
        
        # Find all valid candidates
        candidates = [b for b in memory if b["process"] is None and b["size"] >= process]
        
        if candidates:
            # Sort by smallest remaining fragmentation
            best_block = min(candidates, key=lambda b: b["size"] - process)
            
            best_block["process"] = process_id
            best_block["frag"] = best_block["size"] - process
            
            allocated_count += 1
            total_frag += best_block["frag"]
            status = "ALLOCATED"
            
        else:
            unallocated_count += 1

        history.append({
            "process":    f"{process_id} ({process}k)",
            "memory":     [{'p': b['process'], 'f': b['frag']} for b in memory],
            "status":     status,
        })

    total = allocated_count + unallocated_count

    return {
        "history":      history,
        "allocated":    allocated_count,
        "unallocated":  unallocated_count,
        "total_frag":   total_frag,
        "alloc_rate":   round((allocated_count / total) * 100, 2),
    }


# ─────────────────────────────────────────────
#  WORST FIT ALLOCATION
# ─────────────────────────────────────────────

def run_worst_fit(processes: list[int], partitions: list[int]) -> dict:
    """
    Worst Fit Allocation.

    Allocates the largest available partition that
    is large enough to hold the process.
    """

    memory = [{"size": p, "process": None, "frag": 0} for p in partitions]
    history = []

    allocated_count = 0
    unallocated_count = 0
    total_frag = 0

    for i, process in enumerate(processes):
        process_id = f"P{i+1}"
        status = "UNALLOCATED"
        
        # Find all valid candidates
        candidates = [b for b in memory if b["process"] is None and b["size"] >= process]
        
        if candidates:
            # Sort by largest remaining fragmentation
            worst_block = max(candidates, key=lambda b: b["size"] - process)
            
            worst_block["process"] = process_id
            worst_block["frag"] = worst_block["size"] - process
            
            allocated_count += 1
            total_frag += worst_block["frag"]
            status = "ALLOCATED"
            
        else:
            unallocated_count += 1

        history.append({
            "process":    f"{process_id} ({process}k)",
            "memory":     [{'p': b['process'], 'f': b['frag']} for b in memory],
            "status":     status,
        })

    total = allocated_count + unallocated_count

    return {
        "history":      history,
        "allocated":    allocated_count,
        "unallocated":  unallocated_count,
        "total_frag":   total_frag,
        "alloc_rate":   round((allocated_count / total) * 100, 2),
    }


# ─────────────────────────────────────────────
#  DISPLAY
# ─────────────────────────────────────────────

def display_inputs(processes: list[int], partitions: list[int]):
    """Displays the generated inputs."""

    print("\n  Memory Partitions:")
    print("  " + " | ".join(f"[{p}k]" for p in partitions))
    
    print("\n  Process Stream (Sizes):")
    print("  " + " ".join(map(str, processes)))


def display_memory_table(results: dict):
    """Displays memory changes."""

    history = results["history"]

    print("\n  Memory Table [Partition State: {'p': Process, 'f': Int. Frag}]:")
    print(f"  {'Process':<15} {'Memory State':<50} {'Status':>15}")
    print("  " + "-" * 82)

    for step in history:
        
        # Formatting the dictionary array into a readable string
        memory_display = str(step["memory"]).replace("'", "")
        
        # Truncate if it's too long for the column
        if len(memory_display) > 48:
            memory_display = memory_display[:45] + "..."

        print(
            f"  {step['process']:<15}"
            f" {memory_display:<50}"
            f" {step['status']:>15}"
        )


def display_results(results: dict, algorithm: str):
    """Displays allocation statistics."""

    print("\n" + "=" * 65)
    print(f"   {algorithm.upper()} ALLOCATION RESULTS (MFT)")
    print("=" * 65)

    print(f"\n  Total Allocated    :  {results['allocated']}")
    print(f"  Total Unallocated  :  {results['unallocated']}")

    print(f"\n  Allocation Rate    :  {results['alloc_rate']}%")
    print(f"  Total Int. Frag    :  {results['total_frag']} KB")

    print("=" * 65)


# ─────────────────────────────────────────────
#  USER INPUT
# ─────────────────────────────────────────────

def ask_process_count() -> int:

    while True:
        try:
            length = int(input("\n  Number of processes to generate: "))

            if length <= 0:
                print("  ⚠  Please enter a number greater than 0.")
            elif length > 50:
                print("  ⚠  Maximum length is 50.")
            else:
                return length

        except ValueError:
            print("  ⚠  Please enter a whole number.")


def ask_partition_count() -> int:

    while True:
        try:
            count = int(input("  Number of fixed memory partitions: "))

            if count <= 0:
                print("  ⚠  Please enter a number greater than 0.")
            elif count > 10:
                print("  ⚠  Maximum partition count is 10.")
            else:
                return count

        except ValueError:
            print("  ⚠  Please enter a whole number.")


def ask_algorithm() -> str:

    print("\n  Available Algorithms:")

    for i, algorithm in enumerate(ALGORITHMS, 1):
        print(f"    {i}. {algorithm}")

    while True:
        try:
            choice = int(input(f"\n  Select algorithm (1–{len(ALGORITHMS)}): "))

            if 1 <= choice <= len(ALGORITHMS):
                return ALGORITHMS[choice - 1]

            print(f"  ⚠  Please enter a number between 1 and {len(ALGORITHMS)}.")

        except ValueError:
            print("  ⚠  Please enter a whole number.")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\n" + "=" * 50)
    print("   MFT MEMORY MANAGEMENT (Fixed Partitions)")
    print("=" * 50)

    process_count = ask_process_count()
    partition_count = ask_partition_count()
    algorithm = ask_algorithm()

    processes = generate_process_sizes(process_count)
    partitions = generate_fixed_partitions(partition_count)

    display_inputs(processes, partitions)

    print(f"\n  Algorithm Used: {algorithm}")

    if algorithm == "First Fit":
        results = run_first_fit(processes, partitions)

    elif algorithm == "Best Fit":
        results = run_best_fit(processes, partitions)

    elif algorithm == "Worst Fit":
        results = run_worst_fit(processes, partitions)

    display_memory_table(results)
    display_results(results, algorithm)