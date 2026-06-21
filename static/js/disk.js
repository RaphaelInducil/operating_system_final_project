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

    if (data.error) { 
      alert("Error: " + data.error); 
      return; 
    }

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
  dt.querySelector("thead").innerHTML = `<tr><th>Step</th><th>From Track</th><th>To Track</th><th>Distance Moved</th></tr>`;
  dt.querySelector("tbody").innerHTML = data.history.map((h, i) => {
    return `<tr>
      <td class="pid-cell">${i + 1}</td>
      <td style="font-family:var(--mono);">${h.from}</td>
      <td style="font-family:var(--mono);color:var(--accent);font-weight:700;">${h.to}</td>
      <td style="font-family:var(--mono);">${h.distance}</td>
    </tr>`;
  }).join("");

  // ── Stats ──
  document.getElementById("disk-total-movement").textContent = data.total_movement;
  
  // ── TRIGGERS THE CHART ──
  drawDiskChart(data.sequence);
}

// ── CHART DRAWING LOGIC ──
function drawDiskChart(sequence) {
  const canvas = document.getElementById("disk-chart-canvas");
  const ctx = canvas.getContext("2d");
  
  // Clear any previous chart
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // Constants for drawing
  const padding = 40;
  const width = canvas.width - (padding * 2);
  const height = canvas.height - (padding * 2);
  const maxCylinder = 199; // Standard textbook max cylinder
  
  // Draw X-Axis (Cylinders 0 to 199)
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(canvas.width - padding, padding);
  ctx.strokeStyle = "#444"; // Dark gray axis line
  ctx.lineWidth = 2;
  ctx.stroke();
  
  // Draw Axis Labels (0, 50, 100, 150, 199)
  ctx.fillStyle = "#888";
  ctx.font = "12px monospace";
  ctx.textAlign = "center";
  [0, 50, 100, 150, 199].forEach(tick => {
    const x = padding + (tick / maxCylinder) * width;
    ctx.fillText(tick, x, padding - 10);
    // Draw tiny tick marks
    ctx.beginPath();
    ctx.moveTo(x, padding - 5);
    ctx.lineTo(x, padding + 5);
    ctx.stroke();
  });

  // Calculate coordinates for the sequence points
  const stepHeight = height / (sequence.length - 1);
  const points = sequence.map((track, index) => {
    return {
      x: padding + (track / maxCylinder) * width,
      y: padding + (index * stepHeight) // Y goes down as steps increase
    };
  });

  // Draw the connecting lines
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.strokeStyle = "#b3ff00"; // VALONINI green/accent color!
  ctx.lineWidth = 3;
  ctx.lineJoin = "round";
  ctx.stroke();

  // Draw the dots at each track request
  points.forEach((point, i) => {
    ctx.beginPath();
    ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#b3ff00";
    ctx.fill();
    ctx.strokeStyle = "#111"; // Background color border
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Write the track number next to the dot
    ctx.fillStyle = "#fff";
    ctx.font = "bold 11px monospace";
    ctx.textAlign = "left";
    ctx.fillText(sequence[i], point.x + 10, point.y + 4);
  });
}