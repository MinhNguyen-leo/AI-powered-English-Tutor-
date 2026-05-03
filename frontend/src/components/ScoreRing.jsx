// Reusable animated score ring component
// value: 0–9 IELTS scale
export default function ScoreRing({ value = 0, label = "", color = "#3b82f6", size = 72 }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(Math.max(value / 9, 0), 1);
  const dash = progress * circumference;

  return (
    <div className="score-ring-container">
      <div className="score-ring" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          {/* Track */}
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6"
          />
          {/* Progress */}
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={color} strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference}`}
            style={{ transition: "stroke-dasharray 0.8s ease-out" }}
          />
        </svg>
        <div className="score-ring-value" style={{ fontSize: size * 0.24 }}>
          {value.toFixed(1)}
        </div>
      </div>
      {label && <span className="score-ring-label">{label}</span>}
    </div>
  );
}
