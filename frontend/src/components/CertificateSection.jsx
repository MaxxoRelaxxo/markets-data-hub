import { useState, useEffect } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, Legend,
} from "recharts";
import StatCard from "./StatCard";

const fmt = (v) => v != null ? v.toFixed(1).replace(".", ",") : "\u2013";

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tt">
      <div className="tt-label">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tt-row">
          <div className="tt-dot" style={{ background: p.color }} />
          <span className="tt-name">{p.name}:</span>
          <span className="tt-val">{p.value != null ? `${p.value.toFixed(1)} mdkr` : "\u2013"}</span>
        </div>
      ))}
    </div>
  );
}

export default function CertificateSection() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("./data/cert_data.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return null;
  const { latest: l, timeseries } = data;

  const chartData = timeseries.slice(-120).map((d) => ({
    date: d.date.slice(0, 7),
    "Erbjuden volym": d.erbjuden_volym,
    "Likviditetsoverskott": d.aterstaende,
    "Rantefri inlaning": d.rantefri_inlaning,
  }));

  return (
    <div>
      <div className="section-header">
        <div className="section-accent" />
        <h2 className="section-title">Marknadsoperationer</h2>
        <p className="section-sub">Auktionsresultat Riksbankscertifikat</p>
      </div>

      <div className="stat-row">
        <StatCard label="Erbjuden volym" value={fmt(l.erbjuden_volym)} unit="mdkr" delta={l.delta_erbjuden} />
        <StatCard label="Tilldelad volym" value={fmt(l.tilldelad_volym)} unit="mdkr" delta={l.delta_tilldelad} />
        <StatCard label="Aterstande overskott" value={fmt(l.aterstaende)} unit="mdkr" delta={l.delta_aterstaende} />
        <StatCard label="Antal bud" value={String(l.antal_bud)} delta={l.delta_antal_bud} />
      </div>

      <div className="chart-card">
        <div className="chart-card-title">Likviditetsoverskott over tid</div>
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="gCertBlue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0071B9" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#0071B9" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="gCertRed" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#B91E2B" stopOpacity={0.7} />
                <stop offset="95%" stopColor="#B91E2B" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="gCertAmber" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#D4880A" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#D4880A" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" />
            <XAxis
              dataKey="date" interval={11}
              tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
              width={60}
            />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
            <Area type="monotone" dataKey="Erbjuden volym" stroke="#0071B9" fill="url(#gCertBlue)" strokeWidth={2} />
            <Area type="monotone" dataKey="Likviditetsoverskott" stroke="#B91E2B" fill="url(#gCertRed)" strokeWidth={2} />
            <Area type="monotone" dataKey="Rantefri inlaning" stroke="#D4880A" fill="url(#gCertAmber)" strokeWidth={2} connectNulls={false} />
          </AreaChart>
        </ResponsiveContainer>
        <div className="chart-note">
          Grafen omfattar ej aterforsakring av riksbankscertifikat eller finjusterade transaktioner. Kalla: Riksbanken.
        </div>
      </div>
    </div>
  );
}
