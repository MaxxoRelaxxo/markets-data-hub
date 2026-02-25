import { useState, useEffect } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from "recharts";
import StatCard from "./StatCard";

const COLORS = {
  erbjuden_volym: "var(--chart-blue)",
  aterstaende: "var(--chart-red)",
  rantefri_inlaning: "var(--chart-amber)",
};

function fmt(v) { return v != null ? `${v.toFixed(1)}` : "-"; }
function fmtUnit(v) { return v != null ? `${v.toFixed(1)} mdkr` : "-"; }

function delta(v) {
  if (v == null) return null;
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)} mdkr`;
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <p><strong>{label}</strong></p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {p.value != null ? `${p.value.toFixed(1)} mdkr` : "-"}
        </p>
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

  return (
    <section className="section" id="certificates">
      <div className="section-title">
        <span className="section-title-icon blue">&#xf3;</span>
        Riksbankscertifikat
      </div>

      <div className="stat-row">
        <StatCard
          value={fmt(l.erbjuden_volym)}
          label="Erbjuden volym (mdkr)"
          delta={delta(l.delta_erbjuden)}
          accentColor="var(--chart-blue)"
        />
        <StatCard
          value={fmt(l.tilldelad_volym)}
          label="Tilldelad volym (mdkr)"
          delta={delta(l.delta_tilldelad)}
          accentColor="var(--chart-teal)"
        />
        <StatCard
          value={fmt(l.aterstaende)}
          label="Likviditetsoversott (mdkr)"
          delta={delta(l.delta_aterstaende)}
          accentColor="var(--chart-amber)"
        />
        <StatCard
          value={String(l.antal_bud)}
          label="Antal bud"
          delta={l.delta_antal_bud != null ? `\u0394 ${l.delta_antal_bud >= 0 ? "+" : ""}${l.delta_antal_bud}` : null}
          accentColor="var(--chart-purple)"
        />
      </div>

      <div className="chart-card">
        <div className="chart-card-header">
          <div>
            <div className="chart-card-title">Likviditetsoversott over tid</div>
            <div className="chart-card-subtitle">Miljarder kronor</div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={380}>
          <AreaChart data={timeseries}>
            <defs>
              <linearGradient id="gradBlue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={COLORS.erbjuden_volym} stopOpacity={0.3} />
                <stop offset="100%" stopColor={COLORS.erbjuden_volym} stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="gradRed" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={COLORS.aterstaende} stopOpacity={0.3} />
                <stop offset="100%" stopColor={COLORS.aterstaende} stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="gradAmber" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={COLORS.rantefri_inlaning} stopOpacity={0.3} />
                <stop offset="100%" stopColor={COLORS.rantefri_inlaning} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={(d) => d.slice(0, 4)}
              minTickGap={60}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#94a3b8", fontSize: 12 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              width={50}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone" dataKey="erbjuden_volym" name="Erbjuden volym"
              stackId="1" fill="url(#gradBlue)" stroke={COLORS.erbjuden_volym}
              strokeWidth={2}
            />
            <Area
              type="monotone" dataKey="aterstaende" name="Likviditetsoversott"
              stackId="1" fill="url(#gradRed)" stroke={COLORS.aterstaende}
              strokeWidth={2}
            />
            <Area
              type="monotone" dataKey="rantefri_inlaning" name="Rantefri inlaning"
              stackId="1" fill="url(#gradAmber)" stroke={COLORS.rantefri_inlaning}
              strokeWidth={2} connectNulls={false}
            />
          </AreaChart>
        </ResponsiveContainer>

        <div className="chart-legend-custom">
          <span className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: COLORS.erbjuden_volym }} />
            Erbjuden volym
          </span>
          <span className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: COLORS.aterstaende }} />
            Likviditetsoversott
          </span>
          <span className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: COLORS.rantefri_inlaning }} />
            Rantefri inlaning
          </span>
        </div>
      </div>

      <p className="source-note">
        Grafen omfattar ej aterforsakring av riksbankscertifikat eller finjusterade transaktioner.
        Likviditetsstallningen mot banksystemet kan darfor avvika fran vad som framgar av grafen.
        Kalla: Riksbanken.
      </p>
    </section>
  );
}
