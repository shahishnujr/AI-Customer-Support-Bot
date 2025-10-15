// Composer.tsx
"use client";
import React, { useRef, useState } from "react";
import { ArrowRight } from "lucide-react";

export default function Composer({ onSend, sending }: { onSend: (text: string) => Promise<void>; sending: boolean }) {
  const [text, setText] = useState("");
  const taRef = useRef<HTMLTextAreaElement | null>(null);

  const submit = async () => {
    const t = text.trim();
    if (!t) return;
    await onSend(t);
    setText("");
    taRef.current?.focus();
  };

  return (
    <div className="chat-composer">
      <textarea
        ref={taRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={async (e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            await submit();
          }
        }}
        placeholder="Type a message — press Enter to send. Shift+Enter for newline."
        className="chat-input"
        rows={1}
      />
      <button onClick={submit} disabled={sending} className="chat-send">
        <ArrowRight size={16} />
      </button>
    </div>
  );
}
