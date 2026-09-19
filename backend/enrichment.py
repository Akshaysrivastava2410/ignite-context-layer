"""
Optional external enrichment via Tavily — GitHub + LinkedIn signal.
"""
import json
from pydantic import BaseModel, Field
from .config import groq_client, tavily_client, MODEL_FAST


class ExternalSignal(BaseModel):
    external_summary: str = Field(description="1-2 sentence summary of what their GitHub/LinkedIn activity suggests")
    notable_repos: list[str] = Field(description="up to 3 notable repo names found")


def enrich_from_github(github_username: str, name: str = "") -> dict:
    results = tavily_client.search(
        query=f"github.com/{github_username} OR linkedin.com {name} repositories professional background",
        max_results=4,
    )
    result_items = results.get("results", [])
    if not result_items:
        return {"external_summary": "No external data found.", "notable_repos": []}

    context = "\n\n".join(
        f"{r.get('url')}\n{r.get('content', '')[:500]}" for r in result_items
    )

    schema = ExternalSignal.model_json_schema()
    completion = groq_client.chat.completions.create(
        model=MODEL_FAST,
        temperature=0.2,
        messages=[  
            {"role": "system", "content": f"Extract a professional signal from this search data. Respond with ONLY JSON matching: {json.dumps(schema)}"},
            {"role": "user", "content": context},
        ],
        response_format={"type": "json_object"},
    )
    parsed = ExternalSignal.model_validate_json(completion.choices[0].message.content)
    return parsed.model_dump()                                                                                                                                                                                                                                                                                                                      