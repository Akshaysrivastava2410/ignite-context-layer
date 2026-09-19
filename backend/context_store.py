"""
Dead simple context store — JSON file, no DB setup needed.
"""
import json
import os

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "built_contexts.json")


def save_all_contexts(contexts: list[dict]) -> None:
    with open(STORE_PATH, "w") as f:
        json.dump(contexts, f, indent=2)


def get_all_contexts() -> list[dict]:
    if not os.path.exists(STORE_PATH):
        return []
    with open(STORE_PATH) as f:
        return json.load(f)


def get_context_by_name(name: str):
    contexts = get_all_contexts()
    name_lower = name.lower()
    for c in contexts:
        if name_lower in c.get("name", "").lower():
            return c
    return None