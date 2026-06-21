/* ─────────────────────────────────────────────
   disk.js  —  Disk Management Frontend Logic
   Handles: algo selection, config, API call, results render
───────────────────────────────────────────── */

// ── STATE ──
let diskAlgo = null;

// ── ELEMENTS ──
const diskAlgoBtns    = document.querySelectorAll(".disk-algo-btn");
const diskRunBtn      = document.getElementById("disk-run-btn");
const diskResetBtn    = document.getElementById("disk-reset-btn");
const diskStepConfig  = document.getElementById("disk-step-config");
const diskStepResults = document.getElementById("disk-step-results");

// ── ALGO SELECTION ──
diskAlgoBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    diskAlgoBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    diskAlgo = btn.dataset.algo;
    diskStepConfig.classList.remove("hidden");
  });
});

// ── RUN ──
diskRunBtn.addEventListener("click", async () => {
  if (!diskAlgo) return;

  // Grab user inputs, provide fallbacks if empty or invalid
  let initialHead = parseInt(document.getElementById("disk-initial-head").value);
  if (isNaN(initialHead) || initialHead < 0) { 
    initialHead = 50; 
    document.getElementById("disk-initial-head").value = 50; 
  }

  const reqInput = document.getElementById("disk-track-requests").value;
  let requestsArray = reqInput.split(",").map(s => parseInt(s.trim())).filter(n => !isNaN(n));
  
  if (requestsArray.length === 0) {
    requestsArray = [82, 170, 43, 140, 24, 16, 190];
    document.getElementById("disk-track-requests").value = "82, 170, 43, 140, 24, 16, 190";
  }

  const payload = { algorithm: diskAlgo, initial_head: initialHead, requests: requestsArray };

  diskRunBtn.textContent = "RUNNING...";
  diskRunBtn.disabled    = true;

  try {
    const res  = await fetch("/api/disk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.error) { alert("Error: " + data.error); return; }

    renderDiskResults(data);
    diskStepResults.classList.remove("hidden");
    diskStepResults.scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    alert("Failed to connect to the server. Make sure Flask is running.");
    console.error(err);
  } finally {
    diskRunBtn.innerHTML = `<span>RUN SIMULATION</span><span class="run-arrow">→</span>`;
    diskRunBtn.disabled  = false;
  }
});

// ── RESET ──
diskResetBtn.addEventListener("click", () => {
  diskAlgo = null;
  diskAlgoBtns.forEach(b => b.classList.remove("active"));
  diskStepConfig.classList.add("hidden");
  diskStepResults.classList.add("hidden");
  document.getElementById("disk-initial-head").value = 50;
  document.getElementById("disk-track-requests").value = "82, 170, 43, 140, 24, 16, 190";
  window.scrollTo({ top: 0, behavior: "smooth" });
});

// ── RENDER ──
function renderDiskResults(data) {
  // ── Execution Sequence display ──
  const seqWrap = document.getElementById("disk-sequence");
  seqWrap.innerHTML = data.sequence.map((p, i) =>
    `<span class="ref-page">${p}</span>${i < data.sequence.length - 1 ? '<span style="color:var(--text-dim); margin: 0 4px;">→</span>' : ''}`
  ).join("");

  // ── History table ──
  const dt = document.getElementById("disk-history-table");
  dt.querySelector("thead").innerHTML = `<tr><th>Step</th><th>From</th><th>To</th><th>Distance</th></tr>`;
  dt.querySelector("tbody").innerHTML = data.history.map((h, i) => {
    return `<tr>
      <td class="pid-cell">${i + 1}</td>
      <td style="font-family:var(--mono);">${h.from}</td>
      <td style="font-family:var(--mono);color:var(--accent);font-weight:700;">${h.to}</td>
      <td style="font-family:var(--mono);">${h.distance}</td>
    </tr>`;
  }).join("");

  // ── Stats ──
  document.getElementById("disk-total-movement").textContent = data.total_movement + " Cylinders";
}