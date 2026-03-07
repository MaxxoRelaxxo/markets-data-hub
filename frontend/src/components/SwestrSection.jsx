import { useState, useEffect, useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
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
  const [error, setError] = useState(false);
  const [subTab, setSubTab] = useState("over_tid");

  useEffect(() => {
    fetch("./data/swestr_data.json")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((err) => {
        console.error("Failed to load SWESTR data:", err);
        setError(true);
      });
  }, []);

  const timeseries = data?.timeseries ?? [];
  const monthly = data?.monthly ?? [];
  const latest = data?.latest ?? {};

  const last = timeseries.length ? timeseries[timeseries.length - 1] : null;
  const prev = timeseries.length > 1 ? timeseries[timeseries.length - 2] : null;

  const swestrTicks = useMemo(() => {
    if (!timeseries.length) return [];
    const dates = timeseries.map((d) => d.date);
    const result = dates.filter((_, i) => i % 120 === 0);
    const lastDate = dates[dates.length - 1];
    if (result[result.length - 1] !== lastDate) result.push(lastDate);
    return result;
  }, [timeseries]);

  if (error) {
    return (
      <div className="info-box">
        <div className="info-box-title">Kunde inte ladda SWESTR-data</div>
        <p>Det gick inte att hämta data. Försök ladda om sidan.</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ textAlign: "center", padding: "3rem 0", color: "var(--muted)" }}>
        Laddar SWESTR-data…
      </div>
    );
  }

  if (!timeseries.length) {
    return (
      <div className="info-box">
        <div className="info-box-title">Ingen data tillgänglig</div>
        <p>SWESTR-tidsserien är tom. Data kan vara under uppdatering.</p>
      </div>
    );
  }

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
          value={latest.rate != null ? latest.rate.toFixed(3).replace(".", ",") : "\u2013"}
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
            <LineChart data={timeseries} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
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
              <Line
                type="monotone" dataKey="policy_rate" name="Styrränta"
                stroke="#B91E2B" strokeWidth={1.5} strokeDasharray="5 3" dot={false}
              />
              <Line
                type="monotone" dataKey="rate" name="SWESTR"
                stroke="#0071B9" strokeWidth={1.5} dot={false}
              />
            </LineChart>
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
            <LineChart data={monthly} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
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
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
              <Line
                type="monotone" dataKey="pctl87_5" name="Ränta vid övre trimningsgräns"
                stroke="#0071B9" strokeWidth={1} strokeDasharray="4 2" dot={false} strokeOpacity={0.5}
              />
              <Line
                type="monotone" dataKey="pctl12_5" name="Ränta vid nedre trimningsgräns"
                stroke="#0071B9" strokeWidth={1} strokeDasharray="4 2" dot={false} strokeOpacity={0.5}
              />
              <Line
                type="monotone" dataKey="rate" name="SWESTR"
                stroke="#0071B9" strokeWidth={2} dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="chart-note">
            Percentillinjerna visar spridningen mellan nedre/övre trimningsgräns och SWESTR-noteringen per dag. <br />
            Källa: Riksbanken.
          </div>
        </div>
      )}

      {subTab === "spread" && (
        <div className="chart-card">
          <div className="chart-card-title">Avvikelse från styrräntan</div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={timeseries} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
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
              <Line
                type="monotone" dataKey="diff" name="Diff SWESTR – Styrränta"
                stroke="#D4880A" strokeWidth={1.5} dot={false}
              />
            </LineChart>
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
