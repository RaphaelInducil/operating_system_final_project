# 6/2/2026
# MVT - Memory Management with Variable Partitioning

import random


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

ALGORITHMS = ["Without Compaction", "With Compaction"]


# ─────────────────────────────────────────────
#  RANDOM EVENT GENERATOR
# ─────────────────────────────────────────────

def generate_memory_events(length: int) -> list[int]:
    """
    Generates a random sequence of memory events.
    
    Controlled ranges:
      - Positive int : Allocate size (50 to 300 KB)
      - Negative int : Deallocate Process ID
    """
    
    events = []
    active_pids = []
    next_pid = 1

    for _ in range(length):
        # 30% chance to deallocate a random active process to create holes
        if active_pids and random.random() < 0.30:
            idx = random.randrange(len(active_pids))
            pid_to_remove = active_pids.pop(idx)
            events.append(-pid_to_remove)
        else:
            events.append(random.randint(50, 300))
            active_pids.append(next_pid)
            next_pid += 1

    return events


def merge_free_blocks(memory: list[dict]):
    """Helper to merge adjacent FREE blocks."""
    i = 0
    while i < len(memory) - 1:
        if memory[i]["id"] == "FREE" and memory[i+1]["id"] == "FREE":
            memory[i]["size"] += memory[i+1]["size"]
            memory.pop(i + 1)
        else:
            i += 1


# ─────────────────────────────────────────────
#  MVT WITHOUT COMPACTION
# ─────────────────────────────────────────────

def run_without_compaction(events: list[int], total_memory: int) -> dict:
    """
    MVT Without Compaction.

    Allocates dynamic blocks. If a process cannot fit
    in any single free hole, it is rejected (External Frag).
    """

    memory = [{"id": "FREE", "size": total_memory}]
    history = []

    allocated_count = 0
    rejected_count = 0
    next_pid = 1

    for event in events:
        
        if event > 0:
            # Allocation Request
            process_id = f"P{next_pid}"
            size_req = event
            next_pid += 1
            status = "REJECTED"
            
            # First Fit Strategy for MVT
            for i, block in enumerate(memory):
                if block["id"] == "FREE" and block["size"] >= size_req:
                    
                    remaining = block["size"] - size_req
                    memory[i] = {"id": process_id, "size": size_req}
                    
                    if remaining > 0:
                        memory.insert(i + 1, {"id": "FREE", "size": remaining})
                        
                    allocated_count += 1
                    status = "ALLOCATED"
                    break
            
            if status == "REJECTED":
                rejected_count += 1
                
            action_desc = f"Alloc {process_id} ({size_req}k)"
            
        else:
            # Deallocation Request
            process_id = f"P{-event}"
            
            for block in memory:
                if block["id"] == process_id:
                    block["id"] = "FREE"
                    break
            
            merge_free_blocks(memory)
            status = "FREED"
            action_desc = f"Free {process_id}"

        history.append({
            "action":     action_desc,
            "memory":     memory.copy(),
            "status":     status,
        })

    # Calculate final External Fragmentation (Sum of free blocks)
    ext_frag = sum(b["size"] for b in memory if b["id"] == "FREE")

    total_alloc_attempts = allocated_count + rejected_count
    alloc_rate = round((allocated_count / total_alloc_attempts) * 100, 2) if total_alloc_attempts > 0 else 0

    return {
        "history":      history,
        "allocated":    allocated_count,
        "rejected":     rejected_count,
        "ext_frag":     ext_frag,
        "alloc_rate":   alloc_rate,
    }


# ─────────────────────────────────────────────
#  MVT WITH COMPACTION
# ─────────────────────────────────────────────

def run_with_compaction(events: list[int], total_memory: int) -> dict:
    """
    MVT With Compaction.

    If a process cannot fit in any single free hole, 
    but the total free space is sufficient, memory is compacted.
    """

    memory = [{"id": "FREE", "size": total_memory}]
    history = []

    allocated_count = 0
    rejected_count = 0
    next_pid = 1

    for event in events:
        
        if event > 0:
            # Allocation Request
            process_id = f"P{next_pid}"
            size_req = event
            next_pid += 1
            status = "REJECTED"
            
            # 1. Try standard allocation first
            allocated = False
            for i, block in enumerate(memory):
                if block["id"] == "FREE" and block["size"] >= size_req:
                    remaining = block["size"] - size_req
                    memory[i] = {"id": process_id, "size": size_req}
                    if remaining > 0:
                        memory.insert(i + 1, {"id": "FREE", "size": remaining})
                    allocated = True
                    break
            
            # 2. If it fails, check if compaction is possible
            if not allocated:
                total_free = sum(b["size"] for b in memory if b["id"] == "FREE")
                
                if total_free >= size_req:
                    # Compact memory
                    memory = [b for b in memory if b["id"] != "FREE"]
                    memory.append({"id": "FREE", "size": total_free})
                    status = "COMPACTED & ALLOC"
                    
                    # Allocate in the newly merged hole
                    memory[-1] = {"id": process_id, "size": size_req}
                    if total_free - size_req > 0:
                        memory.append({"id": "FREE", "size": total_free - size_req})
                        
                    allocated_count += 1
                else:
                    rejected_count += 1
                    status = "REJECTED (OOM)"
            else:
                status = "ALLOCATED"
                allocated_count += 1
                
            action_desc = f"Alloc {process_id} ({size_req}k)"
            
        else:
            # Deallocation Request
            process_id = f"P{-event}"
            
            for block in memory:
                if block["id"] == process_id:
                    block["id"] = "FREE"
                    break
            
            merge_free_blocks(memory)
            status = "FREED"
            action_desc = f"Free {process_id}"

        history.append({
            "action":     action_desc,
            "memory":     memory.copy(),
            "status":     status,
        })

    ext_frag = sum(b["size"] for b in memory if b["id"] == "FREE")
    total_alloc_attempts = allocated_count + rejected_count
    alloc_rate = round((allocated_count / total_alloc_attempts) * 100, 2) if total_alloc_attempts > 0 else 0

    return {
        "history":      history,
        "allocated":    allocated_count,
        "rejected":     rejected_count,
        "ext_frag":     ext_frag,
        "alloc_rate":   alloc_rate,
    }


# ─────────────────────────────────────────────
#  DISPLAY
# ─────────────────────────────────────────────

def display_events(events: list[int]):
    """Displays the generated event sequence."""
    
    print("\n  Event Sequence (Positive=Allocate Size, Negative=Deallocate PID):")
    print("  " + " ".join(map(str, events)))


def display_memory_map(results: dict):
    """Displays memory changes step-by-step."""

    history = results["history"]

    print("\n  Memory State Table:")
    print(f"  {'Action':<18} {'Memory Layout':<45} {'Status':>20}")
    print("  " + "-" * 85)

    for step in history:
        
        # Format layout visually: [P1: 100|FREE: 50]
        layout = "|".join([f"{b['id']}:{b['size']}" for b in step["memory"]])
        layout = f"[{layout}]"
        
        if len(layout) > 42:
            layout = layout[:39] + "...]"

        print(
            f"  {step['action']:<18}"
            f" {layout:<45}"
            f" {step['status']:>20}"
        )


def display_results(results: dict, algorithm: str):
    """Displays allocation statistics."""

    print("\n" + "=" * 65)
    print(f"   {algorithm.upper()} ALLOCATION RESULTS (MVT)")
    print("=" * 65)

    print(f"\n  Successful Allocs  :  {results['allocated']}")
    print(f"  Rejected Allocs    :  {results['rejected']}")

    print(f"\n  Allocation Rate    :  {results['alloc_rate']}%")
    print(f"  Final Ext. Frag    :  {results['ext_frag']} KB")

    print("=" * 65)


# ─────────────────────────────────────────────
#  USER INPUT
# ─────────────────────────────────────────────

def ask_event_length() -> int:

    while True:
        try:
            length = int(input("\n  Number of memory events to simulate: "))

            if length <= 0:
                print("  ⚠  Please enter a number greater than 0.")
            elif length > 50:
                print("  ⚠  Maximum length is 50.")
            else:
                return length

        except ValueError:
            print("  ⚠  Please enter a whole number.")


def ask_total_memory() -> int:

    while True:
        try:
            mem = int(input("  Total Memory Size (KB): "))

            if mem < 500:
                print("  ⚠  Please enter a size of at least 500 KB.")
            else:
                return mem

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
    print("   MVT MEMORY MANAGEMENT (Dynamic Partitions)")
    print("=" * 50)

    event_length = ask_event_length()
    total_memory = ask_total_memory()
    algorithm = ask_algorithm()

    events = generate_memory_events(event_length)

    display_events(events)

    print(f"\n  Algorithm Used: {algorithm}")

    if algorithm == "Without Compaction":
        results = run_without_compaction(events, total_memory)

    elif algorithm == "With Compaction":
        results = run_with_compaction(events, total_memory)

    display_memory_map(results)
    display_results(results, algorithm)