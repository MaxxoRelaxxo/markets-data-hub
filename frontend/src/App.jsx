import Header from "./components/Header";
import CertificateSection from "./components/CertificateSection";
import BondsSection from "./components/BondsSection";
import SwestrSection from "./components/SwestrSection";

export default function App() {
  return (
    <div className="page">
      <Header />
      <main className="main">
        <h1 className="section-heading">Marknadsoperationer</h1>
        <CertificateSection />
        <BondsSection />
        <SwestrSection />
      </main>
      <footer className="footer">
        <p>Kalla: Riksbanken &middot; Uppdateras automatiskt via Dagster</p>
      </footer>
    </div>
  );
}
