/* ─────────────────────────────────────────────
   main.js  —  CPU Scheduler Frontend Logic
   Handles: algo selection, config UI, API call, results render
───────────────────────────────────────────── */

// ── STATE ──
let selectedAlgo  = null;
let selectedMode  = "non_preemptive";   // for SJF / Priority
let queueConfigs  = [                   // for MLQ / MFQ
  { algorithm: "FCFS",        quantum: null },
  { algorithm: "Round Robin", quantum: 2    },
  { algorithm: "FCFS",        quantum: null },
];

const ALGO_LABELS = {
  fcfs:     "FCFS",
  sjf:      "SJF",
  priority: "Priority",
  rr:       "Round Robin",
  mlq:      "MLQ",
  mfq:      "MFQ",
};

const QUEUE_ALGOS = ["FCFS", "SJF", "Priority", "Round Robin"];

// ── ELEMENTS ──
const stepSelect  = document.getElementById("step-select");
const stepConfig  = document.getElementById("step-config");
const stepResults = document.getElementById("step-results");

const algoBtns    = document.querySelectorAll(".algo-btn");
const runBtn      = document.getElementById("run-btn");
const resetBtn    = document.getElementById("reset-btn");

const cfgSjfMode      = document.getElementById("cfg-sjf-mode");
const cfgPriMode      = document.getElementById("cfg-priority-mode");
const cfgQuantum      = document.getElementById("cfg-quantum");
const cfgQueues       = document.getElementById("cfg-queues");
const queueConfigRows = document.getElementById("queue-config-rows");


// ── ALGO SELECTION ──
algoBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    algoBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    selectedAlgo = btn.dataset.algo;
    showConfig();
  });
});


function showConfig() {
  // Hide all optional config fields first
  cfgSjfMode.classList.add("hidden");
  cfgPriMode.classList.add("hidden");
  cfgQuantum.classList.add("hidden");
  cfgQueues.classList.add("hidden");

  // Show relevant fields
  if (selectedAlgo === "sjf")      cfgSjfMode.classList.remove("hidden");
  if (selectedAlgo === "priority") cfgPriMode.classList.remove("hidden");
  if (selectedAlgo === "rr")       cfgQuantum.classList.remove("hidden");
  if (selectedAlgo === "mlq" || selectedAlgo === "mfq") {
    cfgQueues.classList.remove("hidden");
    buildQueueRows(selectedAlgo === "mfq");
  }

  stepConfig.classList.remove("hidden");
}


// ── TOGGLE BUTTONS (SJF / Priority mode) ──
document.querySelectorAll(".toggle-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const group = btn.closest(".toggle-group");
    group.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    selectedMode = btn.dataset.mode;
  });
});


// ── QUEUE CONFIG ROWS (MLQ / MFQ) ──
function buildQueueRows(isMFQ) {
  queueConfigRows.innerHTML = "";

  const labels = isMFQ
    ? ["Q1 — highest priority (entry point)", "Q2", "Q3 — lowest priority"]
    : ["Q1 — highest priority", "Q2", "Q3 — lowest priority (runs when Q1 & Q2 empty)"];

  for (let i = 0; i < 3; i++) {
    const row = document.createElement("div");
    row.className = "queue-row";

    // Queue tag
    const tag = document.createElement("span");
    tag.className = `queue-tag q${i + 1}`;
    tag.textContent = `Q${i + 1}`;

    // Algorithm select
    const select = document.createElement("select");
    select.className = "queue-select";
    select.dataset.queueIndex = i;
    QUEUE_ALGOS.forEach(algo => {
      const opt = document.createElement("option");
      opt.value = algo;
      opt.textContent = algo;
      if (algo === queueConfigs[i].algorithm) opt.selected = true;
      select.appendChild(opt);
    });

    // Quantum input (shown only if RR selected)
    const quantumWrap = document.createElement("div");
    quantumWrap.className = "quantum-inline hidden";
    quantumWrap.innerHTML = `quantum <input class="field-input" type="number" min="1" max="10" value="${queueConfigs[i].quantum || 2}" />`;

    if (queueConfigs[i].algorithm === "Round Robin") {
      quantumWrap.classList.remove("hidden");
    }

    // Toggle quantum visibility on select change
    select.addEventListener("change", () => {
      const idx = parseInt(select.dataset.queueIndex);
      queueConfigs[idx].algorithm = select.value;
      queueConfigs[idx].quantum   = null;
      if (select.value === "Round Robin") {
        quantumWrap.classList.remove("hidden");
      } else {
        quantumWrap.classList.add("hidden");
      }
    });

    quantumWrap.querySelector("input")?.addEventListener("change", (e) => {
      const idx = parseInt(select.dataset.queueIndex);
      queueConfigs[idx].quantum = parseInt(e.target.value) || 2;
    });

    // Label
    const lbl = document.createElement("span");
    lbl.style.cssText = "font-size:0.75rem; color:var(--text-dim);";
    lbl.textContent = labels[i];

    row.appendChild(tag);
    row.appendChild(select);
    row.appendChild(quantumWrap);
    row.appendChild(lbl);
    queueConfigRows.appendChild(row);
  }
}


// ── RUN SIMULATION ──
runBtn.addEventListener("click", async () => {
  if (!selectedAlgo) return;

  const n       = parseInt(document.getElementById("num-processes").value) || 4;
  const quantum = parseInt(document.getElementById("quantum").value) || 2;

  // Sync queue configs from DOM
  syncQueueConfigs();

  const payload = {
    algorithm:    selectedAlgo,
    n:            n,
    mode:         selectedMode,
    quantum:      quantum,
    queue_configs: queueConfigs,
  };

  runBtn.textContent = "RUNNING...";
  runBtn.disabled    = true;

  try {
    const res  = await fetch("/api/run", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.error) {
      alert("Error: " + data.error);
      return;
    }

    renderResults(data);
    stepResults.classList.remove("hidden");
    stepResults.scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    alert("Failed to connect to the server. Make sure Flask is running.");
    console.error(err);
  } finally {
    runBtn.textContent = "RUN SIMULATION →";
    runBtn.disabled    = false;
  }
});


function syncQueueConfigs() {
  const selects = queueConfigRows.querySelectorAll(".queue-select");
  selects.forEach((sel, i) => {
    queueConfigs[i].algorithm = sel.value;
    const qInput = sel.closest(".queue-row")?.querySelector(".quantum-inline input");
    queueConfigs[i].quantum   = qInput ? (parseInt(qInput.value) || 2) : null;
  });
}


// ── RENDER RESULTS ──
function renderResults(data) {
  const algo = data.algorithm;

  // ── Generated processes table ──
  const procTable = document.getElementById("proc-table");
  const procCols  = buildProcColumns(algo);
  procTable.querySelector("thead").innerHTML = `<tr>${procCols.headers.map(h => `<th>${h}</th>`).join("")}</tr>`;
  procTable.querySelector("tbody").innerHTML = data.processes.map(p =>
    `<tr>${procCols.cells(p).map((c, i) => `<td${i === 0 ? ' class="pid-cell"' : ""}>${c}</td>`).join("")}</tr>`
  ).join("");

  // ── Gantt Chart ──
  renderGantt(data.gantt || []);

  // ── Results table ──
  const resTable  = document.getElementById("result-table");
  const resCols   = buildResultColumns(algo);
  resTable.querySelector("thead").innerHTML = `<tr>${resCols.headers.map(h => `<th>${h}</th>`).join("")}</tr>`;
  resTable.querySelector("tbody").innerHTML = data.schedule.map(p =>
    `<tr>${resCols.cells(p).map((c, i) => `<td${i === 0 ? ' class="pid-cell"' : ""}>${c}</td>`).join("")}</tr>`
  ).join("");

  // ── Averages ──
  document.getElementById("avg-waiting").textContent    = data.avg_waiting_time    + "s";
  document.getElementById("avg-turnaround").textContent = data.avg_turnaround_time + "s";
}


function buildProcColumns(algo) {
  const base = {
    headers: ["PID", "Arrival", "Burst"],
    cells:   p => [p.pid, p.arrival_time + "s", p.burst_time + "s"],
  };
  if (algo === "priority") {
    return {
      headers: ["PID", "Arrival", "Burst", "Priority"],
      cells:   p => [p.pid, p.arrival_time + "s", p.burst_time + "s", p.priority],
    };
  }
  if (algo === "mlq" || algo === "mfq") {
    return {
      headers: ["PID", "Queue", "Arrival", "Burst", "Priority"],
      cells:   p => [
        p.pid,
        `<span class="queue-badge ${(p.queue || "Q1").toLowerCase()}">${p.queue || "Q1"}</span>`,
        p.arrival_time + "s",
        p.burst_time + "s",
        p.priority,
      ],
    };
  }
  return base;
}


function buildResultColumns(algo) {
  const common = ["PID", "Arrival", "Burst", "Finish", "Waiting", "Turnaround"];
  const commonCells = p => [
    p.pid,
    p.arrival_time + "s",
    p.burst_time + "s",
    p.finish_time + "s",
    p.waiting_time + "s",
    p.turnaround_time + "s",
  ];

  if (algo === "priority") {
    return {
      headers: ["PID", "Arrival", "Burst", "Priority", "Finish", "Waiting", "Turnaround"],
      cells:   p => [p.pid, p.arrival_time + "s", p.burst_time + "s", p.priority, p.finish_time + "s", p.waiting_time + "s", p.turnaround_time + "s"],
    };
  }
  if (algo === "mlq") {
    return {
      headers: ["PID", "Queue", "Arrival", "Burst", "Priority", "Finish", "Waiting", "Turnaround"],
      cells:   p => [
        p.pid,
        `<span class="queue-badge ${(p.queue || "Q1").toLowerCase()}">${p.queue || "Q1"}</span>`,
        p.arrival_time + "s", p.burst_time + "s", p.priority,
        p.finish_time + "s", p.waiting_time + "s", p.turnaround_time + "s",
      ],
    };
  }
  if (algo === "mfq") {
    return {
      headers: ["PID", "Path", "Arrival", "Burst", "Priority", "Finish", "Waiting", "Turnaround"],
      cells:   p => [
        p.pid,
        p.queue_path || "Q1",
        p.arrival_time + "s", p.burst_time + "s", p.priority,
        p.finish_time + "s", p.waiting_time + "s", p.turnaround_time + "s",
      ],
    };
  }
  return { headers: common, cells: commonCells };
}


// ── GANTT RENDER ──
function renderGantt(gantt) {
  const bar    = document.getElementById("gantt-bar");
  const times  = document.getElementById("gantt-times");
  bar.innerHTML   = "";
  times.innerHTML = "";

  if (!gantt.length) return;

  const total    = gantt[gantt.length - 1].end;
  const BASE_PX  = 560;   // base width to distribute across

  // Queue color map
  const qClass = { Q1: "seg-q1", Q2: "seg-q2", Q3: "seg-q3", IDLE: "seg-idle" };

  gantt.forEach(seg => {
    const duration = seg.end - seg.start;
    const width    = Math.max((duration / total) * BASE_PX, 28);

    const el = document.createElement("div");
    el.className = "gantt-seg " + (qClass[seg.queue] || "seg-default");
    el.style.width   = width + "px";
    el.style.minWidth = width + "px";
    el.textContent   = seg.pid;
    el.title         = `${seg.pid} | ${seg.start}s → ${seg.end}s (${duration}s)`;
    bar.appendChild(el);
  });

  // Time markers
  const uniqueTimes = [...new Set(gantt.flatMap(s => [s.start, s.end]))].sort((a, b) => a - b);
  let prevPos = 0;
  uniqueTimes.forEach(t => {
    const pos   = (t / total) * BASE_PX;
    const mark  = document.createElement("span");
    mark.className   = "gantt-time-mark";
    mark.style.width = (pos - prevPos) + "px";
    mark.textContent = t + "s";
    times.appendChild(mark);
    prevPos = pos;
  });
}


// ── RESET ──
resetBtn.addEventListener("click", () => {
  selectedAlgo = null;
  selectedMode = "non_preemptive";

  algoBtns.forEach(b => b.classList.remove("active"));
  stepConfig.classList.add("hidden");
  stepResults.classList.add("hidden");

  document.getElementById("num-processes").value = 4;
  document.getElementById("quantum").value        = 2;

  window.scrollTo({ top: 0, behavior: "smooth" });
});