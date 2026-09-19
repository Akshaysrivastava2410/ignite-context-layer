"""
Context Builder: raw activity -> synthesized user understanding.
"""
import json
from pydantic import BaseModel, Field
from .config import groq_client, MODEL_STRONG


class UserContext(BaseModel):
    skills: list[str] = Field(description="3-6 concrete technical skills inferred from their work")
    strengths: str = Field(description="1-2 sentences on what this person is genuinely good at, inferred not stated")
    project_summary: str = Field(description="1-2 sentence synthesis of their body of work, not a list")
    collaboration_style: str = Field(description="solo builder / team leader / team contributor — inferred from teams_led and submission patterns")
    standout_trait: str = Field(description="The single most notable thing about this person, in one sentence")
    experience_level: str = Field(description="beginner / intermediate / advanced — inferred from submission complexity and hackathon count")


SYSTEM_PROMPT = (
    "You build rich user context profiles for a hackathon platform's organizer tool. "
    "Given a user's raw activity data (bio, past submissions, hackathon history), "
    "synthesize an honest, specific understanding of who they are as a builder. "
    "Do NOT just restate the raw data — interpret it. E.g. if someone led 3 teams "
    "and always does backend, say they're a natural backend lead, don't just list 'backend'. "
    "Respond with ONLY valid JSON matching this schema, no other text:\n{schema}"
)


def build_context(user_raw: dict) -> dict:
    schema = UserContext.model_json_schema()
    completion = groq_client.chat.completions.create(
        model=MODEL_STRONG,
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
    return [build_context(u) for u in users]


if __name__ == "__main__":
    with open("data/mock_users.json") as f:
        data = json.load(f)
    ctx = build_context(data["users"][3])
    print(json.dumps(ctx, indent=2))