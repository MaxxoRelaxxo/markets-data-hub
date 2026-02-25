function getWeekNumber(d) {
  const target = new Date(d.valueOf());
  target.setDate(target.getDate() + 3 - ((target.getDay() + 6) % 7));
  const jan4 = new Date(target.getFullYear(), 0, 4);
  return 1 + Math.round(((target - jan4) / 86400000 - 3 + ((jan4.getDay() + 6) % 7)) / 7);
}

export default function Header() {
  const now = new Date();
  const week = getWeekNumber(now);

  return (
    <header className="header">
      <div className="header-inner">
        <h1 className="header-title">Marknadsdata</h1>
        <div className="header-subtitle">
          Vecka {week}, {now.getFullYear()}
          <span className="header-badge">
            <span className="header-badge-dot" />
            Dagster
          </span>
        </div>
      </div>
    </header>
  );
}
