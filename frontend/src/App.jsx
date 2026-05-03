import { useState } from "react";
import ChatPage from "./components/ChatPage";
import WritingPage from "./components/WritingPage";
import HistoryPanel from "./components/HistoryPanel";
import "./index.css";

// Simple user ID — in production this would come from auth
const USER_ID = "default_user";

const NAV = [
  { id: "chat",    icon: "💬", label: "Chat Tutor",    subtitle: "Real-time corrections" },
  { id: "writing", icon: "✍️", label: "Writing Coach", subtitle: "IELTS essay feedback" },
  { id: "history", icon: "🧠", label: "My Progress",   subtitle: "Past mistakes & stats" },
];

export default function App() {
  const [page, setPage] = useState("chat");

  const current = NAV.find((n) => n.id === page);

  return (
    <div className="app-shell">
      {/* ── Sidebar ── */}
      <nav className="sidebar" aria-label="Main navigation">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">🎓</div>
          <div>
            <div className="sidebar-logo-text">AI English Tutor</div>
            <div className="sidebar-logo-sub">IELTS · Personalized</div>
          </div>
        </div>

        {NAV.map((item) => (
          <button
            key={item.id}
            id={`nav-${item.id}`}
            className={`nav-item ${page === item.id ? "active" : ""}`}
            onClick={() => setPage(item.id)}
            aria-current={page === item.id ? "page" : undefined}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        <div style={{ padding: "12px", borderTop: "1px solid var(--border)", marginTop: 8 }}>
          <div style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.6 }}>
            🔒 Your data stays local<br />
            🤖 Powered by GPT-4o-mini<br />
            ✨ RAG personalization active
          </div>
        </div>
      </nav>

      {/* ── Main content ── */}
      <main className="main-content">
        <header className="page-header">
          <span style={{ fontSize: 22 }}>{current.icon}</span>
          <div>
            <div className="page-title">{current.label}</div>
            <div className="page-subtitle">{current.subtitle}</div>
          </div>
        </header>

        <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          {page === "chat"    && <ChatPage    userId={USER_ID} />}
          {page === "writing" && <WritingPage userId={USER_ID} />}
          {page === "history" && <HistoryPanel userId={USER_ID} />}
        </div>
      </main>
    </div>
  );
}
