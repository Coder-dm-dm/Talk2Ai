async function getJSON(url) {
  const res = await fetch(url, { credentials: "same-origin" });
  return res.json();
}

async function loadPrompt() {
  const r = await getJSON("/dashboard/api/prompt");
  document.getElementById("prompt-text").value = r.prompt || "";
}

async function savePrompt() {
  const text = document.getElementById("prompt-text").value;
  const res = await fetch("/dashboard/api/prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: text }),
  });
  const j = await res.json();
  const msg = document.getElementById("save-msg");
  msg.textContent = j.ok ? "✅ Saved!" : "❌ Save failed";
  setTimeout(() => (msg.textContent = ""), 2500);
}

async function applyPreset(name) {
  const res = await fetch(`/dashboard/api/preset/${name}`, { method: "POST" });
  const j = await res.json();
  const msg = document.getElementById("save-msg");
  if (j.ok) {
    document.getElementById("prompt-text").value = j.prompt;
    msg.textContent = "Preset applied";
  } else msg.textContent = "Preset failed";
  setTimeout(() => (msg.textContent = ""), 2000);
}

async function loadLogs() {
  const lines = document.getElementById("log-lines").value || 200;
  const r = await getJSON(`/dashboard/api/logs?lines=${lines}`);
  document.getElementById("logs-pre").textContent = r.logs || "No logs found";
}

// --- Real-time log streaming ---
function streamLogs() {
  const pre = document.getElementById("logs-pre");
  const es = new EventSource("/dashboard/api/stream");
  es.onmessage = (e) => {
    pre.textContent += "\n" + e.data;
    pre.scrollTop = pre.scrollHeight;
  };
  es.onerror = () => {
    console.warn("Log stream disconnected, retrying...");
    setTimeout(streamLogs, 3000);
  };
}

// Event bindings
document.getElementById("save-btn").addEventListener("click", savePrompt);
document.getElementById("reload-btn").addEventListener("click", loadPrompt);
document.getElementById("refresh-logs").addEventListener("click", loadLogs);
document.querySelectorAll(".btn-preset").forEach((btn) =>
  btn.addEventListener("click", () => applyPreset(btn.dataset.preset))
);

// Initial load
loadPrompt();
loadLogs();
streamLogs();
