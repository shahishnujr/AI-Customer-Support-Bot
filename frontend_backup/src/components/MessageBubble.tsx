// MessageBubble.tsx
import React from "react";

type Props = { role: "user" | "assistant"; text: string; ts?: string; escalated?: boolean };

export default function MessageBubble({ role, text, ts, escalated }: Props) {
  const isUser = role === "user";
  return (
    <div className={`msg-row ${isUser ? "msg-right" : "msg-left"}`}>
      {!isUser && (
        <div className="avatar-circle" style={{ background: "rgba(255,255,255,0.04)" }}>
          AI
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start" }}>
        <div className={`bubble ${isUser ? "bubble-user" : "bubble-assistant"}`}>
          <div style={{ whiteSpace: "pre-wrap" }}>{text}</div>
        </div>
        <div className="msg-ts">{ts ?? new Date().toLocaleTimeString()}</div>
        {!isUser && escalated && <div style={{ color: "crimson", fontWeight: 700, marginTop: 6 }}>⚠️ Escalation recommended</div>}
      </div>

      {isUser && (
        <div className="avatar-circle" style={{ background: "linear-gradient(90deg,#06b6d4,#3dd9df)", color: "#02121a" }}>
          You
        </div>
      )}
    </div>
  );
}
