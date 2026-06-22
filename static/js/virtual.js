/* ─────────────────────────────────────────────
   virtual.js  —  Virtual Memory Frontend Logic
   Handles: algo selection, config, API call, results render
───────────────────────────────────────────── */

// ── STATE ──
let virtAlgo = null;

// ── ELEMENTS ──
const virtAlgoBtns    = document.querySelectorAll(".virt-algo-btn");
const virtRunBtn      = document.getElementById("virt-run-btn");
const virtResetBtn    = document.getElementById("virt-reset-btn");
const virtStepConfig  = document.getElementById("virt-step-config");
const virtStepResults = document.getElementById("virt-step-results");

// ── ALGO SELECTION ──
virtAlgoBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    virtAlgoBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    virtAlgo = btn.dataset.algo;
    virtStepConfig.classList.remove("hidden");
  });
});

// ── RUN ──
virtRunBtn.addEventListener("click", async () => {
  if (!virtAlgo) return;

  let refLength  = parseInt(document.getElementById("virt-ref-length").value);
  let frameCount = parseInt(document.getElementById("virt-frame-count").value);

  if (isNaN(refLength)  || refLength  < 5)  { refLength  = 15; document.getElementById("virt-ref-length").value  = 15; }
  if (isNaN(frameCount) || frameCount < 1)  { frameCount = 3;  document.getElementById("virt-frame-count").value = 3;  }

  const payload = { algorithm: virtAlgo, ref_length: refLength, frame_count: frameCount };

  virtRunBtn.textContent = "RUNNING...";
  virtRunBtn.disabled    = true;

  try {
    const res  = await fetch("/api/virtual", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.error) { alert("Error: " + data.error); return; }

    renderVirtualResults(data);
    virtStepResults.classList.remove("hidden");
    virtStepResults.scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    alert("Failed to connect to the server. Make sure Flask is running.");
    console.error(err);
  } finally {
    virtRunBtn.innerHTML = `<span>RUN SIMULATION</span><span class="run-arrow">→</span>`;
    virtRunBtn.disabled  = false;
  }
});

// ── RESET ──
virtResetBtn.addEventListener("click", () => {
  virtAlgo = null;
  virtAlgoBtns.forEach(b => b.classList.remove("active"));
  virtStepConfig.classList.add("hidden");
  virtStepResults.classList.add("hidden");
  document.getElementById("virt-ref-length").value  = 15;
  document.getElementById("virt-frame-count").value = 3;
  window.scrollTo({ top: 0, behavior: "smooth" });
});

// ── RENDER ──
function renderVirtualResults(data) {
  // ── Reference string display ──
  const refWrap = document.getElementById("virt-ref-string");
  refWrap.innerHTML = data.reference_string.map(p =>
    `<span class="ref-page">${p}</span>`
  ).join("");

  // ── Frame table ──
  const ft = document.getElementById("virt-frame-table");
  const frameHeaders = Array.from({ length: data.frame_count }, (_, i) => `<th>Frame ${i + 1}</th>`).join("");
  ft.querySelector("thead").innerHTML = `<tr><th>Step</th><th>Page</th>${frameHeaders}<th>Status</th></tr>`;
  ft.querySelector("tbody").innerHTML = data.history.map((h, i) => {
    const statusClass = h.status === "HIT" ? "status-hit" : "status-fault";
    // Pad frames to frame_count
    const frameCells = Array.from({ length: data.frame_count }, (_, fi) => {
      const val = h.frames[fi] !== undefined ? h.frames[fi] : "—";
      return `<td style="font-family:var(--mono);color:var(--text-mid);">${val}</td>`;
    }).join("");
    return `<tr>
      <td class="pid-cell">${i + 1}</td>
      <td style="font-family:var(--mono);font-weight:700;color:var(--accent);">${h.page}</td>
      ${frameCells}
      <td><span class="status-badge ${statusClass}">${h.status}</span></td>
    </tr>`;
  }).join("");

  // ── Frame visualizer ──
  drawVirtualVisualizer(data);

  // ── Stats ──
  document.getElementById("virt-hits").textContent      = data.hits;
  document.getElementById("virt-faults").textContent    = data.faults;
  document.getElementById("virt-hit-rate").textContent  = data.hit_rate + "%";
  document.getElementById("virt-fault-rate").textContent = data.fault_rate + "%";
}

function drawVirtualVisualizer(data) {
  const container = document.getElementById("virt-visualizer");
  if (!container) return;

  container.innerHTML = "";

  data.history.forEach((h, i) => {
    const card = document.createElement("div");
    card.className = "virt-step-card";

    const head = document.createElement("div");
    head.className = "virt-step-head";
    head.innerHTML = `<span>STEP ${i + 1}</span><span class="virt-step-page">PAGE ${h.page}</span>`;

    const frameRow = document.createElement("div");
    frameRow.className = "virt-frame-row";

    for (let f = 0; f < data.frame_count; f++) {
      const box = document.createElement("div");
      const value = h.frames[f];
      box.className = `virt-frame-box${value === undefined ? " empty" : ""}`;
      box.textContent = value === undefined ? "—" : value;
      frameRow.appendChild(box);
    }

    const status = document.createElement("div");
    status.className = `virt-status ${h.status.toLowerCase()}`;
    status.textContent = h.status;

    card.appendChild(head);
    card.appendChild(frameRow);
    card.appendChild(status);
    container.appendChild(card);
  });
}