document.getElementById("build-contexts-btn").addEventListener("click", async () => {
  const btn = document.getElementById("build-contexts-btn");
  const status = document.getElementById("build-status");
  btn.disabled = true; btn.textContent = "Building...";
  status.textContent = "Synthesizing profiles for all users...";
  try {
    const res = await fetch("/api/build-contexts", { method: "POST" });
    const data = await res.json();
    status.textContent = data.error ? `Error: ${data.error}` : `Built ${data.built} contexts.`;
  } catch (err) {
    status.textContent = `Failed: ${err}`;
  } finally {
    btn.disabled = false; btn.textContent = "Build All Contexts";
  }
});

document.getElementById("ask-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = document.getElementById("ask-input").value.trim();
  if (!question) return;
  const btn = document.getElementById("ask-btn");
  const resultBox = document.getElementById("ask-result");
  btn.disabled = true; btn.textContent = "Asking...";
  try {
    const res = await fetch("/api/ask-context", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    document.getElementById("ask-answer").textContent = data.answer || data.error || "";
    resultBox.hidden = false;
  } catch (err) {
    document.getElementById("ask-answer").textContent = `Failed: ${err}`;
    resultBox.hidden = false;
  } finally {
    btn.disabled = false; btn.textContent = "Ask";
  }
});

document.getElementById("match-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const opportunity = document.getElementById("match-input").value.trim();
  if (!opportunity) return;
  const btn = document.getElementById("match-btn");
  const resultBox = document.getElementById("match-result");
  btn.disabled = true; btn.textContent = "Matching...";
  try {
    const res = await fetch("/api/match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ opportunity }),
    });
    const data = await res.json();
    document.getElementById("match-answer").textContent = data.result || data.error || "";
    resultBox.hidden = false;
  } catch (err) {
    document.getElementById("match-answer").textContent = `Failed: ${err}`;
    resultBox.hidden = false;
  } finally {
    btn.disabled = false; btn.textContent = "Match";
  }
});
document.querySelectorAll(".rail-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".rail-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("panel-" + btn.dataset.panel).classList.add("active");
  });
});

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

document.getElementById("brainstorm-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const problem = document.getElementById("problem-input").value.trim();
  if (!problem) return;
  const btn = document.getElementById("brainstorm-btn");
  const status = document.getElementById("brainstorm-status");
  const results = document.getElementById("brainstorm-results");
  btn.disabled = true; btn.textContent = "Thinking...";
  status.textContent = "Models are thinking (can take up to a minute)...";
  results.innerHTML = "";
  try {
    const res = await fetch("/api/brainstorm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem_statement: problem }),
    });
    const data = await res.json();
    if (data.error) { status.textContent = `Error: ${data.error}`; return; }
    status.textContent = "";
    results.innerHTML = (data.ideas || []).map((i) => {
      const score = Math.max(0, Math.min(10, Number(i.feasibility_score) || 0));
      const chips = (i.tech_stack || []).map((t) => `<span class="chip">${esc(t)}</span>`).join("");
      return `
        <div class="idea-card">
          <div class="model-label">${esc(i.model_label)}</div>
          <h3>${esc(i.project_title)}</h3>
          <div class="one-liner">${esc(i.one_liner)}</div>
          <div class="stack">${chips}</div>
          <div class="feature"><b>Key feature:</b> ${esc(i.key_feature)}</div>
          <div class="feature"><b>Why it wins:</b> ${esc(i.why_this_wins)}</div>
          <div class="feasibility-bar"><div class="feasibility-fill" style="width:${score * 10}%"></div></div>
          <div class="feasibility-label">Feasibility ${score}/10</div>
        </div>`;
    }).join("");
  } catch (err) {
    status.textContent = `Failed: ${err}`;
  } finally {
    btn.disabled = false; btn.textContent = "Generate approaches";
  }
});

document.getElementById("research-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = document.getElementById("research-input").value.trim();
  if (!query) return;
  const btn = document.getElementById("research-btn");
  const status = document.getElementById("research-status");
  const box = document.getElementById("research-result");
  btn.disabled = true; btn.textContent = "Searching...";
  status.textContent = "Searching the web and writing the answer...";
  box.hidden = true;
  try {
    const res = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    if (data.error) { status.textContent = `Error: ${data.error}`; return; }
    status.textContent = "";
    document.getElementById("research-answer").textContent = data.answer || "";
    document.getElementById("research-points").innerHTML =
      (data.key_points || []).map((p) => `<li>${esc(p)}</li>`).join("");
    document.getElementById("research-sources").innerHTML =
      (data.sources || [])
        .filter((s) => String(s).startsWith("http"))
        .map((s) => `<a href="${esc(s)}" target="_blank" rel="noopener">${esc(s)}</a>`)
        .join("");
    box.hidden = false;
  } catch (err) {
    status.textContent = `Failed: ${err}`;
  } finally {
    btn.disabled = false; btn.textContent = "Search + answer";
  }
});