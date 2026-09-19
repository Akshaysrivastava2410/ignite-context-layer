// Tab switching
document.querySelectorAll(".rail-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".rail-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`panel-${btn.dataset.panel}`).classList.add("active");
  });
});

// Brainstorm
const brainstormForm = document.getElementById("brainstorm-form");
const brainstormBtn = document.getElementById("brainstorm-btn");
const brainstormStatus = document.getElementById("brainstorm-status");
const brainstormResults = document.getElementById("brainstorm-results");

brainstormForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const problem_statement = document.getElementById("problem-input").value.trim();
  if (!problem_statement) return;

  brainstormBtn.disabled = true;
  brainstormBtn.textContent = "Thinking...";
  brainstormStatus.textContent = "Querying 3 models in parallel...";
  brainstormResults.innerHTML = "";

  try {
    const res = await fetch("/api/brainstorm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem_statement }),
    });
    const data = await res.json();

    if (data.error) {
      brainstormStatus.textContent = `Error: ${data.error}`;
    } else {
      brainstormStatus.textContent = `${data.ideas.length} approaches back.`;
      data.ideas.forEach(idea => brainstormResults.appendChild(renderIdeaCard(idea)));
    }
  } catch (err) {
    brainstormStatus.textContent = `Request failed: ${err}`;
  } finally {
    brainstormBtn.disabled = false;
    brainstormBtn.textContent = "Generate approaches";
  }
});

function renderIdeaCard(idea) {
  const card = document.createElement("div");
  card.className = "idea-card";

  const stackChips = (idea.tech_stack || [])
    .map(t => `<span class="chip">${escapeHtml(t)}</span>`)
    .join("");

  const score = idea.feasibility_score || 0;

  card.innerHTML = `
    <div class="model-label">${escapeHtml(idea.model_label || "")}</div>
    <h3>${escapeHtml(idea.project_title || "Untitled")}</h3>
    <div class="one-liner">${escapeHtml(idea.one_liner || "")}</div>
    <div class="stack">${stackChips}</div>
    <div class="feature"><b>Key feature:</b> ${escapeHtml(idea.key_feature || "")}</div>
    <div class="feasibility-bar"><div class="feasibility-fill" style="width:${score * 10}%"></div></div>
    <div class="feasibility-label">feasibility ${score}/10</div>
  `;
  return card;
}

// Research
const researchForm = document.getElementById("research-form");
const researchBtn = document.getElementById("research-btn");
const researchStatus = document.getElementById("research-status");
const researchResult = document.getElementById("research-result");

researchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = document.getElementById("research-input").value.trim();
  if (!query) return;

  researchBtn.disabled = true;
  researchBtn.textContent = "Searching...";
  researchStatus.textContent = "Tavily searching + Groq synthesizing...";
  researchResult.hidden = true;

  try {
    const res = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();

    if (data.error) {
      researchStatus.textContent = `Error: ${data.error}`;
      return;
    }

    researchStatus.textContent = `Confidence: ${data.confidence || "n/a"}`;
    document.getElementById("research-answer").textContent = data.answer || "";

    const pointsEl = document.getElementById("research-points");
    pointsEl.innerHTML = (data.key_points || []).map(p => `<li>${escapeHtml(p)}</li>`).join("");

    const sourcesEl = document.getElementById("research-sources");
    sourcesEl.innerHTML = (data.sources || [])
      .map(s => `<a href="${escapeHtml(s)}" target="_blank" rel="noopener">${escapeHtml(s)}</a>`)
      .join("");

    researchResult.hidden = false;
  } catch (err) {
    researchStatus.textContent = `Request failed: ${err}`;
  } finally {
    researchBtn.disabled = false;
    researchBtn.textContent = "Search + answer";
  }
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
