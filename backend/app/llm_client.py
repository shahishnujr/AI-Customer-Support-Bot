# backend/app/llm_client.py
import os
import json
import logging
from typing import Dict, Any, Optional
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from dotenv import load_dotenv

# load .env (ensure backend/.env is loaded)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# New OpenAI client
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set. LLM calls will fail until set.")

# instantiate client (reads OPENAI_API_KEY from env automatically)
client = OpenAI(api_key=OPENAI_API_KEY)

# Choose model(s) via env override if you want
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")  # change to preferred model
# Note: embeddings model separate; faq.py will use embeddings

SYSTEM_PROMPT = """
You are an AI customer-support assistant. You should answer user queries concisely,
use information from the provided FAQ and conversation history, and be helpful and polite.

IMPORTANT: Your final response must be valid JSON (and only JSON) with the following structure:
{
  "reply": "<the assistant text reply to the user>",
  "escalate": <true or false>,
  "reason": "<optional short reason if escalate is true or null>"
}
"""

# Retry policy for transient OpenAI issues
@retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
def _call_chat_api(messages, temperature=0.15, max_tokens=800):
    """
    Uses the new OpenAI client: client.chat.completions.create(...)
    """
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp

def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end+1]
            try:
                return json.loads(candidate)
            except Exception:
                return None
        return None

def _extract_choice_content(choice) -> str:
    """
    Robustly extract assistant text content from a choice returned by the new OpenAI client.
    Handles shapes like:
      - choice.message (object) with .content attribute or dict-like
      - choice.get("message", {}) where message is dict
      - choice.text or getattr(choice, "text")
    Returns the extracted string (or empty string if not found).
    """
    try:
        # If choice has attribute 'message'
        if hasattr(choice, "message"):
            msg = choice.message
            # msg might be dict-like or object-like
            if isinstance(msg, dict):
                return msg.get("content", "") or ""
            # try attribute access
            content = getattr(msg, "content", None)
            if content is not None:
                return content
            # some shapes: msg.get("content") via attribute access fallback
            try:
                return msg["content"]
            except Exception:
                pass

        # If choice is dict-like
        if isinstance(choice, dict):
            # choice.get("message") might be dict
            msg = choice.get("message") or choice.get("delta") or {}
            if isinstance(msg, dict):
                return msg.get("content", "") or ""
            # direct text fallback
            return choice.get("text", "") or ""

        # If choice has .text attribute (older shape)
        text_attr = getattr(choice, "text", None)
        if text_attr:
            return text_attr

    except Exception as e:
        logger.exception("Error while extracting content from choice: %s", e)

    # final fallback
    try:
        return str(choice)
    except Exception:
        return ""

async def generate_response(user_message: str, conversation_text: str = "", faq_text: str = "", session_meta=None, session_id=None):
    """
    Generate an AI response with built-in keyword-based escalation.
    If certain keywords appear (refund, complaint, cancel, etc.),
    the bot will immediately escalate with a direct contact message.
    """
    escalation_keywords = [
    "hack", "hacked", "hacking", "attack", "attacked", "breach", "breached",
    "return", "returns", "returning", "return policy", "exchange", "exchanges",
    " broken", "defective", "not working", "doesn't work", "warranty", "guarantee",
    "refund", "charge", "charged", "billing", "invoice", "cancel", "cancellation",
    "subscription", "payment", "double charged", "overcharged", "unauthorized charge",
    "fraud", "credit card", "bank", "refund please", "refund me"
]

    lower_msg = user_message.lower()

    # 🔹 Detect escalation keywords and short-circuit reply
    if any(k in lower_msg for k in escalation_keywords):
        return {
            "reply": "⚠️ I’m unable to assist with that request directly. Please contact support@example.com for further help regarding your issue.",
            "escalation": True,
            "summary": f"Escalated issue detected in user message: '{user_message}'",
            "faqs": [],
        }

    try:
        messages = [
            {"role": "system", "content": "You are an AI support assistant. Be brief, polite, and helpful."},
        ]
        if conversation_text:
            messages.append({"role": "system", "content": f"Conversation so far:\n{conversation_text}"})
        if faq_text:
            messages.append({"role": "system", "content": f"Relevant FAQs:\n{faq_text}"})

        messages.append({"role": "user", "content": user_message})

        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            max_tokens=250,
        )

        choice = completion.choices[0]
        assistant_text = choice.message.content if hasattr(choice, "message") else choice.get("message", {}).get("content", "")

        return {
            "reply": assistant_text.strip(),
            "escalation": False,
            "summary": None,
            "faqs": [],
        }

    except Exception as e:
        logging.error(f"LLM generate_response failed: {e}")
        return {
            "reply": f"⚠️ I’m sorry — something went wrong while generating a response. ({str(e)})",
            "escalation": False,
            "summary": None,
            "faqs": [],
        }

def summarize_session(session_id: int, conversation_text: str) -> Dict[str, Any]:
    system = "You are a concise summarizer for customer support transcripts."
    user_prompt = f"Summarize the following conversation in 2-3 sentences and provide a short next action label (one short phrase). Conversation:\n\n{conversation_text}\n\nReturn JSON: {{\"summary\":\"...\",\"next_action\":\"...\"}}"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt}
    ]
    try:
        resp = _call_chat_api(messages, temperature=0.0, max_tokens=400)
        choices = resp.choices if hasattr(resp, "choices") else resp.get("choices", [])
        if not choices:
            raise RuntimeError("No choices in summarizer response")
        text = _extract_choice_content(choices[0])
        parsed = _extract_json_from_text(text)
        if parsed:
            return {"summary": parsed.get("summary", ""), "next_action": parsed.get("next_action")}
        return {"summary": text.strip(), "next_action": None}
    except Exception as e:
        logger.exception("Summarize failed: %s", e)
        raise
