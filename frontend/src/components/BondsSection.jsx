import { useState, useEffect, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, CartesianGrid,
  ResponsiveContainer,
} from "recharts";

const PALETTE = [
  "var(--chart-blue)", "var(--chart-red)", "var(--chart-amber)",
  "var(--chart-green)", "var(--chart-purple)", "var(--chart-teal)",
  "var(--chart-pink)", "var(--chart-cyan)",
];

const PALETTE_RAW = [
  "#0ea5e9", "#f43f5e", "#f59e0b",
  "#10b981", "#8b5cf6", "#14b8a6",
  "#ec4899", "#06b6d4",
];

function BondTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="custom-tooltip">
      <p><strong>{d.date}</strong></p>
      <p>Obligation: {d.lan}</p>
      <p>Bid-to-cover: {d.bid_to_cover?.toFixed(2)}</p>
      <p>Budvolym: {d.budvolym?.toLocaleString("sv-SE")} Mkr</p>
      <p>Tilldelad: {d.tilldelad?.toLocaleString("sv-SE")} Mkr</p>
      <p>Lopetid: {d.lopetid?.toFixed(1)} ar</p>
    </div>
  );
}

function BondChart({ title, subtitle, data }) {
  const uniqueLans = useMemo(
    () => [...new Set(data.map((d) => d.lan))].sort(),
    [data],
  );
  const colorMap = useMemo(
    () => Object.fromEntries(uniqueLans.map((l, i) => [l, PALETTE_RAW[i % PALETTE_RAW.length]])),
    [uniqueLans],
  );

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <div>
          <div className="chart-card-title">{title}</div>
          {subtitle && <div className="chart-card-subtitle">{subtitle}</div>}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={data}>
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
            width={40}
          />
          <Tooltip content={<BondTooltip />} />
          <Bar dataKey="bid_to_cover" radius={[3, 3, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={colorMap[entry.lan]} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="chart-legend-custom">
        {uniqueLans.map((lan, i) => (
          <span key={lan} className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: PALETTE_RAW[i % PALETTE_RAW.length] }} />
            {lan}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function BondsSection() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("./data/bonds_data.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return null;

  return (
    <section className="section" id="bonds">
      <div className="section-title">
        <span className="section-title-icon green">&#x25B3;</span>
        Statsobligationer
      </div>

      <BondChart
        title="Nominella statsobligationer (SGB)"
        subtitle="Bid-to-cover per auktion"
        data={data.sgb}
      />

      <BondChart
        title="Reala statsobligationer (SGB IL)"
        subtitle="Bid-to-cover per auktion"
        data={data.sgb_il}
      />

      <p className="source-note">
        Misslyckade auktioner (tilldelad volym = 0) ar exkluderade.
        Kalla: Riksbanken / Riksgalden.
      </p>
    </section>
  );
}
