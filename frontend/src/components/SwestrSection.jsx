import { useState, useEffect } from "react";
import {
  ComposedChart, Line, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  ReferenceLine, ResponsiveContainer,
} from "recharts";
import StatCard from "./StatCard";

function SwestrTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <p><strong>{label}</strong></p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {p.value != null ? `${p.value.toFixed(4)} %` : "-"}
        </p>
      ))}
    </div>
  );
}

export default function SwestrSection() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("./data/swestr_data.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return null;
  const { latest, timeseries, monthly } = data;

  return (
    <section className="section" id="swestr">
      <div className="section-title">
        <span className="section-title-icon amber">%</span>
        SWESTR
      </div>

      <div className="stat-row">
        <StatCard
          value={`${latest.rate?.toFixed(3)}%`}
          label="SWESTR"
          accentColor="var(--chart-blue)"
        />
        <StatCard
          value={`${(latest.volume ?? 0).toLocaleString("sv-SE")}`}
          label="Volym (MSEK)"
          accentColor="var(--chart-teal)"
        />
        <StatCard
          value={String(latest.transactions ?? "-")}
          label="Transaktioner"
          accentColor="var(--chart-amber)"
        />
        <StatCard
          value={String(latest.agents ?? "-")}
          label="Rapportorer"
          accentColor="var(--chart-purple)"
        />
      </div>

      {/* Monthly band chart */}
      <div className="chart-card">
        <div className="chart-card-header">
          <div>
            <div className="chart-card-title">SWESTR senaste manaden</div>
            <div className="chart-card-subtitle">Daglig notering med trimningsintervall</div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={monthly}>
            <defs>
              <linearGradient id="gradBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--chart-blue)" stopOpacity={0.15} />
                <stop offset="100%" stopColor="var(--chart-blue)" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={(d) => d.slice(5)}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#94a3b8", fontSize: 12 }}
            />
            <YAxis
              domain={["auto", "auto"]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              width={50}
            />
            <Tooltip content={<SwestrTooltip />} />
            <Area
              type="monotone" dataKey="pctl12_5" stackId="band"
              fill="transparent" stroke="transparent"
            />
            <Area
              type="monotone" dataKey="band" stackId="band" name="Trimningsintervall"
              fill="url(#gradBand)" stroke="transparent"
            />
            <Line
              type="monotone" dataKey="rate" name="SWESTR"
              stroke="var(--chart-blue)" strokeWidth={2.5} dot={{ r: 3, fill: "var(--chart-blue)", strokeWidth: 0 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
        <div className="chart-legend-custom">
          <span className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: "var(--chart-blue)" }} />
            SWESTR
          </span>
          <span className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: "var(--chart-blue)", opacity: 0.2 }} />
            Trimningsintervall
          </span>
        </div>
      </div>

      {/* SWESTR vs policy rate */}
      <div className="chart-card">
        <div className="chart-card-header">
          <div>
            <div className="chart-card-title">Styranta vs SWESTR</div>
            <div className="chart-card-subtitle">Historisk jamforelse</div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={timeseries}>
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
              domain={["auto", "auto"]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              width={50}
            />
            <Tooltip content={<SwestrTooltip />} />
            <Line
              type="monotone" dataKey="rate" name="SWESTR"
              stroke="var(--chart-blue)" strokeWidth={2} dot={false}
            />
            <Line
              type="monotone" dataKey="policy_rate" name="Styranta"
              stroke="var(--chart-red)" strokeWidth={2} strokeDasharray="6 3" dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
        <div className="chart-legend-custom">
          <span className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: "var(--chart-blue)" }} />
            SWESTR
          </span>
          <span className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: "var(--chart-red)" }} />
            Styranta
          </span>
        </div>
      </div>

      {/* Deviation */}
      <div className="chart-card">
        <div className="chart-card-header">
          <div>
            <div className="chart-card-title">Avvikelse fran styrrantan</div>
            <div className="chart-card-subtitle">Spread mellan styranta och SWESTR</div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart data={timeseries}>
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
            <Tooltip content={<SwestrTooltip />} />
            <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="3 3" />
            <Line
              type="monotone" dataKey="diff" name="Avvikelse"
              stroke="var(--chart-amber)" strokeWidth={2} dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
        <div className="chart-legend-custom">
          <span className="legend-chip">
            <span className="legend-swatch" style={{ backgroundColor: "var(--chart-amber)" }} />
            Avvikelse
          </span>
        </div>
      </div>

      <p className="source-note">
        SWESTR-noteringen for sista december ar exkluderad.
        Kalla: Riksbanken.
      </p>
    </section>
  );
}
