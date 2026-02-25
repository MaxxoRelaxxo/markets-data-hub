const MONTHS = {
  0: "Januari", 1: "Februari", 2: "Mars", 3: "April",
  4: "Maj", 5: "Juni", 6: "Juli", 7: "Augusti",
  8: "September", 9: "Oktober", 10: "November", 11: "December",
};

function getWeekNumber(d) {
  const target = new Date(d.valueOf());
  target.setDate(target.getDate() + 3 - ((target.getDay() + 6) % 7));
  const jan4 = new Date(target.getFullYear(), 0, 4);
  return 1 + Math.round(((target - jan4) / 86400000 - 3 + ((jan4.getDay() + 6) % 7)) / 7);
}

export default function Header() {
  const now = new Date();
  const week = getWeekNumber(now);
  const datum = `Vecka ${week} - ${now.getFullYear()}`;

  return (
    <header className="header">
      <div className="header-inner">
        <h1 className="header-title">Marknadsdata</h1>
        <div className="header-subtitle">{datum}</div>
      </div>
    </header>
  );
}
