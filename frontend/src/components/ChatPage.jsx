import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../services/api";
import ScoreRing from "./ScoreRing";

const WELCOME = {
  id: "welcome",
  role: "ai",
  text: "👋 Hi! I'm your AI English tutor. Send me any text in English — a sentence, a paragraph, or a question — and I'll help you correct mistakes and improve your IELTS score!",
  corrections: [],
  score: null,
  contextUsed: false,
};

export default function ChatPage({ userId }) {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { id: Date.now(), role: "user", text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await sendChatMessage(userId, text);
      const aiMsg = {
        id: Date.now() + 1,
        role: "ai",
        text: data.corrected_text,
        explanation: data.explanation,
        corrections: data.errors || [],
        score: data.score,
        contextUsed: data.context_used,
      };
      setMessages((m) => [...m, aiMsg]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: "ai",
          text: "⚠️ Sorry, I couldn't process that. Please check your connection and try again.",
          corrections: [],
          score: null,
          contextUsed: false,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages" id="chat-messages-list">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-row ${msg.role}`}>
            <div className={`avatar ${msg.role}`}>
              {msg.role === "user" ? "👤" : "🤖"}
            </div>
            <div className={`bubble ${msg.role}`}>
              {msg.contextUsed && (
                <div className="context-badge">
                  ✨ Personalized from your past mistakes
                </div>
              )}

              <div>{msg.text}</div>

              {msg.explanation && msg.corrections?.length === 0 && (
                <div style={{ marginTop: 8, color: "var(--green-400)", fontSize: 13 }}>
                  ✅ {msg.explanation}
                </div>
              )}

              {msg.corrections?.length > 0 && (
                <div className="correction-block">
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>
                    🔍 {msg.corrections.length} issue{msg.corrections.length > 1 ? "s" : ""} found:
                  </div>
                  {msg.corrections.map((c, i) => (
                    <div key={i} className="correction-item">
                      <div className="label">{c.error_type}</div>
                      <div className="original">"{c.original}"</div>
                      <div className="corrected">→ "{c.corrected}"</div>
                      <div className="expl">{c.explanation}</div>
                    </div>
                  ))}
                  {msg.explanation && (
                    <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>
                      💬 {msg.explanation}
                    </div>
                  )}
                </div>
              )}

              {msg.score && (
                <div className="scores-row">
                  <ScoreRing value={msg.score.grammar}    label="Grammar"    color="#3b82f6" size={64} />
                  <ScoreRing value={msg.score.vocabulary} label="Vocabulary" color="#10b981" size={64} />
                  <ScoreRing value={msg.score.overall}    label="Overall"    color="#a78bfa" size={64} />
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-row ai">
            <div className="avatar ai">🤖</div>
            <div className="bubble ai">
              <div className="typing-dots">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <div className="input-row">
          <textarea
            id="chat-input"
            ref={textareaRef}
            className="chat-textarea"
            rows={1}
            placeholder="Type your English text here… (Shift+Enter for new line)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            id="chat-send-btn"
            className="send-btn"
            onClick={handleSend}
            disabled={!input.trim() || loading}
            aria-label="Send message"
          >
            {loading ? <div className="spinner" style={{ width: 16, height: 16 }} /> : "➤"}
          </button>
        </div>
        <div style={{ marginTop: 8, fontSize: 11, color: "var(--text-muted)", textAlign: "center" }}>
          Your mistakes are remembered to personalize future corrections ✨
        </div>
      </div>
    </div>
  );
}
