import os, json, logging
from typing import TypedDict, List, Dict, Any
from flask import Flask, request, jsonify, send_from_directory
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.graph import StateGraph, END
from backend.config import tavily_client, groq_client, MODEL_STRONG
from backend.idea_generator import brainstorm
from backend.agent import SimpleEmbeddings, AgentState, GroundedAnswer
from backend.context_builder import build_all_contexts
from backend.context_store import save_all_contexts, get_all_contexts
from backend.context_agent import ask_about_users
from backend.matchmaker import match_users_to_opportunity

load_dotenv()
logger = logging.getLogger("app")

def search_web(state: AgentState) -> Dict[str, Any]:
    try: return {"raw_results": tavily_client.search(query=state["query"], max_results=5).get("results", [])}
    except: return {"raw_results": []}

def index_and_retrieve(state: AgentState) -> Dict[str, Any]:
    raw = state.get("raw_results", [])
    if not raw: return {"retrieved_snippets": []}
    docs = [Document(page_content=r.get("content", ""), metadata={"source": r.get("url", "")}) for r in raw]
    splits = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=120).split_documents(docs)
    gkey = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=gkey) if gkey else SimpleEmbeddings()
    try:
        db = Chroma.from_documents(documents=splits, embedding=embeddings)
        retrieved = db.as_retriever(search_kwargs={"k": 4}).invoke(state["query"])
        return {"retrieved_snippets": [f"Source [{d.metadata.get('source')}]: {d.page_content}" for d in retrieved]}
    except:
        return {"retrieved_snippets": [f"Source [{r.get('url')}]: {r.get('content', '')[:600]}" for r in raw[:3]]}

def generate_answer(state: AgentState) -> Dict[str, Any]:
    snippets = state.get("retrieved_snippets", [])
    if not snippets: return {"answer": "No snippets.", "key_points": [], "sources": [], "confidence": "low"}
    context, schema = "\n\n".join(snippets), GroundedAnswer.model_json_schema()
    sys_prompt = f"You are VeriFact AI. Answer precisely grounded in snippets. Return ONLY JSON matching schema:\n{json.dumps(schema)}"
    gkey = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gkey:
        try:
            os.environ["GOOGLE_API_KEY"] = gkey
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2, google_api_key=gkey)
            raw = llm.invoke([("system", sys_prompt), ("user", f"Q: {state['query']}\nSnippets:\n{context}")]).content.strip()
            if raw.startswith("```"): raw = "\n".join(raw.split("\n")[1:-1]).strip() if raw.endswith("```") else raw.strip("`").replace("json", "").strip()
            return GroundedAnswer.model_validate_json(raw).model_dump()
        except Exception as e:
            logger.error(f"Gemini failed: {e}")
    try:
        comp = groq_client.chat.completions.create(
            model=MODEL_STRONG, temperature=0.2, response_format={"type": "json_object"},
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": f"Q: {state['query']}\nSnippets:\n{context}"}]
        )
        return GroundedAnswer.model_validate_json(comp.choices[0].message.content).model_dump()
    except Exception as e:
        return {"answer": f"LLM error. {state['query']}", "key_points": [s[:100] for s in snippets[:3]], "sources": list(set(s.split("Source [")[1].split("]:")[0] for s in snippets if "Source [" in s)), "confidence": "low"}

workflow = StateGraph(AgentState)
workflow.add_node("search_web", search_web)
workflow.add_node("index_and_retrieve", index_and_retrieve)
workflow.add_node("generate_answer", generate_answer)
workflow.set_entry_point("search_web")
workflow.add_edge("search_web", "index_and_retrieve")
workflow.add_edge("index_and_retrieve", "generate_answer")
workflow.add_edge("generate_answer", END)
agent_app = workflow.compile()

app = Flask(__name__, static_folder="static", static_url_path="")

@app.route("/")
def home(): return send_from_directory("static", "index.html")

@app.route("/api/brainstorm", methods=["POST"])
def api_brainstorm():
    data = request.get_json(force=True)
    pb = (data.get("problem_statement") or "").strip()
    if not pb: return jsonify({"error": "Required"}), 400
    try: return jsonify({"ideas": brainstorm(pb)})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/research", methods=["POST"])
def api_research():
    data = request.get_json(force=True)
    q = (data.get("query") or "").strip()
    if not q: return jsonify({"error": "Required"}), 400
    try:
        res = agent_app.invoke({"query": q, "raw_results": [], "retrieved_snippets": [], "answer": "", "key_points": [], "sources": [], "confidence": ""})
        return jsonify({"answer": res.get("answer", ""), "key_points": res.get("key_points", []), "sources": res.get("sources", []), "confidence": res.get("confidence", "medium")})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/build-contexts", methods=["POST"])
def api_build_contexts():
    with open("data/real_users.json") as f:
        data = json.load(f)
    contexts = build_all_contexts(data["users"])
    save_all_contexts(contexts)
    return jsonify({"built": len(contexts), "contexts": contexts})

@app.route("/api/ask-context", methods=["POST"])
def api_ask_context():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    if not question: return jsonify({"error": "question is required"}), 400
    try:
        return jsonify({"answer": ask_about_users(question)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/raw-users", methods=["GET"])
def api_raw_users():
    with open("data/real_users.json") as f:
        return jsonify(json.load(f))

@app.route("/api/match", methods=["POST"])
def api_match():
    data = request.get_json(force=True)
    opp = (data.get("opportunity") or "").strip()
    if not opp: return jsonify({"error": "opportunity required"}), 400
    try:
        return jsonify({"result": match_users_to_opportunity(opp)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)