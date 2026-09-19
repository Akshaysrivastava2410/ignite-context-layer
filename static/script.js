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