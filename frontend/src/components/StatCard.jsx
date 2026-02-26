export default function StatCard({ label, value, unit, delta }) {
  const isPos = delta > 0;
  const isNeg = delta < 0;
  const cls = isPos ? "positive" : isNeg ? "negative" : "neutral";

  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">
        {value}
        {unit && <span className="stat-unit">{unit}</span>}
      </div>
      {delta !== undefined && delta !== null && (
        <div className={`stat-delta ${cls}`}>
          {isPos ? "\u25B2" : isNeg ? "\u25BC" : "\u2014"}{" "}
          {isPos ? "+" : ""}{typeof delta === "number" ? delta.toFixed(1).replace(".", ",") : delta}
          {unit ? ` ${unit}` : ""}
        </div>
      )}
    </div>
  );
}
