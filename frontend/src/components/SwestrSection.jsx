import { useState, useEffect, useMemo } from "react";
import {
  ComposedChart, Line, Area, AreaChart, XAxis, YAxis, Tooltip, CartesianGrid,
  ReferenceLine, ResponsiveContainer, Legend,
} from "recharts";
import StatCard from "./StatCard";

function RateTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tt">
      <div className="tt-label">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tt-row">
          <div className="tt-dot" style={{ background: p.color || p.stroke }} />
          <span className="tt-name">{p.name}:</span>
          <span className="tt-val">{p.value != null ? `${p.value.toFixed(4)}%` : "\u2013"}</span>
        </div>
      ))}
    </div>
  );
}

export default function SwestrSection() {
  const [data, setData] = useState(null);
  const [subTab, setSubTab] = useState("over_tid");

  useEffect(() => {
    fetch("./data/swestr_data.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return null;
  const { latest, timeseries, monthly } = data;

  const last = timeseries[timeseries.length - 1];
  const prev = timeseries.length > 1 ? timeseries[timeseries.length - 2] : null;

  const swestrTicks = useMemo(() => {
    const dates = timeseries.map((d) => d.date);
    const result = dates.filter((_, i) => i % 120 === 0);
    const lastDate = dates[dates.length - 1];
    if (result[result.length - 1] !== lastDate) result.push(lastDate);
    return result;
  }, [timeseries]);

  return (
    <div>
      <div className="section-header">
        <div className="section-accent" />
        <h2 className="section-title">Penningmarknad {"\u2013"} SWESTR</h2>
        <p className="section-sub">Swedish Short-Term Rate</p>
      </div>

      <div className="stat-row">
        <StatCard
          label="SWESTR"
          value={latest.rate?.toFixed(3).replace(".", ",")}
          unit="%"
          delta={prev ? parseFloat((last.rate - prev.rate).toFixed(4)) : undefined}
        />
        <StatCard
          label="Volym"
          value={Math.round((latest.volume ?? 0) / 1000).toLocaleString("sv-SE")}
          unit="mdkr"
        />
        <StatCard label="Transaktioner" value={String(latest.transactions ?? "\u2013")} />
        <StatCard label="Rapportörer" value={String(latest.agents ?? "\u2013")} />
      </div>

      <div className="sub-tabs">
        {[
          { id: "over_tid", label: "SWESTR över tid" },
          { id: "manad", label: "Senaste månaden" },
          { id: "spread", label: "Avvikelse" },
        ].map((t) => (
          <button
            key={t.id}
            className={`sub-tab ${subTab === t.id ? "active" : ""}`}
            onClick={() => setSubTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {subTab === "over_tid" && (
        <div className="chart-card">
          <div className="chart-card-title">Styrränta vs SWESTR</div>
          <ResponsiveContainer width="100%" height={340}>
            <AreaChart data={timeseries} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="gSwestr" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#D4880A" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#D4880A" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" />
              <XAxis
                dataKey="date" ticks={swestrTicks}
                tick={{ fontSize: 10, fill: "var(--muted)" }} tickLine={false} axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
                domain={["auto", "auto"]} width={50}
              />
              <Tooltip content={<RateTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
              <Area
                type="monotone" dataKey="policy_rate" name="Styrränta"
                stroke="#B91E2B" fill="transparent" strokeWidth={1.5} strokeDasharray="5 3"
              />
              <Area
                type="monotone" dataKey="rate" name="SWESTR"
                stroke="#0071B9" fill="url(#gSwestr)" strokeWidth={1.5}
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="chart-note">
            Sista notering för året är exkluderad. <br />
            Källa: Riksbanken.
          </div>
        </div>
      )}

      {subTab === "manad" && (
        <div className="chart-card">
          <div className="chart-card-title">
            SWESTR senaste 30 dagarna
          </div>
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={monthly} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="gBand" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0071B9" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#0071B9" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
                domain={["auto", "auto"]} width={55}
              />
              <Tooltip content={<RateTooltip />} />
              <Area
                type="monotone" dataKey="pctl87_5" name="Ovre percentil (87,5%)"
                stroke="transparent" fill="#0071B9" fillOpacity={0.12}
              />
              <Area
                type="monotone" dataKey="pctl12_5" name="Nedre percentil (12,5%)"
                stroke="transparent" fill="#fff" fillOpacity={1}
              />
              <Line
                type="monotone" dataKey="rate" name="SWESTR"
                stroke="#0071B9" strokeWidth={2} dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
          <div className="chart-note">
            Fältet visar spridningen mellan nedre/övre trimningsgräns och SWESTR-noteringen per dag. <br />
            Källa: Riksbanken.
          </div>
        </div>
      )}

      {subTab === "spread" && (
        <div className="chart-card">
          <div className="chart-card-title">Avvikelse från styrräntan</div>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={timeseries} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="gDiff" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#D4880A" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#D4880A" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" />
              <XAxis
                dataKey="date" ticks={swestrTicks}
                tick={{ fontSize: 10, fill: "var(--muted)" }} tickLine={false} axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
                domain={["auto", "auto"]} width={55}
              />
              <Tooltip content={<RateTooltip />} />
              <ReferenceLine y={0} stroke="var(--muted)" strokeDasharray="3 2" />
              <Area
                type="monotone" dataKey="diff" name="Diff SWESTR - Styrränta"
                stroke="#D4880A" fill="url(#gDiff)" strokeWidth={1.5}
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="chart-note">
            Positiva värden innebär att SWESTR noterar över styrräntan. <br />
            Källa: Riksbanken.
          </div>
        </div>
      )}
      <div className="info-box">
        <div className="info-box-title">Om SWESTR</div>
        <p>
          Swestr (Swedish krona Short Term Rate) är en transaktionsbaserad referensränta 
          som Riksbanken beräknar utifrån transaktioner som leder till inlåning utan säkerhet i svenska kronor
           som genomförs på penningmarknaden från en bankdag till nästa. 
        </p>
        <p>
          Referensräntor används som ett gemensamt riktmärke, eller ett basvärde, 
          vid prissättning av finansiella kontrakt som räntederivat, valutaderivat 
          och räntebärande värdepapper. Referensräntor används även vid prissättning 
          av lån med rörlig ränta, i Sverige främst vid lån till företag. 
          Traditionellt har så kallade interbankräntor använts som referensvärden för dessa ändamål. 
          Dessa räntor reflekterar enligt olika beräkningsmetoder de räntor som banker kräver av 
          varandra för kortfristiga lån utan säkerheter, det vill säga kostnaden för att låna pengar
           av en annan bank.Interbankräntorna har vanligen beräknats delvis baserade på bankers bud 
           eller bedömningar av en rimlig ränta för icke-säkerställd utlåning på den aktuella löptiden 
           givet rådande marknadsläge. Dessa räntor bygger alltså inte endast direkt på faktiska 
           transaktioner.
        </p>
        <p>
          Under den globala finanskrisen 2008-2009 försämrades likviditeten i interbank­låne­marknaden 
          avsevärt. Detta bidrog till en osäkerhet om huruvida de traditionella referensräntorna 
          verkligen speglade rådande marknadsförhållanden. Efter att Liborskandalen uppdagades att flera internationella banker, 
          i syfte att gynna den egna banken eller enskilda anställda, hade manipulerat referensräntan Libor.
          Dessa faktorer ledde till ett minskat globalt förtroende för de existerande referensräntorna. 
          Ett stort reformarbete påbörjades därför med syftet att stärka förtroendet och tillförlitligheten för referensräntor.
        </p>
        <p>
          Swestr började användas som referensränta i finansiella kontrakt från och med värdedag 1 september 2021, 
          det vill säga den notering som publicerades den 2 september 2021.
        </p>
        <p>Läs mer om <a href="https://www.riksbank.se/sv/statistik/swestr/" target="_blank" rel="noreferrer">Swestr</a> här.</p>
      </div>
    </div>
  );
}
