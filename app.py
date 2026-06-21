"""
app.py
Flask entry point — serves the frontend and exposes /api/run
which routes to the correct scheduling algorithm.

Folder structure expected:
  app.py
  templates/
    index.html
  static/
    css/style.css
    js/main.js
    js/memory.js
    js/virtual.js
  cpu_scheduling/
    fcfs.py  sjf.py  priority.py  round_robin.py  mlq.py  mfq.py
  memory_management/
    mft_partitioning.py
    mvt_partitioning.py
  virtual_memory/
    vir_mem.py
"""

from flask import Flask, render_template, request, jsonify

# ── CPU Scheduling ──
from cpu_scheduling.fcfs        import generate_processes as gen_fcfs,        run_fcfs
from cpu_scheduling.sjf         import generate_processes as gen_sjf,         run_sjf, run_srtf
from cpu_scheduling.priority    import generate_processes as gen_priority,     run_priority_np, run_priority_p
from cpu_scheduling.rr          import generate_processes as gen_rr,          run_round_robin
from cpu_scheduling.mlq         import generate_processes as gen_mlq,         run_mlq
from cpu_scheduling.mlfq        import generate_processes as gen_mfq,         run_mfq

# ── Memory Management ──
from memory_management.mft_partitioning import (
    generate_process_sizes as gen_mft_processes, 
    generate_fixed_partitions,
    run_first_fit, 
    run_best_fit, 
    run_worst_fit
)
from memory_management.mvt_partitioning import (
    generate_memory_events as gen_mvt_events,
    run_without_compaction, 
    run_with_compaction
)

# ── Virtual Memory ──
from virtual_memory.vir_mem import generate_reference_string, run_fifo, run_lru, run_optimal

app = Flask(__name__)


# ─────────────────────────────────────────────
#  PAGES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────
#  CPU SCHEDULING API
# ─────────────────────────────────────────────

@app.route("/api/run", methods=["POST"])
def run_algorithm():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "No data received"}), 400

    algo          = body.get("algorithm")
    n             = int(body.get("n", 4))
    mode          = body.get("mode", "non_preemptive")
    quantum       = int(body.get("quantum", 2))
    queue_configs = body.get("queue_configs", [])

    n = max(1, min(n, 20))

    try:
        if algo == "fcfs":
            processes = gen_fcfs(n)
            results   = run_fcfs(processes)
            return jsonify({
                "algorithm": "fcfs", "processes": processes,
                "schedule": results["schedule"], "gantt": results["gantt"],
                "avg_waiting_time": results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        elif algo == "sjf":
            processes = gen_sjf(n)
            results   = run_srtf(processes) if mode == "preemptive" else run_sjf(processes)
            return jsonify({
                "algorithm": "sjf", "mode": mode, "processes": processes,
                "schedule": results["schedule"], "gantt": results["gantt"],
                "avg_waiting_time": results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        elif algo == "priority":
            processes = gen_priority(n)
            results   = run_priority_p(processes) if mode == "preemptive" else run_priority_np(processes)
            return jsonify({
                "algorithm": "priority", "mode": mode, "processes": processes,
                "schedule": results["schedule"], "gantt": results["gantt"],
                "avg_waiting_time": results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        elif algo == "rr":
            processes = gen_rr(n)
            results   = run_round_robin(processes, quantum)
            return jsonify({
                "algorithm": "rr", "quantum": quantum, "processes": processes,
                "schedule": results["schedule"], "gantt": results["gantt"],
                "avg_waiting_time": results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        elif algo == "mlq":
            processes = gen_mlq(n)
            for p in processes:
                p["queue"] = f"Q{p['queue'] + 1}"
            results = run_mlq(
                [{**p, "queue": int(p["queue"][1]) - 1} for p in processes],
                queue_configs
            )
            return jsonify({
                "algorithm": "mlq", "processes": processes,
                "schedule": results["schedule"], "gantt": results["gantt"],
                "avg_waiting_time": results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        elif algo == "mfq":
            processes = gen_mfq(n)
            results   = run_mfq(processes, queue_configs)
            return jsonify({
                "algorithm": "mfq", "processes": processes,
                "schedule": results["schedule"], "gantt": results["gantt"],
                "avg_waiting_time": results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        else:
            return jsonify({"error": f"Unknown algorithm: {algo}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
#  MEMORY MANAGEMENT API
# ─────────────────────────────────────────────

@app.route("/api/memory", methods=["POST"])
def run_memory():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "No data received"}), 400

    # Ensure frontend formats ("First-Fit") match python function expectations ("First Fit")
    algo       = body.get("algorithm", "First-Fit").replace("-", " ")
    mode       = body.get("mode", "mvt_with_compaction") 
    n          = max(1, min(int(body.get("n", 10)), 30))
    
    total_memory = int(body.get("total_memory", 1024))
    partitions   = body.get("partitions", None)

    try:
        # Route to the appropriate simulation based on the requested mode
        if mode == "mft":
            processes = gen_mft_processes(n)
            
            # Use provided partitions, or generate 5 random ones if none provided
            parts = partitions if partitions else generate_fixed_partitions(5)

            if algo == "First Fit":
                results = run_first_fit(processes, parts)
            elif algo == "Best Fit":
                results = run_best_fit(processes, parts)
            elif algo == "Worst Fit":
                results = run_worst_fit(processes, parts)
            else:
                results = run_first_fit(processes, parts) # Fallback
                
            input_data = processes

        else:
            # MVT generates an event stream (positive for alloc, negative for free)
            events = gen_mvt_events(n)

            if mode == "mvt_with_compaction":
                results = run_with_compaction(events, total_memory)
            else:
                results = run_without_compaction(events, total_memory)
                
            input_data = events

        # Safely package all data regardless of whether it's MFT or MVT
        return jsonify({
            "algorithm":       algo,
            "mode":            mode,
            "processes":       input_data,  
            "history":         results.get("history", []),
            "allocated":       results.get("allocated", 0),
            "unallocated":     results.get("unallocated", 0), # Exists only in MFT
            "rejected":        results.get("rejected", 0),    # Exists only in MVT
            "allocation_rate": results.get("alloc_rate", 0),
            "total_frag":      results.get("total_frag", 0),  # Exists only in MFT
            "ext_frag":        results.get("ext_frag", 0),    # Exists only in MVT
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
#  VIRTUAL MEMORY API
# ─────────────────────────────────────────────

@app.route("/api/virtual", methods=["POST"])
def run_virtual():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "No data received"}), 400

    algo        = body.get("algorithm", "FIFO")   # FIFO | LRU | Optimal
    ref_length  = max(5, min(int(body.get("ref_length", 15)), 50))
    frame_count = max(1, min(int(body.get("frame_count", 3)), 10))

    try:
        reference_string = generate_reference_string(ref_length)

        if algo == "FIFO":
            results = run_fifo(reference_string, frame_count)
        elif algo == "LRU":
            results = run_lru(reference_string, frame_count)
        else:
            results = run_optimal(reference_string, frame_count)

        return jsonify({
            "algorithm":        algo,
            "frame_count":      frame_count,
            "reference_string": reference_string,
            "history":          results["history"],
            "hits":             results["hits"],
            "faults":           results["faults"],
            "hit_rate":         results["hit_rate"],
            "fault_rate":       results["fault_rate"],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)