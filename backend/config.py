"""
Shared config: loads API keys, creates clients, defines model IDs.

IMPORTANT: Groq retires models fairly often. If you get a `model_not_found`
error on hackathon day, check https://console.groq.com/docs/deprecations
and swap the ID below — everything else keeps working unchanged.
"""
import os
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing — copy .env.example to .env and fill it in")
if not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY missing — copy .env.example to .env and fill it in")

groq_client = Groq(api_key=GROQ_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Current (Sep 2026) Groq model IDs. llama-3.1-8b-instant / llama-3.3-70b-versatile
# are retired for free/dev tier — do NOT use them.
MODEL_FAST = "openai/gpt-oss-20b"      # cheapest + fastest, good default
MODEL_STRONG = "openai/gpt-oss-120b"   # more reasoning power, slightly slower
MODEL_ALT = "openai/gpt-oss-20b"       # a third, differently-trained model — good for variety in brainstorming
