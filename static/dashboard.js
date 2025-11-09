// static/dashboard.js
async function getJSON(url) {
  const res = await fetch(url, { credentials: "same-origin" });
  return res.json();
}

async function loadPrompt() {
  const r = await getJSON("/dashboard/api/prompt");
  if (r.prompt !== undefined) {
    document.getElementById("prompt-text").value = r.prompt;
  } else {
    document.getElementById("prompt-text").value = "";
  }
}

async function savePrompt() {
  const text = document.getElementById("prompt-text").value;
  const res = await fetch("/dashboard/api/prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: text }),
    credentials: "same-origin"
  });
  const j = await res.json();
  if (j.ok) {
    document.getElementById("save-msg").textContent = "Saved!";
    setTimeout(()=> document.getElementById("save-msg").textContent = "", 2000);
  } else {
    document.getElementById("save-msg").textContent = "Save failed";
  }
}

async function applyPreset(name) {
  const res = await fetch(`/dashboard/api/preset/${name}`, { method: "POST", credentials: "same-origin" });
  const j = await res.json();
  if (j.ok) {
    document.getElementById("prompt-text").value = j.prompt;
    document.getElementById("save-msg").textContent = "Preset applied";
    setTimeout(()=> document.getElementById("save-msg").textContent = "", 2000);
  } else {
    document.getElementById("save-msg").textContent = "Preset failed";
  }
}

async function loadLogs() {
  const lines = document.getElementById("log-lines").value || 200;
  const r = await getJSON(`/dashboard/api/logs?lines=${lines}`);
  if (r.logs !== undefined) {
    document.getElementById("logs-pre").textContent = r.logs;
  } else {
    document.getElementById("logs-pre").textContent = "No logs found";
  }
}

document.getElementById("save-btn").addEventListener("click", savePrompt);
document.getElementById("reload-btn").addEventListener("click", loadPrompt);
document.getElementById("refresh-logs").addEventListener("click", loadLogs);

document.querySelectorAll(".btn-preset").forEach(btn=>{
  btn.addEventListener("click", ()=> applyPreset(btn.dataset.preset));
});

// initial load
loadPrompt();
loadLogs();
