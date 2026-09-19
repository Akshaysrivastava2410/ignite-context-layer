"""
Drop in the problem statement on hackathon morning, get back several
different build approaches from different Groq models so you're not
anchored to one idea.

Calls are staggered slightly and retried more, because Groq's free tier
returns 429 (Too Many Requests) when all calls fire at the same instant.
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field
from .config import groq_client, MODEL_FAST, MODEL_STRONG, MODEL_ALT

MODELS = [
    (f"Fast ({MODEL_FAST})", MODEL_FAST),
    (f"Strong ({MODEL_STRONG})", MODEL_STRONG),
    (f"Alt ({MODEL_ALT})", MODEL_ALT),
]

STAGGER_SECONDS = 2  # gap between starting each call


class Approach(BaseModel):
    project_title: str = Field(description="Crisp, catchy technical title")
    one_liner: str = Field(description="One sentence describing what it does")
    tech_stack: list[str] = Field(description="3-6 concrete technologies/APIs to use")
    key_feature: str = Field(description="The single standout/demo-able feature")
    feasibility_score: int = Field(description="1-10, buildable solo in 8 hours")
    why_this_wins: str = Field(description="Why judges would like this, one sentence")


SYSTEM_PROMPT = (
    "You are an expert hackathon strategist helping a SOLO developer pick a winning, "
    "realistically-buildable idea for an 8-hour AI hackathon (Groq + Tavily sponsor tools "
    "available). Given a problem statement, propose ONE strong, specific, buildable approach. "
    "Be concrete and technical, not generic. Respond with ONLY valid JSON matching this schema, "
    "no other text:\n{schema}"
)


def _call_model(label: str, model_id: str, problem_statement: str, delay: float) -> dict:
    time.sleep(delay)  # stagger so we don't hit the rate limit all at once
    schema = Approach.model_json_schema()
    client = groq_client.with_options(max_retries=6)  # retry 429s more patiently
    completion = client.chat.completions.create(
        model=model_id,
        temperature=0.7,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(schema=json.dumps(schema))},
            {"role": "user", "content": f"Problem statement: {problem_statement}"},
        ],
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content
    parsed = Approach.model_validate_json(raw)
    result = parsed.model_dump()
    result["model_label"] = label
    return result


def brainstorm(problem_statement: str) -> list[dict]:
    """Fire the models with a small stagger, return whichever come back."""
    ideas = []
    with ThreadPoolExecutor(max_workers=len(MODELS)) as executor:
        futures = {
            executor.submit(_call_model, label, model_id, problem_statement, i * STAGGER_SECONDS): label
            for i, (label, model_id) in enumerate(MODELS)
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                ideas.append(future.result())
            except Exception as e:
                ideas.append({
                    "model_label": label,
                    "project_title": "Error",
                    "one_liner": f"This model failed: {e}",
                    "tech_stack": [],
                    "key_feature": "",
                    "feasibility_score": 0,
                    "why_this_wins": "",
                })
    return ideas


if __name__ == "__main__":
    # Quick manual test: python -m backend.idea_generator
    result = brainstorm("Build an AI feature that helps small businesses on Paytm manage cashflow")
    print(json.dumps(result, indent=2))