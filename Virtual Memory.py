# 05/24/26
# virtual memory page replacement algorithms with random reference string generation

import random


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

ALGORITHMS = ["FIFO", "LRU", "Optimal"]


# ─────────────────────────────────────────────
#  RANDOM REFERENCE STRING GENERATOR
# ─────────────────────────────────────────────

def generate_reference_string(length: int) -> list[int]:
    """
    Generates a random page reference string.

    Controlled ranges:
      - pages : 0 to 9
    """

    return [random.randint(0, 9) for _ in range(length)]


# ─────────────────────────────────────────────
#  FIFO PAGE REPLACEMENT
# ─────────────────────────────────────────────

def run_fifo(reference_string: list[int], frame_count: int) -> dict:
    """
    First-In First-Out Page Replacement.

    Replaces the oldest page in memory first.
    """

    frames = []
    pointer = 0

    history = []

    hits = 0
    faults = 0

    for page in reference_string:

        if page in frames:
            hits += 1
            status = "HIT"

        else:
            faults += 1
            status = "FAULT"

            if len(frames) < frame_count:
                frames.append(page)

            else:
                frames[pointer] = page
                pointer = (pointer + 1) % frame_count

        history.append({
            "page":   page,
            "frames": frames.copy(),
            "status": status,
        })

    total = hits + faults

    return {
        "history":      history,
        "hits":         hits,
        "faults":       faults,
        "hit_rate":     round((hits / total) * 100, 2),
        "fault_rate":   round((faults / total) * 100, 2),
    }


# ─────────────────────────────────────────────
#  LRU PAGE REPLACEMENT
# ─────────────────────────────────────────────

def run_lru(reference_string: list[int], frame_count: int) -> dict:
    """
    Least Recently Used Page Replacement.

    Replaces the page that has not been used
    for the longest time.
    """

    frames = []
    recent = []

    history = []

    hits = 0
    faults = 0

    for page in reference_string:

        if page in frames:
            hits += 1
            status = "HIT"

            recent.remove(page)
            recent.append(page)

        else:
            faults += 1
            status = "FAULT"

            if len(frames) < frame_count:
                frames.append(page)

            else:
                lru_page = recent.pop(0)
                index = frames.index(lru_page)
                frames[index] = page

            recent.append(page)

        history.append({
            "page":   page,
            "frames": frames.copy(),
            "status": status,
        })

    total = hits + faults

    return {
        "history":      history,
        "hits":         hits,
        "faults":       faults,
        "hit_rate":     round((hits / total) * 100, 2),
        "fault_rate":   round((faults / total) * 100, 2),
    }


# ─────────────────────────────────────────────
#  OPTIMAL PAGE REPLACEMENT
# ─────────────────────────────────────────────

def run_optimal(reference_string: list[int], frame_count: int) -> dict:
    """
    Optimal Page Replacement.

    Replaces the page that will not be used
    for the longest time in the future.
    """

    frames = []

    history = []

    hits = 0
    faults = 0

    for i in range(len(reference_string)):

        page = reference_string[i]

        if page in frames:
            hits += 1
            status = "HIT"

        else:
            faults += 1
            status = "FAULT"

            if len(frames) < frame_count:
                frames.append(page)

            else:
                future = reference_string[i + 1:]

                indexes = []

                for frame in frames:

                    if frame in future:
                        indexes.append(future.index(frame))

                    else:
                        indexes.append(float("inf"))

                replace_index = indexes.index(max(indexes))
                frames[replace_index] = page

        history.append({
            "page":   page,
            "frames": frames.copy(),
            "status": status,
        })

    total = hits + faults

    return {
        "history":      history,
        "hits":         hits,
        "faults":       faults,
        "hit_rate":     round((hits / total) * 100, 2),
        "fault_rate":   round((faults / total) * 100, 2),
    }


# ─────────────────────────────────────────────
#  DISPLAY
# ─────────────────────────────────────────────

def display_reference_string(reference_string: list[int]):
    """Displays the generated reference string."""

    print("\n  Reference String:")
    print("  " + " ".join(map(str, reference_string)))


def display_frames(results: dict):
    """Displays frame changes."""

    history = results["history"]

    print("\n  Frame Table:")
    print(f"  {'Page':<8} {'Frames':<25} {'Status':>10}")
    print("  " + "-" * 48)

    for step in history:

        frames_display = str(step["frames"])

        print(
            f"  {step['page']:<8}"
            f" {frames_display:<25}"
            f" {step['status']:>10}"
        )


def display_results(results: dict, algorithm: str):
    """Displays page replacement statistics."""

    print("\n" + "=" * 65)
    print(f"   {algorithm} PAGE REPLACEMENT RESULTS")
    print("=" * 65)

    print(f"\n  Total Hits       :  {results['hits']}")
    print(f"  Total Faults     :  {results['faults']}")

    print(f"\n  Hit Rate         :  {results['hit_rate']}%")
    print(f"  Fault Rate       :  {results['fault_rate']}%")

    print("=" * 65)


# ─────────────────────────────────────────────
#  USER INPUT
# ─────────────────────────────────────────────

def ask_reference_length() -> int:

    while True:
        try:
            length = int(input("\n  Reference string length: "))

            if length <= 0:
                print("  ⚠  Please enter a number greater than 0.")

            elif length > 50:
                print("  ⚠  Maximum length is 50.")

            else:
                return length

        except ValueError:
            print("  ⚠  Please enter a whole number.")


def ask_frame_count() -> int:

    while True:
        try:
            frame_count = int(input("  Number of frames: "))

            if frame_count <= 0:
                print("  ⚠  Please enter a number greater than 0.")

            elif frame_count > 10:
                print("  ⚠  Maximum frame count is 10.")

            else:
                return frame_count

        except ValueError:
            print("  ⚠  Please enter a whole number.")


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
    print("   VIRTUAL MEMORY MANAGEMENT")
    print("=" * 50)

    length      = ask_reference_length()
    frame_count = ask_frame_count()
    algorithm   = ask_algorithm()

    reference_string = generate_reference_string(length)

    display_reference_string(reference_string)

    print(f"\n  Algorithm Used: {algorithm}")

    if algorithm == "FIFO":
        results = run_fifo(reference_string, frame_count)

    elif algorithm == "LRU":
        results = run_lru(reference_string, frame_count)

    else:
        results = run_optimal(reference_string, frame_count)

    display_frames(results)
    display_results(results, algorithm)