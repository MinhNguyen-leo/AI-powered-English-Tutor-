import { useState } from "react";
import { sendWritingText } from "../services/api";
import ScoreRing from "./ScoreRing";

export default function WritingPage({ userId }) {
  const [text, setText] = useState("");
  const [taskType, setTaskType] = useState("Task 2");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!text.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const { data } = await sendWritingText(userId, text, taskType);
      setResult(data);
    } catch (err) {
      setError("⚠️ Could not analyze the essay. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  return (
    <div className="writing-layout">
      {/* ── Left: Input panel ── */}
      <div className="writing-input-panel">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <select
            id="task-type-select"
            className="task-select"
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
          >
            <option value="Task 1">IELTS Task 1</option>
            <option value="Task 2">IELTS Task 2</option>
          </select>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {wordCount} words
            {taskType === "Task 2" && wordCount < 250 && wordCount > 0 && (
              <span style={{ color: "var(--amber-400)" }}> (aim for 250+)</span>
            )}
          </span>
        </div>

        <textarea
          id="writing-textarea"
          className="writing-textarea"
          placeholder={`Paste your IELTS ${taskType} essay here…\n\nExample: "Some people believe that technology has made life more complex. Others argue it has made things simpler. Discuss both views and give your own opinion."`}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <button
          id="analyze-btn"
          className="analyze-btn"
          onClick={handleAnalyze}
          disabled={text.trim().length < 10 || loading}
        >
          {loading ? (
            <>
              <div className="spinner" />
              Analyzing your essay…
            </>
          ) : (
            <>✍️ Analyze &amp; Score Essay</>
          )}
        </button>

        {error && (
          <div style={{ color: "var(--red-400)", fontSize: 13, padding: "10px 0" }}>
            {error}
          </div>
        )}

        <div className="card" style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.7 }}>
          <div style={{ fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>
            💡 Tips for a better score
          </div>
          <ul style={{ paddingLeft: 16, display: "flex", flexDirection: "column", gap: 4 }}>
            <li>Task 2: Write at least 250 words</li>
            <li>Use linking words (However, Furthermore, In addition…)</li>
            <li>Include a clear introduction + 2 body paragraphs + conclusion</li>
            <li>Vary your sentence structures</li>
          </ul>
        </div>
      </div>

      {/* ── Right: Results panel ── */}
      <div className="writing-result-panel">
        {!result && !loading && (
          <div className="empty-state">
            <div className="empty-icon">📝</div>
            <div>Write or paste your essay on the left,<br />then click Analyze to get your IELTS feedback.</div>
          </div>
        )}

        {result && (
          <>
            {/* Band estimate hero */}
            <div className="card" style={{ textAlign: "center", padding: "28px 20px" }}>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.8px" }}>
                Estimated IELTS Band
              </div>
              <ScoreRing
                value={result.ielts_score.estimated_band}
                label=""
                color="#10b981"
                size={96}
              />
              <div style={{ marginTop: 12, fontSize: 13, color: "var(--text-secondary)" }}>
                {result.ielts_score.estimated_band >= 7
                  ? "🎉 Excellent! Band 7+ achieved."
                  : result.ielts_score.estimated_band >= 6
                  ? "📈 Good progress — keep refining!"
                  : "💪 Keep practising — you're improving!"}
              </div>
            </div>

            {/* Sub-scores grid */}
            <div className="card">
              <div className="section-label">Score Breakdown</div>
              <div className="ielts-scores-grid">
                {[
                  { label: "Task Achievement", key: "task_achievement" },
                  { label: "Coherence & Cohesion", key: "coherence_cohesion" },
                  { label: "Lexical Resource", key: "lexical_resource" },
                  { label: "Grammatical Range", key: "grammatical_range" },
                ].map(({ label, key }) => {
                  const val = result.ielts_score[key];
                  return (
                    <div key={key} className="score-item">
                      <div className="score-item-label">{label}</div>
                      <div className="score-item-value">{val.toFixed(1)}</div>
                      <div className="score-item-bar">
                        <div
                          className="score-item-bar-fill"
                          style={{ width: `${(val / 9) * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Overall feedback */}
            <div className="card">
              <div className="section-label">Overall Feedback</div>
              <div className="feedback-text">{result.overall_feedback}</div>
            </div>

            {/* Strengths & areas */}
            <div className="card">
              <div className="section-label" style={{ marginBottom: 10 }}>Strengths</div>
              <div className="tags-list">
                {result.strengths.map((s, i) => (
                  <span key={i} className="tag strength">✅ {s}</span>
                ))}
                {result.strengths.length === 0 && (
                  <span style={{ color: "var(--text-muted)", fontSize: 13 }}>None identified yet.</span>
                )}
              </div>

              <div className="section-label" style={{ marginTop: 16, marginBottom: 10 }}>Areas to Improve</div>
              <div className="tags-list">
                {result.areas_to_improve.map((a, i) => (
                  <span key={i} className="tag improve">⚡ {a}</span>
                ))}
              </div>
            </div>

            {/* Sentence corrections */}
            {result.corrections.length > 0 && (
              <div className="card">
                <div className="section-label">Sentence Corrections</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {result.corrections.map((c, i) => (
                    <div key={i} className="correction-item">
                      <div className="label">{c.issue}</div>
                      <div className="original">"{c.original_sentence}"</div>
                      <div className="corrected">→ "{c.corrected_sentence}"</div>
                      <div className="expl">{c.suggestion}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
