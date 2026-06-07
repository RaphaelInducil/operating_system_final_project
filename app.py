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
  cpu_scheduling/
    fcfs.py
    sjf.py
    priority.py
    round_robin.py
    mlq.py
    mfq.py
"""

from flask import Flask, render_template, request, jsonify
from cpu_scheduling.fcfs        import generate_processes as gen_fcfs,        run_fcfs
from cpu_scheduling.sjf         import generate_processes as gen_sjf,         run_sjf, run_srtf
from cpu_scheduling.priority    import generate_processes as gen_priority,     run_priority_np, run_priority_p
from cpu_scheduling.rr          import generate_processes as gen_rr,          run_round_robin
from cpu_scheduling.mlq         import generate_processes as gen_mlq,         run_mlq
from cpu_scheduling.mlfq import generate_processes as gen_mfq, run_mfq

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


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

    # Clamp n to valid range
    n = max(1, min(n, 20))

    try:
        # ── FCFS ──
        if algo == "fcfs":
            processes = gen_fcfs(n)
            results   = run_fcfs(processes)
            return jsonify({
                "algorithm":         "fcfs",
                "processes":         processes,
                "schedule":          results["schedule"],
                "gantt":             results["gantt"],
                "avg_waiting_time":  results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        # ── SJF ──
        elif algo == "sjf":
            processes = gen_sjf(n)
            if mode == "preemptive":
                results = run_srtf(processes)
            else:
                results = run_sjf(processes)
            return jsonify({
                "algorithm":         "sjf",
                "mode":              mode,
                "processes":         processes,
                "schedule":          results["schedule"],
                "gantt":             results["gantt"],
                "avg_waiting_time":  results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        # ── PRIORITY ──
        elif algo == "priority":
            processes = gen_priority(n)
            if mode == "preemptive":
                results = run_priority_p(processes)
            else:
                results = run_priority_np(processes)
            return jsonify({
                "algorithm":         "priority",
                "mode":              mode,
                "processes":         processes,
                "schedule":          results["schedule"],
                "gantt":             results["gantt"],
                "avg_waiting_time":  results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        # ── ROUND ROBIN ──
        elif algo == "rr":
            processes = gen_rr(n)
            results   = run_round_robin(processes, quantum)
            return jsonify({
                "algorithm":         "rr",
                "quantum":           quantum,
                "processes":         processes,
                "schedule":          results["schedule"],
                "gantt":             results["gantt"],
                "avg_waiting_time":  results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        # ── MLQ ──
        elif algo == "mlq":
            processes = gen_mlq(n)
            # Attach queue label to each process for display
            for p in processes:
                p["queue"] = f"Q{p['queue'] + 1}"
            results = run_mlq(
                [{**p, "queue": int(p["queue"][1]) - 1} for p in processes],
                queue_configs
            )
            return jsonify({
                "algorithm":         "mlq",
                "processes":         processes,
                "schedule":          results["schedule"],
                "gantt":             results["gantt"],
                "avg_waiting_time":  results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        # ── MFQ ──
        elif algo == "mfq":
            processes = gen_mfq(n)
            results   = run_mfq(processes, queue_configs)
            return jsonify({
                "algorithm":         "mfq",
                "processes":         processes,
                "schedule":          results["schedule"],
                "gantt":             results["gantt"],
                "avg_waiting_time":  results["avg_waiting_time"],
                "avg_turnaround_time": results["avg_turnaround_time"],
            })

        else:
            return jsonify({"error": f"Unknown algorithm: {algo}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)