import { useState, useEffect } from "react";
import {
  ComposedChart, Line, Area, XAxis, YAxis, Tooltip,
  ReferenceLine, ResponsiveContainer, Legend,
} from "recharts";
import StatCard from "./StatCard";

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
    <section className="section">
      <h2>Kort penningmarknad</h2>

      {/* Latest quote cards */}
      <h3>Swestr senaste notering</h3>
      <div className="stat-row">
        <StatCard value={`${latest.rate?.toFixed(3)} %`} label="SWESTR" />
        <StatCard value={`${(latest.volume ?? 0).toLocaleString("sv-SE")} MSEK`} label="Volym" />
        <StatCard value={String(latest.transactions ?? "-")} label="Antal transaktioner" />
        <StatCard value={String(latest.agents ?? "-")} label="Antal rapportorer" />
      </div>

      {/* Monthly band chart */}
      <h3 className="chart-title">Swestrs utveckling senaste manaden</h3>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={monthly}>
          <XAxis
            dataKey="date"
            tickFormatter={(d) => d.slice(5)}
          />
          <YAxis
            domain={["auto", "auto"]}
            label={{ value: "Ranta (%)", angle: -90, position: "insideLeft", offset: 10 }}
          />
          <Tooltip
            labelFormatter={(d) => d}
            formatter={(v, name) => [v?.toFixed(4), name]}
          />
          {/* Band between percentiles: invisible base + visible band */}
          <Area
            type="monotone" dataKey="pctl12_5" stackId="band"
            fill="transparent" stroke="transparent"
          />
          <Area
            type="monotone" dataKey="band" stackId="band" name="Trimningsintervall"
            fill="#0071B9" fillOpacity={0.2} stroke="transparent"
          />
          <Line
            type="monotone" dataKey="rate" name="SWESTR"
            stroke="#0071B9" strokeWidth={2} dot={{ r: 3 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
      <p className="source-note">
        Omradet visar spridningen mellan nedre/ovre trimningsgrans och Swestrnoteringen per dag.<br />
        Kalla: Riksbanken.
      </p>

      {/* SWESTR vs policy rate over time */}
      <h3 className="chart-title">Styranta vs Swestr</h3>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={timeseries}>
          <XAxis
            dataKey="date"
            tickFormatter={(d) => d.slice(0, 4)}
            minTickGap={60}
          />
          <YAxis
            domain={["auto", "auto"]}
            label={{ value: "Ranta (%)", angle: -90, position: "insideLeft", offset: 10 }}
          />
          <Tooltip
            labelFormatter={(d) => d}
            formatter={(v, name) => [v?.toFixed(3) + " %", name]}
          />
          <Legend verticalAlign="bottom" />
          <Line
            type="monotone" dataKey="rate" name="SWESTR"
            stroke="#0071B9" strokeWidth={1.5} dot={false}
          />
          <Line
            type="monotone" dataKey="policy_rate" name="Styranta"
            stroke="#B91E2B" strokeWidth={1.5} strokeDasharray="5 3" dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Deviation from policy rate */}
      <h3 className="chart-title">Avvikelse fran styrrantan</h3>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={timeseries}>
          <XAxis
            dataKey="date"
            tickFormatter={(d) => d.slice(0, 4)}
            minTickGap={60}
          />
          <YAxis
            label={{ value: "Diff (%)", angle: -90, position: "insideLeft", offset: 10 }}
          />
          <Tooltip
            labelFormatter={(d) => d}
            formatter={(v) => [v?.toFixed(4) + " %", "Diff Styranta - Swestr"]}
          />
          <ReferenceLine y={0} stroke="#475569" strokeDasharray="3 3" />
          <Line
            type="monotone" dataKey="diff" name="Avvikelse"
            stroke="#f4a700" strokeWidth={1.5} dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
      <p className="source-note">
        Gula linjen visar spreaden mellan styranta och Swestr. Swestr noteringen for sista december ar exkluderad.<br />
        Kalla: Riksbanken.
      </p>
    </section>
  );
}
