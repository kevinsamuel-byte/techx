"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { api } from "@/lib/api";

type Props = {
  token: string;
  onAfterAction: () => Promise<void>;
};

export function GuruChat({ token, onAfterAction }: Props) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("Hi, I am AGENT GURU. Ask me to add goals, remove modules, or update resume.");

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    const result = await api.chatGuru(token, message);
    setReply(result.reply);
    setMessage("");
    await onAfterAction();
  };

  return (
    <>
      <button className="guru-fab" onClick={() => setOpen((prev) => !prev)}>
        <Sparkles size={18} /> AGENT GURU
      </button>
      {open && (
        <aside className="guru-panel">
          <h3>AGENT GURU</h3>
          <p>{reply}</p>
          <form onSubmit={send}>
            <input value={message} onChange={(e) => setMessage(e.target.value)} placeholder="add new goal: AI Product Manager" />
            <button type="submit">Send</button>
          </form>
        </aside>
      )}
    </>
  );
}
