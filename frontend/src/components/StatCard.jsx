export default function StatCard({ value, label, caption }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {caption && <div className="stat-caption">{caption}</div>}
    </div>
  );
}
