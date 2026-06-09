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
    mm_with_comp.py
    mm_without_comp.py
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
from memory_management.mm_with_compaction    import generate_processes as gen_mem, run_simulation as run_mem_with
from memory_management.mm_without_compaction import run_simulation as run_mem_without

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

    algo       = body.get("algorithm", "First-Fit")   # First-Fit | Best-Fit | Worst-Fit
    mode       = body.get("mode", "with_compaction")  # with_compaction | without_compaction
    n          = max(1, min(int(body.get("n", 10)), 30))

    try:
        processes = gen_mem(n)

        if mode == "with_compaction":
            results = run_mem_with(processes, algo)
        else:
            results = run_mem_without(processes, algo)

        return jsonify({
            "algorithm":       algo,
            "mode":            mode,
            "processes":       processes,
            "history":         results["history"],
            "allocated":       results["allocated"],
            "rejected":        results["rejected"],
            "allocation_rate": results["allocation_rate"],
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