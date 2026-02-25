import { useState, useEffect, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
  ResponsiveContainer,
} from "recharts";

const PALETTE = ["#0071B9", "#B91E2B", "#f4a700", "#2ca02c", "#9467bd", "#8c564b", "#e377c2", "#17becf"];

function BondChart({ title, data }) {
  const uniqueLans = useMemo(
    () => [...new Set(data.map((d) => d.lan))].sort(),
    [data],
  );
  const colorMap = useMemo(
    () => Object.fromEntries(uniqueLans.map((l, i) => [l, PALETTE[i % PALETTE.length]])),
    [uniqueLans],
  );

  return (
    <div>
      <h3 className="chart-title">{title}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <XAxis
            dataKey="date"
            tickFormatter={(d) => d.slice(0, 4)}
            minTickGap={60}
          />
          <YAxis label={{ value: "Bid-to-cover", angle: -90, position: "insideLeft", offset: 10 }} />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0].payload;
              return (
                <div className="custom-tooltip">
                  <p><strong>Datum:</strong> {d.date}</p>
                  <p><strong>Obligation:</strong> {d.lan}</p>
                  <p><strong>Bid-to-cover:</strong> {d.bid_to_cover?.toFixed(2)}</p>
                  <p><strong>Budvolym (Mkr):</strong> {d.budvolym}</p>
                  <p><strong>Tilldelad (Mkr):</strong> {d.tilldelad}</p>
                  <p><strong>Lopetid (ar):</strong> {d.lopetid?.toFixed(2)}</p>
                </div>
              );
            }}
          />
          <Bar dataKey="bid_to_cover" opacity={0.7}>
            {data.map((entry, i) => (
              <Cell key={i} fill={colorMap[entry.lan]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="chart-legend-custom">
        {uniqueLans.map((lan) => (
          <span key={lan} className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: colorMap[lan] }} />
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
    <section className="section">
      <h2>Forsaljning av Statsobligationer</h2>

      <BondChart
        title="Forsaljning av Statsobligationer &ndash; Bid-to-cover per auktion"
        data={data.sgb}
      />

      <div style={{ height: 48 }} />

      <BondChart
        title="Forsaljning av Reala Statsobligationer &ndash; Bid-to-cover per auktion"
        data={data.sgb_il}
      />

      <p className="source-note">
        Anmarkning: Misslyckade auktioner (tilldelad volym = 0) ar exkluderade.<br />
        Kalla: Riksbanken/Riksgalden.
      </p>
    </section>
  );
}
