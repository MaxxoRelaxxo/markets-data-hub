import { useState, useEffect, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, CartesianGrid,
  ReferenceLine, ResponsiveContainer, Legend,
} from "recharts";
import StatCard from "./StatCard";

const PALETTE = ["#0071B9", "#B91E2B", "#D4880A", "#2D7D4F", "#7C3AED", "#0891B2", "#C026D3", "#059669"];


function BondTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="tt">
      <div className="tt-label">{d.date}</div>
      <div className="tt-row">
        <span className="tt-name">Lån:</span>
        <span className="tt-val">{d.lan}</span>
      </div>
      <div className="tt-row">
        <span className="tt-name">Bid-to-cover:</span>
        <span className="tt-val">{d.bid_to_cover?.toFixed(2).replace(".", ",")}</span>
      </div>
      <div className="tt-row">
        <span className="tt-name">Budvolym:</span>
        <span className="tt-val">{d.budvolym?.toLocaleString("sv-SE")} Mkr</span>
      </div>
      <div className="tt-row">
        <span className="tt-name">Tilldelad:</span>
        <span className="tt-val">{d.tilldelad?.toLocaleString("sv-SE")} Mkr</span>
      </div>
      <div className="tt-row">
        <span className="tt-name">Lopetid:</span>
        <span className="tt-val">{d.lopetid?.toFixed(1).replace(".", ",")} ar</span>
      </div>
    </div>
  );
}

export default function BondsSection() {
  const [data, setData] = useState(null);
  const [bondType, setBondType] = useState("sgb");

  useEffect(() => {
    fetch("./data/bonds_data.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  const filtered = data ? (data[bondType] || []) : [];
  const sorted = [...filtered].sort((a, b) => a.date.localeCompare(b.date));

  const uniqueLans = useMemo(
    () => [...new Set(sorted.map((d) => d.lan))].sort(),
    [bondType, data],
  );
  const colorMap = useMemo(
    () => Object.fromEntries(uniqueLans.map((l, i) => [l, PALETTE[i % PALETTE.length]])),
    [uniqueLans],
  );

  const last = sorted[sorted.length - 1];
  const avgBtc = sorted.length
    ? (sorted.reduce((s, d) => s + d.bid_to_cover, 0) / sorted.length)
    : 0;

  if (!data) return null;

  return (
    <div>
      <div className="section-header">
        <div className="section-accent" />
        <h2 className="section-title">Statsobligationer</h2>
        <p className="section-sub">Bid-to-cover per auktion</p>
      </div>

      <div className="stat-row">
        <StatCard label="Senaste B/C" value={last?.bid_to_cover?.toFixed(2).replace(".", ",") ?? "\u2013"} />
        <StatCard label="Genomsnitt B/C" value={avgBtc.toFixed(2).replace(".", ",")} />
        <StatCard label="Senaste tilldelning" value={last ? Math.round(last.tilldelad).toLocaleString("sv-SE") : "\u2013"} unit="Mkr" />
        <StatCard label="Senaste löptid" value={last?.lopetid?.toFixed(1).replace(".", ",") ?? "\u2013"} unit="ar" />
      </div>

      <div className="chart-card">
        <div className="chart-card-head">
          <div>
            <div className="chart-card-title">
              Bid-to-cover {"\u2013"} {bondType === "sgb" ? "Nominella" : "Reala"} Statsobligationer
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <div className="toggle-group">
              <button
                className={`toggle-btn ${bondType === "sgb" ? "active" : ""}`}
                onClick={() => setBondType("sgb")}
              >SGB</button>
              <button
                className={`toggle-btn ${bondType === "sgb_il" ? "active" : ""}`}
                onClick={() => setBondType("sgb_il")}
              >SGB IL</button>
            </div>
            <a
              className="export-btn"
              href={`./data/statsobligationer_${bondType}.csv`}
              download={`statsobligationer_${bondType}.csv`}
            >
              Exportera CSV
            </a>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={sorted} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={(d) => d.slice(0, 7)}
              interval={Math.max(1, Math.floor(sorted.length / 12))}
              tick={{ fontSize: 10, fill: "var(--muted)" }} tickLine={false} axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
              domain={[0, "auto"]}
            />
            <Tooltip content={<BondTooltip />} />
            <ReferenceLine y={2.0} stroke="#D4880A" strokeDasharray="4 2" strokeWidth={1.5} />
            <Bar dataKey="bid_to_cover" radius={[3, 3, 0, 0]}>
              {sorted.map((entry, i) => (
                <Cell key={i} fill={colorMap[entry.lan]} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <div className="chart-legend">
          {uniqueLans.map((lan) => (
            <span key={lan} className="legend-item">
              <span className="legend-dot" style={{ background: colorMap[lan] }} />
              Lån {lan}
            </span>
          ))}
        </div>

        <div className="chart-note">
          Misslyckade auktioner (tilldelad volym = 0) ar exkluderade. <br />
          Källa: Riksbanken/Riksgalden.
        </div>
      

      <div className="info-box">
        <div className="info-box-title">Om försäljning av statsobligationer</div>
        <p>
          Riksbanken beslutade i februari 2023 att börja sälja statsobligationer 
          från april samma år, med efterföljande beslut om ökad försäljningstakt i 
          juni 2023 och februari 2024. Syftet är att främja välfungerande marknader 
          och minska finansiella risker på balansräkningen utan att störa inflationsmålet 
          på 2 procent. Till följd av detta minskar obligationsinnehavet snabbare än vad 
          enbart förfall skulle innebära.
        </p>
        <p>
          Försäljningarna sker via återkommande auktioner där Riksbankens penningpolitiska 
          motparter och Riksgäldskontorets återförsäljare kan delta. Investerare som vill 
          delta lägger bud via de motparter som anmält intresse. Obligationerna tilldelas 
          de budgivare som lämnar bäst bud.
        </p>
        </div>
      </div>
    </div>
  );
}
