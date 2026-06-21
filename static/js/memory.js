/* ─────────────────────────────────────────────
   memory.js  —  Memory Management Frontend Logic
   Handles: algo selection, compaction toggle, API call, results render
───────────────────────────────────────────── */

// ── STATE ──
let memAlgo = null;
let memMode = "mvt_with_compaction"; // Default matched to HTML/Backend

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

// ── CONFIGURATION TOGGLE (MFT/MVT Modes) ──
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

  // Adding total_memory and partitions optionally if you add inputs for them later
  const payload = { 
      algorithm: memAlgo, 
      mode: memMode, 
      n: n 
  };

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
  const isMFT = data.mode === "mft";

  // ── 1. Process / Event Table ──
  const pt = document.getElementById("mem-proc-table");
  
  if (isMFT) {
      pt.querySelector("thead").innerHTML = `<tr><th>PID</th><th>Requested Size</th></tr>`;
      if (data.processes && data.processes.length > 0) {
          pt.querySelector("tbody").innerHTML = data.processes.map((size, i) =>
            `<tr><td class="pid-cell">P${i+1}</td><td>${size} KB</td></tr>`
          ).join("");
      }
  } else {
      pt.querySelector("thead").innerHTML = `<tr><th>Event #</th><th>Action</th><th>Target</th></tr>`;
      if (data.processes && data.processes.length > 0) {
          pt.querySelector("tbody").innerHTML = data.processes.map((ev, i) => {
              const action = ev > 0 ? "ALLOCATE" : "DEALLOCATE";
              const target = ev > 0 ? `${ev} KB` : `PID P${-ev}`;
              return `<tr><td class="pid-cell">${i+1}</td><td>${action}</td><td>${target}</td></tr>`;
          }).join("");
      }
  }

  if (!data.processes || data.processes.length === 0) {
      pt.querySelector("tbody").innerHTML = `<tr><td colspan="3">No events generated.</td></tr>`;
  }

  // ── 2. History Table ──
  const ht = document.getElementById("mem-history-table");
  ht.querySelector("thead").innerHTML = `<tr><th>Step</th><th>Action / Target</th><th>Status</th><th>Memory Layout Snapshot</th></tr>`;
  
  if (data.history && data.history.length > 0) {
      ht.querySelector("tbody").innerHTML = data.history.map((h, i) => {
        // Status color logic
        let statusClass = "status-reject";
        if (h.status === "ALLOCATED" || h.status.includes("COMPACTED")) statusClass = "status-alloc";
        if (h.status === "FREED") statusClass = "status-free"; // Assuming you have a CSS class for freed
        
        // Format memory map layout
        let mapStr = "";
        if (isMFT) {
            // MFT: array of {p: 'P1', f: 0}
            mapStr = h.memory.map(b => b.p ? `[<b>${b.p}</b> | Frag: ${b.f}K]` : `[FREE]`).join(" ");
        } else {
            // MVT: array of {id: 'P1', size: 100}
            mapStr = h.memory.map(b => b.id === 'FREE' ? `[FREE: ${b.size}K]` : `[<b>${b.id}</b>: ${b.size}K]`).join(" ");
        }
        
        return `<tr>
          <td class="pid-cell">${i+1}</td>
          <td>${h.action || h.process || '-'}</td>
          <td><span class="status-badge ${statusClass}">${h.status || '-'}</span></td>
          <td style="font-family:var(--mono); font-size:0.8rem; word-break:break-all;">${mapStr}</td>
        </tr>`;
      }).join("");
  } else {
      ht.querySelector("tbody").innerHTML = `<tr><td colspan="4">No history data returned.</td></tr>`;
  }

  // ── 3. Stats Board ──
  document.getElementById("mem-allocated-count").textContent = data.allocated || 0;
  
  // Update rejected/unallocated dynamically
  const rejElem = document.getElementById("mem-rejected-count");
  if (rejElem) {
      rejElem.textContent = isMFT ? (data.unallocated || 0) : (data.rejected || 0);
      const prevSpan = rejElem.previousElementSibling;
      if (prevSpan && prevSpan.tagName === 'SPAN') {
          prevSpan.textContent = isMFT ? "Unallocated" : "Rejected";
      }
  }
  document.getElementById("mem-alloc-rate").textContent = (data.allocation_rate || 0) + "%";

  // ── 4. Memory Bar ──
  renderMemoryBar(data);
}

function renderMemoryBar(data) {
  const wrap = document.getElementById("mem-bar-wrap");
  wrap.innerHTML = "";

  if (!data.history || !data.history.length) return;

  const lastStep = data.history[data.history.length - 1];
  if (!lastStep.memory) return;

  const isMFT = data.mode === "mft";
  let barHtml = "";

  if (isMFT) {
      // For MFT, render fixed partitions equally spaced
      const partitions = lastStep.memory;
      let totalFrag = data.total_frag || 0;

      const segments = partitions.map(p => {
          const isFree = !p.p;
          const bg = isFree ? "var(--bg3)" : "#1a2600";
          const border = isFree ? "none" : "2px solid var(--accent)";
          const text = isFree ? "FREE" : `${p.p}`;
          return `<div style="flex:1; background:${bg}; border-right:${border}; display:flex; align-items:center; justify-content:center; font-family:var(--mono); font-size:0.7rem; color:var(--text);">${text}</div>`;
      }).join("");

      barHtml = `
        <div class="mem-bar-label" style="display:flex;justify-content:space-between;margin-bottom:0.4rem;">
          <span style="font-family:var(--mono);font-size:0.7rem;color:var(--accent);">FINAL MEMORY SNAPSHOT (MFT)</span>
          <span style="font-family:var(--mono);font-size:0.7rem;color:var(--text-dim);">TOTAL INT. FRAG: ${totalFrag} KB</span>
        </div>
        <div style="display:flex;height:34px;border-radius:var(--radius);overflow:hidden;border:1px solid var(--border);">
          ${segments}
        </div>
      `;
  } else {
      // For MVT, calculate exact percentages based on block sizes
      const blocks = lastStep.memory;
      const totalMemory = blocks.reduce((sum, b) => sum + b.size, 0);
      let extFrag = data.ext_frag || 0;

      const segments = blocks.map(b => {
          const isFree = b.id === "FREE";
          const pct = ((b.size / totalMemory) * 100).toFixed(2);
          const bg = isFree ? "var(--bg3)" : "#1a2600";
          const border = isFree ? "1px solid var(--border)" : "2px solid var(--accent)";
          const text = pct > 5 ? (isFree ? "" : b.id) : ""; // Hide text if block is too small
          
          return `<div title="${b.id}: ${b.size}KB" style="width:${pct}%; background:${bg}; border-right:${border}; display:flex; align-items:center; justify-content:center; font-family:var(--mono); font-size:0.7rem; color:var(--text); overflow:hidden;">${text}</div>`;
      }).join("");

      barHtml = `
        <div class="mem-bar-label" style="display:flex;justify-content:space-between;margin-bottom:0.4rem;">
          <span style="font-family:var(--mono);font-size:0.7rem;color:var(--accent);">FINAL MEMORY SNAPSHOT (MVT)</span>
          <span style="font-family:var(--mono);font-size:0.7rem;color:var(--text-dim);">TOTAL EXT. FRAG: ${extFrag} KB</span>
        </div>
        <div style="display:flex;height:34px;border-radius:var(--radius);overflow:hidden;border:1px solid var(--border);">
          ${segments}
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:0.35rem;">
          <span style="font-family:var(--mono);font-size:0.65rem;color:var(--text-dim);">0 KB</span>
          <span style="font-family:var(--mono);font-size:0.65rem;color:var(--text-dim);">${totalMemory} KB TOTAL</span>
        </div>
      `;
  }

  wrap.innerHTML = barHtml;
}