"""
Context Builder: raw activity -> synthesized user understanding.
"""
import json
import time
from pydantic import BaseModel, Field
from .config import groq_client, MODEL_FAST


class UserContext(BaseModel):
    skills: list[str] = Field(description="3-6 concrete technical skills inferred from their work")
    strengths: str = Field(description="1-2 sentences on what this person is genuinely good at, inferred not stated")
    project_summary: str = Field(description="1-2 sentence synthesis of their body of work, not a list")
    collaboration_style: str = Field(description="solo builder / team leader / team contributor — inferred from available signals")
    standout_trait: str = Field(description="The single most notable thing about this person, in one sentence")
    experience_level: str = Field(description="beginner / intermediate / advanced — inferred from available signals")


SYSTEM_PROMPT = (
    "You build rich user context profiles for a hackathon platform's organizer tool. "
    "Given a user's raw data (LinkedIn, GitHub, job title/college, submissions if any), "
    "synthesize an honest, specific understanding of who they are as a builder. "
    "Do NOT just restate the raw data — interpret it. "
    "Respond with ONLY valid JSON matching this schema, no other text:\n{schema}"
)


def build_context(user_raw: dict) -> dict:
    schema = UserContext.model_json_schema()
    completion = groq_client.chat.completions.create(
        model=MODEL_FAST,
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(schema=json.dumps(schema))},
            {"role": "user", "content": f"User raw data:\n{json.dumps(user_raw, indent=2)}"},
        ],
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content
    parsed = UserContext.model_validate_json(raw)
    result = parsed.model_dump()
    result["user_id"] = user_raw["user_id"]
    result["name"] = user_raw["name"]
    return result


def build_all_contexts(users: list[dict]) -> list[dict]:
    """Build contexts for every user. Never crashes the whole batch on one failure."""
    contexts = []
    for i, u in enumerate(users):
        try:
            contexts.append(build_context(u))
        except Exception as e:
            contexts.append({
                "user_id": u.get("user_id", f"u{i}"),
                "name": u.get("name", "Unknown"),
                "skills": [],
                "strengths": "Profile generation temporarily unavailable.",
                "project_summary": "",
                "collaboration_style": "unknown",
                "standout_trait": "",
                "experience_level": "unknown",
            })
        if i < len(users) - 1:
            time.sleep(2)
    return contexts


if __name__ == "__main__":
    with open("data/real_users.json") as f:
        data = json.load(f)
    ctx = build_context(data["users"][0])
    print(json.dumps(ctx, indent=2))