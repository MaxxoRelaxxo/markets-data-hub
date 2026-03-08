import { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
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

  const chartData = timeseries.map((d) => ({
    date: d.date,
    "Tilldelad volym": d.tilldelad_volym,
    "Reserver": d.aterstaende,
    "Räntefri inlåning": d.rantefri_inlaning,
    "Finjusterade transaktioner": d.finjusterade,
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
        <StatCard label="Reserver" value={fmt(l.aterstaende)} unit="mdkr" delta={l.delta_aterstaende} />
        <StatCard label="Antal bud" value={String(l.antal_bud)} delta={l.delta_antal_bud} />
      </div>

      <div className="chart-card">
        <div className="chart-card-head">
          <div className="chart-card-title">Banksystemets likviditetsställning - fördelning mellan penningpolitiska instrument</div>
          <a className="export-btn" href="./data/riksbankscertifikat.csv" download="riksbankscertifikat.csv">
            Exportera CSV
          </a>
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" vertical={false} />
            <XAxis
              dataKey="date" interval={Math.floor(chartData.length / 8)}
              tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
              width={60}
            />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
            <Bar dataKey="Tilldelad volym" stackId="stack" fill="#0071B9" fillOpacity={0.85} />
            <Bar dataKey="Reserver" stackId="stack" fill="#B91E2B" fillOpacity={0.85} />
            <Bar dataKey="Finjusterade transaktioner" stackId="stack" fill="#2D7D4F" fillOpacity={0.85} />
            <Bar dataKey="Räntefri inlåning" stackId="stack" fill="#D4880A" fillOpacity={0.85} radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <div className="chart-note">
          Grafen omfattar ej återköp av riksbankscertifikat. <br />
          Källa: Riksbanken.
        </div>

        <div className="info-box">
          <div className="info-box-title">Riksbankens penningpolitiska styrsystem</div>

          <h4>Bakgrund: Varför ett nytt system 1994?</h4>
          <p>
            Räntetrappan som gällde 1985–1994 hade konstruerats för ett system med fast växelkurs, där det gällde att styra valutaflöden med tydliga och relativt stora räntesteg. När Sverige övergav den fasta växelkursen i november 1992 och Riksbanken i januari 1993 antog ett inflationsmål förändrades förutsättningarna i grunden. Under rörlig växelkurs kan små och gradvisa räntejusteringar vara att föredra, men det skapade ett strukturellt problem med räntetrappan. Om stegen gjordes tillräckligt små, exempelvis om stegens höjd förändrades från 0,25 till 0,10 procentenheter fanns en risk med att bankernas incitament att handla med varandra på dagslånemarknaden skulle försvinna. Riksbanken bedömde att det krävdes ett helt nytt system, och den 1 juni 1994 infördes räntekorridoren.
          </p>

          <h4>Räntekorridoren 1994–2019: Hur systemet fungerade</h4>
          <p>
            Räntekorridoren ersatte räntetrappans många steg med en enkel och elegant mekanism bestående av tre komponenter. Riksbanken erbjöd en stående inlåningsfacilitet, ett golv där banker med överskottslikviditet kunde placera pengar hos Riksbanken till inlåningsräntan. På motsatt sida fanns en stående utlåningsfacilitet, ett tak där banker med underskott kunde låna till utlåningsräntan från Riksbanken. Dessa två räntor bildade korridoren. Mittemellan satt reporäntan, den ränta Riksbanken satte i sina veckovisa marknadsoperationer, och som blev det operativa målet för dagslåneräntan.
          </p>
          <p>
            Systemet var självbalanserande: ingen bank vill låna dyrare än nödvändigt av Riksbanken om den kan låna billigare av en annan bank, och ingen bank vill placera billigare hos Riksbanken om den kan få mer av en motpart. Korridorens prisstruktur skapade alltså starka incitament för bankerna att jämna ut sin likviditet sinsemellan på dagslånemarknaden, och dagslåneräntan höll sig naturligt nära reporäntan i mitten. Korridorbredden var som huvudregel 150 räntepunkter – reporäntan ±0,75 procentenheter.
          </p>
          <p>
            För att hålla systemet i balans genomförde Riksbanken varje vecka penningpolitiska repor, köpte värdepapper av bankerna med avtal om återförsäljning, för att tillföra precis den mängd likviditet som krävdes. Efter en tids erfarenhet visade det sig att dagslåneräntan inte i genomsnitt motsvarade reporäntan när den fluktuerade fritt inom räntekorridoren. Dessa variationer tolkades ibland som policysignaler, vilket skapade oklarhet och gjorde att Riksbanken behövde stabilisera räntan. Som komplement till reporna introducerades 1995 finjusterande transaktioner varje bankdag mellan klockan 16 och 16:40, där Riksbanken erbjöd kredit eller inlåning till reporäntan ±0,10 procentenheter för att stabilisera dagslåneräntan om banksystemet hamnade i obalans mot slutet av dagen. Detta gällde dock endast upp till banksystemets totala underskott eller överskott. Tilldelningen skedde efter principen &quot;först till kvarn&quot; och var manuell – personal ringde in och Riksbanken hanterade varje transaktion för hand.
          </p>
          <p>
            Från slutet av 1992 började Riksbanken dessutom emittera egna riksbankscertifikat, kortfristiga skuldebrev som ett alternativt dräneringsverktyg. Dessa blev det dominerande instrumentet från 2008, då banksystemet gick in i ett strukturellt likviditetsöverskott till följd av Riksbankens värdepappersköp och valutareservfinansiering. I stället för att tillföra likviditet via repor dränerade Riksbanken systemet varje vecka genom att erbjuda bankerna möjligheten att placera i certifikat till reporäntan.
          </p>
          <p>
            Finanskrisen 2008 testade systemet under press. När kreditmarknaderna frös lanserade Riksbanken en extraordinär lånefacilitet med tre månaders löptid, och bankerna lånade 100 miljarder kronor i den första auktionen den 6 oktober. Banksystemet gick från underskott till massivt överskott i ett slag, och Riksbanken fick anpassa sina marknadsoperationer ett tydligt bevis på systemets flexibilitet. Korridorbredden justerades också tillfälligt: när reporäntan sänktes till 0,50 procent i april 2009 drogs korridoren samman till 100 räntepunkter för att undvika negativ inlåningsränta, och när reporäntan nådde −0,10 procent 2015 accepterade Riksbanken en negativ inlåningsränta och återgick till full bredd.
          </p>

          <h4>Reformen 2019–2022: Varför och hur</h4>
          <p>
            Trots att räntekorridoren fungerat väl i över två decennier tvingade tre strukturella förändringar i omvärlden Riksbanken att reformera systemet.
          </p>
          <p>
            Det första problemet var skalbarhet. De dagliga finjusteringstransaktionerna var manuella och fungerade acceptabelt med 10–13 motparter, men intresset för att bli penningpolitisk motpart till Riksbanken ökade kraftigt. Med upp till 30 nya potentiella motparter på fem års sikt skulle de operationella riskerna bli oacceptabla.
          </p>
          <p>
            Det andra problemet var autonoma faktorer, faktorer som påverkade banksystemets likviditet men som Riksbanken inte kontrollerade. Dessa var exempelvis allmänhetens kontantefterfrågan, centrala motparters inlåningsfaciliteter och avsättningar till Bankgirot för omedelbar betalningsavveckling. Varje ny sådan tjänst krävde ytterligare manuella begränsningar för att finjusteringarna skulle fungera som avsett.
          </p>
          <p>
            Det tredje problemet var längre öppettider i betalningssystemet RIX. Den 14 oktober 2019 förlängde RIX sina öppettider med en timme till kl. 18:00. Eftersom finjusteringarna måste genomföras en timme innan stängning hade personal behövt stanna ännu längre varje kväll, och på sikt vill Riksbanken möjliggöra betalningsavveckling i riksbankspengar dygnet runt vilket är oförenligt med dagliga manuella finjusteringar.
          </p>
          <p>
            Lösningen blev att göra korridoren så smal att finjusteringarna blir onödiga. Med en korridor på bara 20 räntepunkter, mot tidigare 150 är marginalkostnaden för att hamna på fel sida försumbar, och dagslåneräntan håller sig naturligt nära styrräntan utan manuell styrning. Systemet blir självbalanserande. Reformen genomfördes i fyra konkreta steg:
          </p>
          <ol>
            <li>Den 9 oktober 2019 avvecklades de finjusterande transaktionerna och inlåningsräntan sänktes till styrräntan −0,10 procent.</li>
            <li>Den 2 juli 2020 sänktes utlåningsräntan till styrräntan +0,10 procent – korridoren var nu 20 räntepunkter bred.</li>
            <li>Den 8 juni 2022 inrättades en ny kompletterande likviditetsfacilitet för utlåning mot sekundära säkerheter till styrräntan +0,75 procent, och samtidigt skärptes säkerhetskraven för den ordinarie utlåningsfaciliteten till enbart primär säkerhetsmassa – statspapper och centralbanksfordringar.</li>
            <li>Slutligen byttes begreppet &quot;reporänta&quot; ut mot det mer träffande &quot;styrränta&quot;, eftersom Riksbanken länge emitterat certifikat snarare än genomfört repor.</li>
          </ol>

          <h4>Det färdiga systemet: Tre nivåer av likviditetsförsörjning</h4>
          <p>
            Det reformerade systemet har en tydlig hierarki. I normalläget placerar eller lånar banker sin överskotts- eller underskottslikviditet automatiskt i stående inlånings- respektive utlåningsfaciliteten till styrräntan ±0,10 procent, utan att behöva kontakta Riksbanken. Saldot på deras konto i RIX hamnar automatiskt rätt vid stängning. Om en bank saknar tillräckliga primära säkerheter för att täcka sitt lånebehov finns den kompletterande likviditetsfaciliteten som sista utväg, till styrräntan +0,75 procent mot sekundära säkerheter som säkerställda obligationer och statsgaranterade papper. Riksbanken styr likviditetsvolymen i systemet via veckovisa emissioner av riksbankscertifikat, begränsade till ungefär banksystemets totala likviditetsöverskott, vilket håller dagslåneräntan nära styrräntan.
          </p>
          <p>
            Den centrala logiken i säkerhetsuppdelningen är att Riksbanken prissätter lån mot de säkraste tillgångarna nära styrräntan och låter marknaden självständigt sätta relativpriset mot mer riskfyllda säkerheter – en princip som stärker marknadens egna incitament att hantera och prissätta risk.
          </p>

          <h4>Huvudtyper av styrsystem</h4>

          <h5>Korridorsystem</h5>
          <p>
            Kännetecknen för ett korridorsystem är centralbanken stabiliserar marknadsräntor inom styrsystemets räntekorridor som utgörs av in-och utlåningsräntor över natten. Centralbankens huvudsakliga styrränta ligger vanligtvis i mitten av korridoren med samma avstånd till inlåningsräntan (golv) som till utlåningsräntan (tak). Banker med överskottslikviditet och banker med underskott har incitament att handla med varandra till en ränta mellan golv och tak, istället för att gå via centralbanken. Centralbanken balanserar systemet genom marknadsoperationer. Fördelarna med ett korridorsystem att det inte kräver en stor balansräkning, stimulerar interbankhandel. Bredden på korridoren är en avvägning. En smal korridor ger låg volatilitet men svagare incitament för marknadsaktivitet, men en bred korridor ger starkare incitament men mer rörelse i räntan.
          </p>

          <h5>Golvsystem</h5>
          <p>
            Centralbanken håller ett stort likviditetsöverskott i systemet. Alla banker har ett placeringsbehov, så dagslåneräntan pressas ner till inlåningsräntan som utgör golvet. Styrräntan är oftast samma som inlåningsräntan. Fördelar med ett golvsystem är att dagslåneräntan inte blir så volatil, centralbanken behöver inte prognostisera dagliga likviditetsflöden lika noggrant. Nackdelar med ett golvsystem är en svag interbankmarknad, stor balansräkning med medföljande finansiella risker, och potentiell målkonflikt vid åtstramning eftersom systemet alltid kräver likviditetsöverskott. Golvsystem blev vanligare efter centralbankernas storskaliga tillgångsköp.
          </p>

          <h5>Kvotsystem</h5>
          <p>
            En hybrid mellan korridor-och golvsystem. Centralbanken sätter en kvot per motpart, inlåning upp till kvoten får styrräntan, överskjutande volymer får en sämre ränta. Det skapar incitament att handla på interbankmarknaden (likt korridorsystem) men fungerar med likviditetsöverskott (likt golvsystem). Blev vanligare under perioden med negativa räntor eftersom det möjliggjorde generös ersättning till bankerna på genomsnittsnivå utan att påverka marginalprissättningen. Nackdelarna med ett kvotsystem är att kvoterna kräver prognoser och innebär ett visst mått av godtycke.
          </p>
        </div>
      </div>
    </div>
  );
}
