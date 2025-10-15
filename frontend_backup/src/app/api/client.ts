// src/api/client.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export type SessionCreateResp = {
  id: string;
  user_id?: string | null;
  metadata?: any | null;
  created_at?: string | null;
};

export type ChatResponse = {
  reply: string;
  faqs?: Array<{ id: number; question: string; answer: string; score: number }>;
  escalation: boolean;
  summary?: string | null;
  reason?: string | null;
};

export async function createSession(userId = "web_user"): Promise<SessionCreateResp> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, metadata: {} }),
  });
  if (!res.ok) throw new Error(`createSession failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function postMessage(sessionId: string, user_message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, user_message }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`postMessage failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function summarize(sessionId: string) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`summarize failed: ${res.status} ${await res.text()}`);
  return res.json();
}
