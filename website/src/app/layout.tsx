import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Finnish Grid Atlas — Evidence-based electricity grid research",
    template: "%s | Finnish Grid Atlas",
  },
  description: "Explore source-linked Finnish grid connection outlooks and national electricity system records. An independent research platform with transparent methodology and a read-only API.",
  robots: { index: true, follow: true },
  openGraph: { title: "Finnish Grid Atlas", description: "Independent grid evidence and connection outlook for Finland.", type: "website", siteName: "Finnish Grid Atlas" },
  twitter: { card: "summary_large_image" },
};

const navigation = [
  { href: "/", label: "Overview" },
  { href: "/connections", label: "Connection outlook" },
  { href: "/operations", label: "System data" },
  { href: "/method", label: "Methodology" },
  { href: "/api", label: "API" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>
    <a className="skip" href="#main">Skip to content</a>
    <div className="utility-bar">
      <div className="wrap utility-inner">
        <span><span className="utility-dot" aria-hidden="true" />Independent research platform · Finland</span>
        <a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence" target="_blank" rel="noreferrer">View project on GitHub <span aria-hidden="true">↗</span></a>
      </div>
    </div>
    <header className="site-header">
      <div className="wrap header-inner">
        <Link href="/" className="brand" aria-label="Finnish Grid Atlas home">
          <span className="brand-mark" aria-hidden="true"><svg viewBox="0 0 42 42" width="34" height="34">
<path d="M9 28 18 9 34 17 27 34 9 28 34 17 M18 9 27 34" fill="none" stroke="white" strokeWidth="2.1" strokeLinecap="round" opacity=".82"/>
<g fill="#fff"><circle cx="9" cy="28" r="3.4"/><circle cx="18" cy="9" r="3.4"/><circle cx="34" cy="17" r="3.4"/><circle cx="27" cy="34" r="3.4"/></g>
</svg></span>
          <span className="brand-type"><strong>FINNISH GRID</strong><span>ATLAS <b>•</b> OPEN EVIDENCE</span></span>
        </Link>
        <nav className="desktop-nav" aria-label="Main navigation">
          {navigation.map(item => <Link key={item.href} href={item.href}>{item.label}</Link>)}
        </nav>
        <Link href="/connections" className="nav-action">Explore data <span aria-hidden="true">↗</span></Link>
        <details className="mobile-menu">
          <summary>Menu <span aria-hidden="true">☰</span></summary>
          <nav aria-label="Mobile navigation">
            {navigation.map(item => <Link key={item.href} href={item.href}>{item.label}<span aria-hidden="true">↗</span></Link>)}
          </nav>
        </details>
      </div>
    </header>

    <main id="main">{children}</main>

    <footer className="site-footer">
      <div className="wrap">
        <div className="footer-top">
          <div>
            <div className="footer-brand"><span className="footer-network" aria-hidden="true">◇</span> FINNISH GRID ATLAS</div>
            <h2>Clear data.<br />Careful conclusions.</h2>
            <p>Independent research into published Finnish electricity-grid evidence. Not affiliated with a transmission system operator and not an offer of grid connection.</p>
          </div>
          <div className="footer-nav-wrap">
            <div className="footer-links">
              <strong>EXPLORE</strong>
              <Link href="/connections">Connection outlook</Link>
              <Link href="/operations">National operations</Link>
              <Link href="/method">Research methodology</Link>
              <Link href="/api">Developer API</Link>
            </div>
            <div className="footer-links">
              <strong>ORIGINAL SOURCES</strong>
              <a href="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/" target="_blank" rel="noreferrer">Fingrid Grid Scope ↗</a>
              <a href="https://data.fingrid.fi/" target="_blank" rel="noreferrer">Fingrid Open Data ↗</a>
              <a href="https://transparency.entsoe.eu/" target="_blank" rel="noreferrer">ENTSO-E Transparency ↗</a>
              <a href="https://finnish-grid-atlas.streamlit.app/" target="_blank" rel="noreferrer">Original Streamlit app ↗</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom"><span>© {new Date().getUTCFullYear()} Finnish Grid Atlas · Independent research</span><span>Built for transparency, not connection guarantees.</span></div>
      </div>
    </footer>
  </body></html>;
}
