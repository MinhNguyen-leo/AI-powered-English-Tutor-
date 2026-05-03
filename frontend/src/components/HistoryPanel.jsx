import { useState, useEffect } from "react";
import { getMemoryStats, getMemoryErrors } from "../services/api";

const BADGE_CLASS = {
  grammar: "badge-grammar",
  vocabulary: "badge-vocabulary",
  spelling: "badge-spelling",
};

export default function HistoryPanel({ userId }) {
  const [stats, setStats] = useState(null);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [sRes, eRes] = await Promise.all([
        getMemoryStats(userId),
        getMemoryErrors(userId, 30),
      ]);
      setStats(sRes.data);
      setErrors(eRes.data.errors || []);
    } catch {
      // silently ignore — user may not have any history yet
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [userId]);

  if (loading) {
    return (
      <div className="history-layout" style={{ alignItems: "center", justifyContent: "center" }}>
        <div className="spinner" style={{ width: 32, height: 32 }} />
      </div>
    );
  }

  const total = stats?.total_errors ?? 0;
  const breakdown = stats?.error_breakdown ?? {};

  return (
    <div className="history-layout">
      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{total}</div>
          <div className="stat-label">Total Errors Caught</div>
        </div>
        {Object.entries(breakdown).map(([type, count]) => (
          <div key={type} className="stat-card">
            <div className="stat-number">{count}</div>
            <div className="stat-label" style={{ textTransform: "capitalize" }}>{type}</div>
          </div>
        ))}
      </div>

      {/* Error list */}
      {errors.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🧠</div>
          <div>
            No mistakes recorded yet.<br />
            Start chatting or submit a writing task!
          </div>
        </div>
      ) : (
        <>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)" }}>
              Recent Mistakes ({errors.length})
            </div>
            <button
              onClick={load}
              style={{
                background: "none", border: "1px solid var(--border)",
                color: "var(--text-secondary)", borderRadius: "var(--radius-sm)",
                padding: "4px 12px", fontSize: 12, cursor: "pointer"
              }}
            >
              ↻ Refresh
            </button>
          </div>
          <div className="error-list">
            {[...errors].reverse().map((err, i) => (
              <div key={i} className="error-record">
                <span
                  className={`error-type-badge ${BADGE_CLASS[err.error_type] || "badge-unknown"}`}
                >
                  {err.error_type}
                </span>
                <div className="error-original">"{err.original}"</div>
                <div className="error-corrected">✓ "{err.corrected}"</div>
                <div className="error-expl">{err.explanation}</div>
                <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 6 }}>
                  {new Date(err.timestamp).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
