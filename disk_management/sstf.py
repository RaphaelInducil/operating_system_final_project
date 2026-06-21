# 6/9/2026
# Disk Management Simulation: Shortest Seek Time First (SSTF) Algorithm

import random

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

ALGORITHM_NAME = "Shortest Seek Time First (SSTF)"
MAX_CYLINDER = 199
MIN_CYLINDER = 0
NUM_REQUESTS = 8

# ─────────────────────────────────────────────
#  REQUEST GENERATOR
# ─────────────────────────────────────────────

def generate_requests(num_requests: int) -> list[int]:
    """Generates a list of random track requests."""
    return [random.randint(MIN_CYLINDER, MAX_CYLINDER) for _ in range(num_requests)]

# ─────────────────────────────────────────────
#  DISK SCHEDULING ALGORITHM
# ─────────────────────────────────────────────

def calculate_sstf(initial_head: int, requests: list[int]) -> dict:
    """Selects the request closest to the current head position."""
    pending = requests.copy()
    current_head = initial_head
    seek_count = 0
    sequence = [initial_head]
    history = []
    
    while pending:
        closest = min(pending, key=lambda x: abs(x - current_head))
        distance = abs(closest - current_head)
        seek_count += distance
        
        history.append({
            "from": current_head,
            "to": closest,
            "distance": distance
        })
        
        current_head = closest
        sequence.append(closest)
        pending.remove(closest)
        
    return {
        "sequence": sequence,
        "total_movement": seek_count,
        "history": history
    }

# ─────────────────────────────────────────────
#  DISPLAY FUNCTIONS
# ─────────────────────────────────────────────

def display_requests(initial_head: int, requests: list[int]):
    print("\n  Initial State:")
    print(f"  Head Position :  {initial_head}")
    print(f"  Track Requests:  {requests}")

def display_results(results: dict):
    print("\n" + "═" * 60)
    print(f"   {ALGORITHM_NAME} SIMULATION RESULTS")
    print("═" * 60)
    print(f"\n  Total Head Movement :  {results['total_movement']} cylinders")
    print(f"  Execution Sequence  :  {results['sequence']}")
    print("\n" + "═" * 60)

def display_history(results: dict):
    print("\n  Movement History:")
    print(f"  {'Step':<6} {'From':<8} {'To':<8} {'Distance':<10}")
    print("  " + "─" * 35)
    
    for step, move in enumerate(results["history"], 1):
        print(f"  {step:<6}  {move['from']:<8}  {move['to']:<8}  {move['distance']:<10}")

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═" * 50)
    print(f"   DISK MANAGEMENT: {ALGORITHM_NAME}")
    print("═" * 50)
    
    initial_head = random.randint(MIN_CYLINDER, MAX_CYLINDER)
    requests = generate_requests(NUM_REQUESTS)
    
    display_requests(initial_head, requests)
    
    results = calculate_sstf(initial_head, requests)
    
    display_results(results)
    display_history(results)