import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Finnish Grid Atlas · Evidence for connection screening", template: "%s · Finnish Grid Atlas" },
  description: "Source-traceable Finnish grid connection estimates and operational time series. Independent research — not an operator connection offer.",
  robots: { index: true, follow: true },
};
export default function RootLayout({children}:{children:React.ReactNode}) {
  return <html lang="en"><body>
    <a className="skip" href="#main">Skip to content</a>
    <header className="site-header">
      <div className="wrap header-inner">
        <Link href="/" className="brand"><span className="brand-mark">FG</span>
          <span>finnish<strong>grid</strong>atlas</span></Link>
        <span className="header-note">Open evidence · Finland</span>
        <nav aria-label="Main navigation">
          <Link href="/">Overview</Link>
          <Link href="/connections">Connections</Link>
          <Link href="/operations">System data</Link>
          <Link href="/method">Method &amp; limits</Link>
          <Link href="/api">REST API</Link>
        </nav>
      </div>
    </header>
    <main id="main">{children}</main>
    <footer className="site-footer"><div className="wrap footer-grid">
      <div><span className="eyebrow inverse">Finland · independent research</span>
        <h2>Evidence first.<br/><em>Claims within limits.</em></h2>
        <p>A reproducible screening demonstrator, not a connection offer,
          grid-operator endorsement or engineering feasibility study.</p></div>
      <div className="footer-links">
        <a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence" target="_blank" rel="noreferrer">Source code ↗</a>
        <a href="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/" target="_blank" rel="noreferrer">Fingrid Grid Scope ↗</a>
        <a href="https://data.fingrid.fi/" target="_blank" rel="noreferrer">Fingrid Open Data ↗</a>
        <a href="https://transparency.entsoe.eu/" target="_blank" rel="noreferrer">ENTSO-E Transparency ↗</a>
        <a href="https://finnish-grid-atlas.streamlit.app/" target="_blank" rel="noreferrer">Original Streamlit app ↗</a>
      </div></div></footer>
  </body></html>;
}
