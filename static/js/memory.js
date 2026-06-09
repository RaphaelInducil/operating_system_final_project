/* ─────────────────────────────────────────────
   memory.js  —  Memory Management Frontend Logic
   Handles: algo selection, compaction toggle, API call, results render
───────────────────────────────────────────── */

// ── STATE ──
let memAlgo = null;
let memMode = "with_compaction";

const MEM_ALGOS = ["First-Fit", "Best-Fit", "Worst-Fit"];

// ── ELEMENTS ──
const memAlgoBtns   = document.querySelectorAll(".mem-algo-btn");
const memRunBtn     = document.getElementById("mem-run-btn");
const memResetBtn   = document.getElementById("mem-reset-btn");
const memStepConfig  = document.getElementById("mem-step-config");
const memStepResults = document.getElementById("mem-step-results");

// ── ALGO SELECTION ──
memAlgoBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    memAlgoBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    memAlgo = btn.dataset.algo;
    memStepConfig.classList.remove("hidden");
  });
});

// ── COMPACTION TOGGLE ──
document.querySelectorAll(".mem-toggle-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mem-toggle-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    memMode = btn.dataset.mode;
  });
});

// ── RUN ──
memRunBtn.addEventListener("click", async () => {
  if (!memAlgo) return;

  let n = parseInt(document.getElementById("mem-num-processes").value);
  if (isNaN(n) || n < 1) { n = 10; document.getElementById("mem-num-processes").value = 10; }

  const payload = { algorithm: memAlgo, mode: memMode, n };

  memRunBtn.textContent = "RUNNING...";
  memRunBtn.disabled    = true;

  try {
    const res  = await fetch("/api/memory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.error) { alert("Error: " + data.error); return; }

    renderMemoryResults(data);
    memStepResults.classList.remove("hidden");
    memStepResults.scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    alert("Failed to connect to the server. Make sure Flask is running.");
    console.error(err);
  } finally {
    memRunBtn.innerHTML = `<span>RUN SIMULATION</span><span class="run-arrow">→</span>`;
    memRunBtn.disabled  = false;
  }
});

// ── RESET ──
memResetBtn.addEventListener("click", () => {
  memAlgo = null;
  memAlgoBtns.forEach(b => b.classList.remove("active"));
  memStepConfig.classList.add("hidden");
  memStepResults.classList.add("hidden");
  document.getElementById("mem-num-processes").value = 10;
  window.scrollTo({ top: 0, behavior: "smooth" });
});

// ── RENDER ──
function renderMemoryResults(data) {
  // ── Process table ──
  const pt = document.getElementById("mem-proc-table");
  pt.querySelector("thead").innerHTML = `<tr><th>PID</th><th>Size (KB)</th><th>Duration</th></tr>`;
  pt.querySelector("tbody").innerHTML = data.processes.map(p =>
    `<tr><td class="pid-cell">${p.pid}</td><td>${p.size} KB</td><td>${p.duration}</td></tr>`
  ).join("");

  // ── History table ──
  const ht = document.getElementById("mem-history-table");
  ht.querySelector("thead").innerHTML = `<tr><th>Step</th><th>PID</th><th>Size</th><th>Status</th><th>Allocated</th><th>Free</th></tr>`;
  ht.querySelector("tbody").innerHTML = data.history.map(h => {
    const statusClass = h.status === "ALLOCATED" ? "status-alloc" : "status-reject";
    return `<tr>
      <td class="pid-cell">${h.step}</td>
      <td>${h.pid}</td>
      <td>${h.size} KB</td>
      <td><span class="status-badge ${statusClass}">${h.status}</span></td>
      <td>${h.memory.allocated} KB</td>
      <td>${h.memory.free} KB</td>
    </tr>`;
  }).join("");

  // ── Memory bar ──
  renderMemoryBar(data.history);

  // ── Stats ──
  document.getElementById("mem-allocated-count").textContent = data.allocated;
  document.getElementById("mem-rejected-count").textContent  = data.rejected;
  document.getElementById("mem-alloc-rate").textContent      = data.allocation_rate + "%";
}

function renderMemoryBar(history) {
  const wrap = document.getElementById("mem-bar-wrap");
  wrap.innerHTML = "";

  if (!history.length) return;

  // Show last memory snapshot as a visual bar
  const last  = history[history.length - 1].memory;
  const total = last.total;

  const allocPct = ((last.allocated / total) * 100).toFixed(1);
  const freePct  = ((last.free      / total) * 100).toFixed(1);

  wrap.innerHTML = `
    <div class="mem-bar-label" style="display:flex;justify-content:space-between;margin-bottom:0.4rem;">
      <span style="font-family:var(--mono);font-size:0.7rem;color:var(--accent);">ALLOCATED ${last.allocated} KB (${allocPct}%)</span>
      <span style="font-family:var(--mono);font-size:0.7rem;color:var(--text-dim);">FREE ${last.free} KB (${freePct}%)</span>
    </div>
    <div style="display:flex;height:28px;border-radius:var(--radius);overflow:hidden;border:1px solid var(--border);">
      <div style="width:${allocPct}%;background:#1a2600;border-right:2px solid var(--accent);transition:width 0.4s;"></div>
      <div style="flex:1;background:var(--bg3);"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:0.35rem;">
      <span style="font-family:var(--mono);font-size:0.65rem;color:var(--text-dim);">0 KB</span>
      <span style="font-family:var(--mono);font-size:0.65rem;color:var(--text-dim);">${total} KB TOTAL</span>
    </div>
  `;
}