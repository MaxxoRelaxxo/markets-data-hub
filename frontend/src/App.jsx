import { useState, useEffect } from "react";
import CertificateSection from "./components/CertificateSection";
import BondsSection from "./components/BondsSection";
import SwestrSection from "./components/SwestrSection";
import ScbRatesSection from "./components/ScbRatesSection";

function getWeekNumber(d) {
  const target = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  target.setUTCDate(target.getUTCDate() + 4 - (target.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(target.getUTCFullYear(), 0, 1));
  return Math.ceil(((target - yearStart) / 86400000 + 1) / 7);
}

const formatDate = (s) => {
  if (!s) return "\u2013";
  return new Date(s).toLocaleDateString("sv-SE", { day: "numeric", month: "short", year: "numeric" });
};

const TABS = [
  { id: "cert", label: "Riksbankscertifikat" },
  { id: "gov", label: "Försäljning av Statsobligationer" },
  { id: "swestr", label: "Swestr" },
  { id: "scb", label: "SCB Räntor" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("cert");
  const [swestrData, setSwestrData] = useState(null);
  const [mounted, setMounted] = useState(false);

  const now = new Date();
  const week = getWeekNumber(now);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    fetch("./data/swestr_data.json")
      .then((r) => r.json())
      .then(setSwestrData);
  }, []);

  const lastRate = swestrData?.latest?.rate;
  const lastTs = swestrData?.timeseries;
  const policyRate = lastTs?.[lastTs.length - 1]?.policy_rate;
  const lastDate = lastTs?.[lastTs.length - 1]?.date;

  return (
    <div className="app" style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.3s ease" }}>
      {/* Header */}
      <header className="header">
        <div className="container">
          <div className="header-top">
            <div>
              <div className="header-brand">
                <div className="header-accent" />
                <h1 className="header-title">Marknadsdata</h1>
              </div>
              <div className="header-meta">
                Vecka {week} &middot; {now.getFullYear()}
              </div>
            </div>
            <div className="header-stats">
              <div className="header-stat">
                <div className="header-stat-label">Styränta</div>
                <div className="header-stat-value">
                  {policyRate != null ? `${policyRate.toFixed(2).replace(".", ",")} %` : "\u2013"}
                </div>
              </div>
              <div className="header-stat">
                <div className="header-stat-label">SWESTR</div>
                <div className="header-stat-value">
                  {lastRate != null ? `${lastRate.toFixed(3).replace(".", ",")} %` : "\u2013"}
                </div>
              </div>
              <div className="header-stat">
                <div className="header-stat-label">Senast uppdaterat</div>
                <div className="header-stat-value">{formatDate(lastDate)}</div>
              </div>
            </div>
          </div>
          <nav className="header-nav">
            {TABS.map((t) => (
              <button
                key={t.id}
                className={`header-nav-btn ${activeTab === t.id ? "active" : ""}`}
                onClick={() => setActiveTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="container" style={{ paddingBottom: 48 }}>
        {activeTab === "cert" && <CertificateSection />}
        {activeTab === "gov" && <BondsSection />}
        {activeTab === "swestr" && <SwestrSection />}
        {activeTab === "scb" && <ScbRatesSection />}

        <div className="footer">
          <div>Publicerat: {now.toISOString().slice(0, 10)}</div>
          <div className="footer-right">Marknadsdata &mdash; Vecka {week} {now.getFullYear()}</div>
        </div>
      </main>
    </div>
  );
}
