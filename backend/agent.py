"""
VeriFact AI: A LangGraph-powered web-grounded research agent.
Flow:
  1. search_web: Tavily searches live sources.
  2. index_and_retrieve: Documents are split, indexed in an in-memory Chroma vector database (RAG),
     and relevant snippets are retrieved.
  3. generate_answer: Google Gemini (gemini-1.5-pro) synthesizes and structures a verified response.
"""

import os
import json
import logging
from typing import TypedDict, List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.embeddings import Embeddings

from langgraph.graph import StateGraph, END

from .config import tavily_client, groq_client, MODEL_STRONG

load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Fallback Simple Embeddings ---
class SimpleEmbeddings(Embeddings):
    """
    A lightweight, deterministic fallback embedding generator using numpy and hashing.
    Prevents crashes if GOOGLE_API_KEY is not defined or active.
    """
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import numpy as np
        vectors = []
        for text in texts:
            # Deterministic hash seed
            np.random.seed(abs(hash(text)) % (2**32))
            v = np.random.randn(128).tolist()
            vectors.append(v)
        return vectors

    def embed_query(self, text: str) -> List[float]:
        import numpy as np
        np.random.seed(abs(hash(text)) % (2**32))
        return np.random.randn(128).tolist()

# --- LangGraph Agent State Definition ---
class AgentState(TypedDict):
    query: str
    raw_results: List[Dict[str, Any]]
    retrieved_snippets: List[str]
    answer: str
    key_points: List[str]
    sources: List[str]
    confidence: str

# --- Pydantic Output Schema ---
class GroundedAnswer(BaseModel):
    answer: str = Field(description="Direct, verified, concise answer to the user's question, grounded in retrieved snippets.")
    key_points: list[str] = Field(description="3-5 bullet points backing up the answer with facts and sources.")
    sources: list[str] = Field(description="The source URLs of the websites cited to back up this answer.")
    confidence: str = Field(description="One of: high, medium, low")


# --- LangGraph Nodes ---

def search_web(state: AgentState) -> Dict[str, Any]:
    """Search the web using Tavily API."""
    query = state["query"]
    logger.info(f"Node [search_web]: Searching Tavily for query: '{query}'")
    
    try:
        search_results = tavily_client.search(
            query=query,
            max_results=5,
            include_answer=False,
        )
        results = search_results.get("results", [])
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        results = []
        
    return {"raw_results": results}


def index_and_retrieve(state: AgentState) -> Dict[str, Any]:
    """Index fetched pages into a local in-memory Chroma db and retrieve relevant snippets (RAG)."""
    raw_results = state.get("raw_results", [])
    query = state["query"]
    logger.info(f"Node [index_and_retrieve]: Indexing {len(raw_results)} results into Chroma.")
    
    if not raw_results:
        return {"retrieved_snippets": []}
        
    documents = []
    for r in raw_results:
        content = r.get("content", "")
        url = r.get("url", "")
        title = r.get("title", "No Title")
        doc = Document(page_content=content, metadata={"source": url, "title": title})
        documents.append(doc)
        
    # Chunk text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=120)
    split_docs = text_splitter.split_documents(documents)
    
    # Check if Google API Key is available for Embeddings
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if google_api_key:
        logger.info("Using GoogleGenerativeAIEmbeddings (models/embedding-001)")
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
    else:
        logger.warning("GOOGLE_API_KEY missing. Falling back to SimpleEmbeddings.")
        embeddings = SimpleEmbeddings()
        
    # Store documents in Chroma vector db (in-memory)
    try:
        vector_store = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings
        )
        # Query top 4 most relevant fragments
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})
        retrieved_docs = retriever.invoke(query)
    except Exception as e:
        logger.error(f"Chroma store/retrieval failed: {e}")
        # Fallback to simple snippet collection
        retrieved_snippets = [f"Source [{r.get('url')}]: {r.get('content', '')[:600]}" for r in raw_results[:3]]
        return {"retrieved_snippets": retrieved_snippets}
        
    retrieved_snippets = []
    for doc in retrieved_docs:
        source = doc.metadata.get("source", "Unknown")
        retrieved_snippets.append(f"Source [{source}]: {doc.page_content}")
        
    return {"retrieved_snippets": retrieved_snippets}


def generate_answer(state: AgentState) -> Dict[str, Any]:
    """Generate verified structured answer using Google Gemini (gemini-1.5-pro)."""
    query = state["query"]
    retrieved_snippets = state.get("retrieved_snippets", [])
    logger.info("Node [generate_answer]: Synthesizing response with LLM.")
    
    if not retrieved_snippets:
        return {
            "answer": "No information retrieved from the web search.",
            "key_points": [],
            "sources": [],
            "confidence": "low",
        }
        
    context_text = "\n\n".join(retrieved_snippets)
    schema = GroundedAnswer.model_json_schema()
    
    system_prompt = (
        "You are VeriFact AI, an elite real-time fact checker and research agent. "
        "Your task is to answer the user's question with absolute precision, grounded ONLY in the retrieved snippets provided. "
        "Ensure all factual claims are backed by the retrieved snippets. "
        "Return ONLY a valid JSON object matching this schema. Do not enclose the output in markdown block format (like ```json ... ```) or include any extra text. Just print the JSON object:\n"
        f"{json.dumps(schema)}"
    )
    
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    # Try using Google Gemini first (gemini-1.5-pro or latest)
    if google_api_key:
        try:
            logger.info("Calling Google Gemini (gemini-1.5-pro)")
            # Set environment variable as expected by ChatGoogleGenerativeAI
            os.environ["GOOGLE_API_KEY"] = google_api_key
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                temperature=0.2,
                google_api_key=google_api_key
            )
            messages = [
                ("system", system_prompt),
                ("user", f"Question: {query}\n\nRetrieved Snippets:\n{context_text}")
            ]
            response = llm.invoke(messages)
            raw = response.content.strip()
            
            # Clean up if Gemini wrapped it in markdown code block
            if raw.startswith("```"):
                lines = raw.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                raw = "\n".join(lines).strip()
                
            parsed = GroundedAnswer.model_validate_json(raw)
            return parsed.model_dump()
            
        except Exception as e:
            logger.error(f"Google Gemini call failed or returned invalid JSON: {e}. Falling back to Groq.")
            
    # Fallback to Groq if Google API Key is absent or fails
    try:
        logger.info("Calling Groq as fallback")
        completion = groq_client.chat.completions.create(
            model=MODEL_STRONG,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {query}\n\nRetrieved Snippets:\n{context_text}"},
            ],
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content
        parsed = GroundedAnswer.model_validate_json(raw)
        return parsed.model_dump()
    except Exception as e:
        logger.error(f"Groq fallback also failed: {e}")
        # Final emergency fallback: return raw search results structured nicely
        unique_urls = list(set(
            line.split("Source [")[1].split("]:")[0] 
            for line in retrieved_snippets 
            if "Source [" in line and "]:" in line
        ))
        return {
            "answer": f"Unable to reach LLM engines. Question was: {query}",
            "key_points": [snippet[:100] + "..." for snippet in retrieved_snippets[:3]],
            "sources": unique_urls,
            "confidence": "low",
        }


# --- LangGraph Workflow Setup ---

def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("search_web", search_web)
    workflow.add_node("index_and_retrieve", index_and_retrieve)
    workflow.add_node("generate_answer", generate_answer)
    
    # Define Flow/Edges
    workflow.set_entry_point("search_web")
    workflow.add_edge("search_web", "index_and_retrieve")
    workflow.add_edge("index_and_retrieve", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    return workflow.compile()


# Compile the LangGraph agent
agent_app = build_workflow()


# --- Main Research Function ---

def research(query: str, max_results: int = 5) -> dict:
    """
    Search the web with Tavily, store/retrieve using Chroma RAG,
    and synthesize a verified answer using Google Gemini or fallback.
    """
    logger.info(f"Starting VeriFact AI agent for query: '{query}'")
    try:
        initial_state = {
            "query": query,
            "raw_results": [],
            "retrieved_snippets": [],
            "answer": "",
            "key_points": [],
            "sources": [],
            "confidence": "",
        }
        final_state = agent_app.invoke(initial_state)
        return {
            "answer": final_state.get("answer", ""),
            "key_points": final_state.get("key_points", []),
            "sources": final_state.get("sources", []),
            "confidence": final_state.get("confidence", "medium"),
        }
    except Exception as e:
        logger.error(f"VeriFact AI LangGraph run crashed: {e}")
        return {
            "answer": f"An error occurred while running the VeriFact AI agent: {str(e)}",
            "key_points": [],
            "sources": [],
            "confidence": "low",
        }


if __name__ == "__main__":
    # Test execution: python -m backend.agent
    out = research("What is the current status of the Artemis Space Program?")
    print(json.dumps(out, indent=2))
