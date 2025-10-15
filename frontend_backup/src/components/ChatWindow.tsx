// ChatWindow.tsx (modern centered layout) - always start fresh on load
"use client";
import React, { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import Composer from "./Composer";
import { createSession, postMessage, summarize } from "../app/api/client";

type Msg = {
  id: string;
  role: "user" | "assistant";
  text: string;
  ts?: string;
  escalated?: boolean;
};

export default function ChatWindow() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [sending, setSending] = useState(false);
  const [typing, setTyping] = useState(false);
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  // Always create a new session on mount (do NOT reuse localStorage)
  useEffect(() => {
    (async () => {
      try {
        const s = await createSession("web_user");
        setSessionId(s.id);
        // start with an empty message list for a fresh chat
        setMsgs([]);
      } catch (err) {
        setMsgs([
          {
            id: "sys",
            role: "assistant",
            text: "Failed to create session (backend unavailable).",
            ts: new Date().toLocaleTimeString(),
          },
        ]);
      }
    })();
    // run once on mount
  }, []);

  // autoscroll when messages or typing change
  useEffect(() => {
    scrollerRef.current?.scrollTo({ top: scrollerRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, typing]);

  async function handleSend(text: string) {
    if (!sessionId) {
      setMsgs((m) => [
        ...m,
        { id: `err-${Date.now()}`, role: "assistant", text: "No session. Try reloading.", ts: new Date().toLocaleTimeString() },
      ]);
      return;
    }

    setSending(true);
    const userMsg: Msg = { id: `u-${Date.now()}`, role: "user", text, ts: new Date().toLocaleTimeString() };
    setMsgs((m) => [...m, userMsg]);

    try {
      setTyping(true);
      const res = await postMessage(sessionId, text);
      setTyping(false);

      const assistantMsg: Msg = {
        id: `a-${Date.now()}`,
        role: "assistant",
        text: res.reply,
        ts: new Date().toLocaleTimeString(),
        // backend returns `escalation` boolean
        escalated: !!res.escalation,
      };
      setMsgs((m) => [...m, assistantMsg]);
    } catch (err: any) {
      setTyping(false);
      setMsgs((m) => [
        ...m,
        { id: `err-${Date.now()}`, role: "assistant", text: `Error: ${err?.message ?? String(err)}`, ts: new Date().toLocaleTimeString() },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="chat-root">
      <div className="chat-panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <div>
            <h1 style={{ fontSize: 28, margin: 0, fontWeight: 700 }}>AI Customer Support</h1>
            <div style={{ color: "var(--muted)", fontSize: 13 }}>Answers · escalation simulation</div>
          </div>
          <div>
            <button
              className="px-3 py-1 rounded border border-slate-700 text-sm"
              onClick={async () => {
                if (!sessionId) return alert("No session");
                try {
                  const s = await summarize(sessionId);
                  alert(s.summary || "No summary");
                } catch (e: any) {
                  alert("Summarize failed: " + (e?.message ?? String(e)));
                }
              }}
            >
              Summarize
            </button>
          </div>
        </div>

        <div className="chat-messages" ref={scrollerRef} style={{ overflowY: "auto", maxHeight: "60vh", marginTop: 12 }}>
          {msgs.length === 0 && (
            <div style={{ color: "var(--muted)", textAlign: "center", marginTop: 30 }}>
              Welcome! Ask about orders, refunds, or support hours.
            </div>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {msgs.map((m) => (
              <MessageBubble key={m.id} role={m.role} text={m.text} ts={m.ts} escalated={m.escalated} />
            ))}
            {typing && <div style={{ color: "var(--muted)" }}>AI is typing…</div>}
          </div>
        </div>

        <Composer onSend={handleSend} sending={sending} />
      </div>
      <div style={{ width: "100%", maxWidth: 980, padding: "0 18px 18px", boxSizing: "border-box" }}>
        <div style={{ color: "var(--muted)", fontSize: 13, textAlign: "center" }}>
          Tip: Try asking "Where is my order?" or request a refund — the bot will escalate if needed.
        </div>
      </div>
    </div>
  );
}
