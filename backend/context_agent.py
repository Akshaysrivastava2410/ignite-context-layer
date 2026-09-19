"""
Conversational agent: open-ended question -> synthesized answer.
"""
from .config import groq_client, MODEL_STRONG
from .context_store import get_all_contexts
import json


SYSTEM_PROMPT = (
    "You are a context agent for a hackathon organizer platform. You have access to "
    "SYNTHESIZED profiles of every user (not raw database rows). An organizer will ask "
    "an open-ended question about their user base, INCLUDING existence checks like "
    "'is X in our database'. If asked about existence, explicitly say YES/NO first, "
    "then give the synthesized profile if found. Answer the way a sharp, honest "
    "talent scout would — synthesize across users, don't just list matching fields. "
    "If no user fits well, say so honestly rather than forcing a match."
)


def ask_about_users(question: str) -> str:
    contexts = get_all_contexts()
    if not contexts:
        return "No user contexts have been built yet. Run the context builder first."

    context_block = json.dumps(contexts, indent=2)

    try:
        completion = groq_client.chat.completions.create(
            model=MODEL_STRONG,
            temperature=0.4,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"User contexts:\n{context_block}\n\nOrganizer question: {question}"},
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        return "The agent is temporarily busy (rate limit) — please try again in a few seconds."


if __name__ == "__main__":
    print(ask_about_users("Who would be a good backend lead for a fintech project?"))