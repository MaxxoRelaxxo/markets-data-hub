import Header from "./components/Header";
import CertificateSection from "./components/CertificateSection";
import BondsSection from "./components/BondsSection";
import SwestrSection from "./components/SwestrSection";

export default function App() {
  return (
    <div className="page">
      <Header />
      <main className="main">
        <h1 className="page-heading">Marknadsoperationer</h1>
        <p className="page-heading-sub">Riksbankens marknadsoperationer och penningpolitiska instrument</p>
        <CertificateSection />
        <BondsSection />
        <SwestrSection />
      </main>
      <footer className="footer">
        <div className="footer-inner">
          <span>Kalla: Riksbanken</span>
          <span className="footer-divider">&middot;</span>
          <span>Uppdateras automatiskt via Dagster</span>
        </div>
      </footer>
    </div>
  );
}
