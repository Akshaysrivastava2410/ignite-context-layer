from .config import groq_client, MODEL_STRONG
from .context_store import get_all_contexts
import json

def match_users_to_opportunity(opportunity_description: str, top_n: int = 3) -> str:
    contexts = get_all_contexts()
    prompt = (
        f"Given this opportunity: {opportunity_description}\n\n"
        f"And these user contexts: {json.dumps(contexts, indent=2)}\n\n"
        f"Rank the top {top_n} best-fit users with a one-line reason each."
    )
    completion = groq_client.chat.completions.create(
        model=MODEL_STRONG, temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content