# Ignite Cockpit — hackathon boilerplate

Groq + Tavily agent, pre-wired, with a working UI. Two tools in one app:

1. **Brainstorm** — paste the problem statement the moment you get it on hackathon morning.
   Fires 3 different Groq models in parallel and returns structured, buildable approaches
   (title, tech stack, key feature, feasibility score) in a few seconds — not one at a time.
2. **Live Research agent** — Tavily searches the web, Groq turns the results into a
   structured, grounded answer. This is your actual Day-2-mission agent, reusable for
   whatever the final problem statement needs.

## Setup (do this today, not on the 19th)

```bash
python -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your real GROQ_API_KEY and TAVILY_API_KEY
```

Get keys:
- Groq: https://console.groq.com/keys
- Tavily: https://app.tavily.com

## Run

```bash
python app.py
```

Open http://127.0.0.1:5000

## Quick CLI sanity checks (no UI needed)

```bash
python -m backend.agent            # tests the Tavily+Groq research agent
python -m backend.idea_generator   # tests the parallel brainstorm
```

If either of these prints JSON with real content, your keys and stack are working end to end.

## On hackathon day

1. Get the problem statement → paste into the **Brainstorm** tab → pick the approach
   with the best feasibility score that you can actually finish solo in ~7 hours.
2. Reuse `backend/agent.py`'s `research()` function directly inside your actual project
   if it needs live/current data — don't rebuild it from scratch.
3. If Groq gives a `model_not_found` error, a model got deprecated — check
   https://console.groq.com/docs/deprecations and swap the ID in `backend/config.py`.
   Everything else keeps working unchanged.

## Files

```
app.py                     Flask server + routes
backend/config.py          API keys, clients, model IDs (edit models here if deprecated)
backend/agent.py           Tavily search -> Groq structured answer
backend/idea_generator.py  Parallel multi-model brainstorming
static/                    UI (plain HTML/CSS/JS, no build step)
```


## Use Case Justification Use case: Hackathon listing platform. Context sources: platform-native (submissions, hackathons attended, teams led) + external GitHub signal, because for a dev-focused platform, code activity is the strongest external signal of skill — unlike a food-delivery app where only in-platform behavior matters.

## What we built
- Context builder: synthesizes 15 real hackathon participants' profiles from LinkedIn/GitHub/college data
- Conversational agent: answers open-ended questions including existence checks ("Is X in our database?")
- Bonus: matchmaking algorithm ranks best-fit users for a given opportunity

## Live demo
https://ignite-context-layer.onrender.com