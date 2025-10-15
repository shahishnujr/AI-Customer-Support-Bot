# backend/app/main.py
import os
import json
import uuid
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from . import faq
from .llm_client import client as openai_client, generate_response, summarize_session

# Load environment
HERE = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(HERE, ".env"))

logger = logging.getLogger("uvicorn.error")
logging.basicConfig(level=logging.INFO)

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", "8"))
TOP_K_FAQ = int(os.getenv("TOP_K_FAQ", "3"))
FAQ_SIM_THRESHOLD = float(os.getenv("FAQ_SIM_THRESHOLD", "0.7"))

app = FastAPI(title="ai-cs-bot backend")

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None
    metadata: Optional[dict] = {}

class CreateSessionResponse(BaseModel):
    id: str
    user_id: Optional[str]
    metadata: Optional[dict]

class MessageRequest(BaseModel):
    session_id: str
    user_message: str

class MessageResponse(BaseModel):
    reply: str
    faqs: Optional[list] = []
    escalation: bool = False
    summary: Optional[str] = None


# High-risk keywords for escalation


@app.on_event("startup")
async def startup():
    if OPENAI_API_KEY:
        try:
            models = openai_client.models.list()
            logger.info(f"✅ OpenAI connected. Models: {len(models.data)} available.")
        except Exception as e:
            logger.error(f"❌ OpenAI auth failed: {e}")
    else:
        logger.warning("⚠️ OPENAI_API_KEY not found.")


@app.get("/health")
async def health():
    if not OPENAI_API_KEY:
        return JSONResponse(status_code=500, content={"status": "error", "message": "Missing OPENAI_API_KEY"})
    return {"status": "ok"}


@app.post("/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    session_id = str(uuid.uuid4())
    conn = faq.get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (id, user_id, metadata) VALUES (?, ?, ?)",
        (session_id, req.user_id or "", json.dumps(req.metadata or {}))
    )
    conn.commit()
    conn.close()
    return CreateSessionResponse(id=session_id, user_id=req.user_id, metadata=req.metadata)





@app.post("/message", response_model=MessageResponse)
async def handle_message(req: MessageRequest):
    # Ensure OpenAI client loaded
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized")

    session_id = req.session_id
    user_message = (req.user_message or "").strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="user_message cannot be empty")

    # Persist user message
    faq.save_message(session_id, "user", user_message)

    # Build conversation context for LLM
    recent = faq.get_recent_messages(session_id, limit=CONTEXT_WINDOW * 2)
    conversation = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent]) if recent else ""

    # Retrieve relevant FAQs (embedding search)
    top_faqs = faq.get_top_k_faqs(user_message, TOP_K_FAQ, FAQ_SIM_THRESHOLD)
    faq_text = "\n\n".join([f"Q: {f['question']}\nA: {f['answer']}" for f in top_faqs]) if top_faqs else ""

    # Call the LLM wrapper which now handles keyword escalation internally
    try:
        result = await generate_response(
        user_message=user_message,
        conversation_text=conversation,
        faq_text=faq_text,
        session_meta=None,
        session_id=session_id,
        )
    except Exception as e:
        logger.exception("LLM generate_response failed: %s", e)
        fallback = f"Sorry, something went wrong generating a response. ({str(e)})"
        faq.save_message(session_id, "assistant", fallback)
        return MessageResponse(reply=fallback, faqs=top_faqs, escalation=False, summary=None)


    # Normalize result shape
    reply_text = ""
    model_escalate = False
    model_faqs = top_faqs
    summary = None

    if isinstance(result, dict):
        reply_text = result.get("reply", "") or ""
        # support either 'escalation' or 'escalate' keys
        model_escalate = bool(result.get("escalation", result.get("escalate", False)))
        # if LLM returned faqs or summary include them
        model_faqs = result.get("faqs", top_faqs)
        summary = result.get("summary")
    else:
        reply_text = str(result)

    # Persist assistant reply
    faq.save_message(session_id, "assistant", reply_text)

    # Try to produce/refresh summary if not returned by LLM (best-effort)
    if not summary:
        try:
            convo_for_summary = conversation + "\nASSISTANT: " + reply_text
            s = summarize_session(session_id, convo_for_summary)
            if isinstance(s, dict):
                summary = s.get("summary")
        except Exception:
            # ignore summary errors — it's best-effort only
            summary = None

    return MessageResponse(
        reply=reply_text,
        faqs=model_faqs,
        escalation=model_escalate,
        summary=summary,
    )

from fastapi import Path
@app.post("/sessions/{session_id}/summarize")
async def summarize_endpoint(session_id: str = Path(..., description="Session UUID")):
    """
    Build a short conversation text for the given session and ask the LLM to produce
    a concise summary + next action via summarize_session(...) from llm_client.
    Returns the raw dictionary produced by summarize_session (e.g. {"summary": "...", "next_action": "..."})
    """
    # Grab recent messages for this session (more history for a good summary)
    try:
        recent = faq.get_recent_messages(session_id, limit=CONTEXT_WINDOW * 10)
    except Exception as e:
        logger.exception("Failed to fetch recent messages for summarization: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load session messages")

    if not recent:
        raise HTTPException(status_code=404, detail="No messages found for this session")

    # Build conversation text: alternate roles for clarity
    convo_lines = []
    for m in recent:
        role = (m.get("role") or "").upper()
        content = m.get("content") or ""
        convo_lines.append(f"{role}: {content}")
    conversation_text = "\n".join(convo_lines)

    # Call summarize helper (llm_client.summarize_session)
    try:
        result = summarize_session(session_id, conversation_text)
    except Exception as e:
        logger.exception("Summarize failed: %s", e)
        raise HTTPException(status_code=500, detail=f"summarize failed: {str(e)}")

    # result expected to be a dict like {"summary":"...","next_action":"..."}
    return result
