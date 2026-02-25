export default function StatCard({ value, label, delta, accentColor }) {
  const deltaClass = delta
    ? delta.startsWith("+") || (delta.startsWith("Δ +") || delta.startsWith("Δ+"))
      ? "positive"
      : delta.includes("+0") || delta.includes("0.0") || delta === "Δ 0"
        ? "neutral"
        : "negative"
    : null;

  // Detect truly neutral (zero change)
  const isNeutral = delta && (
    delta === "Δ 0" || delta === "+0.0 mdkr" || delta === "Δ +0" ||
    delta.includes("+0.0") || delta.includes("-0.0")
  );

  return (
    <div className="stat-card">
      {accentColor && (
        <div className="stat-card-accent" style={{ background: accentColor }} />
      )}
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {delta && (
        <span className={`stat-delta ${isNeutral ? "neutral" : deltaClass}`}>
          {delta}
        </span>
      )}
    </div>
  );
}
