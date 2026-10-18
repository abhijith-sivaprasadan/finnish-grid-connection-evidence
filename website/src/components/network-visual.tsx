/**
 * Conceptual point-index visual. Node positions and edges are purely illustrative:
 * NOT geographic coordinates, transmission topology, or available capacity.
 */
export function NetworkVisual() {
  return <div className="network-panel">
    <div className="network-head"><span><span className="network-light" /> ATLAS / POINT INDEX</span><span>400 kV SAMPLE</span></div>
    <svg className="network-visual" viewBox="0 0 540 430" role="img"
      aria-label="Illustrative five-point connection evidence schematic; lines and positions do not represent actual grid geography or topology">
      <defs>
        <pattern id="atlasDots" width="24" height="24" patternUnits="userSpaceOnUse">
          <circle cx="1.5" cy="1.5" r="1" fill="#7fb4f5" fillOpacity=".25" />
        </pattern>
        <linearGradient id="lineBlue" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="#73bafa" stopOpacity=".88" />
          <stop offset="1" stopColor="#2c6bb8" stopOpacity=".72" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="540" height="430" fill="url(#atlasDots)" />
      <circle cx="260" cy="210" r="185" fill="none" stroke="#5c92d2" strokeOpacity=".20" />
      <circle cx="260" cy="210" r="130" fill="none" stroke="#5c92d2" strokeOpacity=".12" />
      <path d="M78 147 L248 92 L432 178 L342 323 L126 333 L78 147 L342 323 M248 92 L126 333" fill="none" stroke="url(#lineBlue)" strokeWidth="2.1" opacity=".85" />
      <path d="M78 147 L432 178 M248 92 L342 323" fill="none" stroke="#79a8e6" strokeDasharray="3 9" strokeWidth="1" opacity=".5" />
      {[
        { x: 78, y: 147 }, { x: 248, y: 92 }, { x: 432, y: 178 },
        { x: 342, y: 323 }, { x: 126, y: 333 },
      ].map((point, index) => <g key={index}>
        <circle cx={point.x} cy={point.y} r="18" fill="#77bfff" fillOpacity=".12"/>
        <circle cx={point.x} cy={point.y} r="8.5" fill="#ffffff" stroke="#8dd5ff" strokeWidth="3" />
        <circle cx={point.x} cy={point.y} r="2.3" fill="#003580" />
      </g>)}
      <g className="network-labels">
        <text x="55" y="116">VUOLIJOKI</text>
        <text x="237" y="56">ALAPITKÄ</text>
        <text x="392" y="144">ALAJÄRVI</text>
        <text x="337" y="360">SEINÄJOKI</text>
        <text x="88" y="369">UUSNIVALA</text>
      </g>
      <g transform="translate(205 196)">
        <rect x="0" y="0" width="138" height="56" rx="7" fill="#f0f7ff" stroke="#7eb2e4" strokeOpacity=".5" />
        <text x="15" y="22" fill="#164b86" fontSize="10" letterSpacing="1.2">PUBLIC EVIDENCE</text>
        <text x="15" y="43" fill="#003580" fontSize="16" fontWeight="700">5 connection points</text>
      </g>
    </svg>
    <div className="network-foot"><span><span className="foot-square" aria-hidden="true" /> PUBLICLY SOURCED SAMPLE</span><span>ILLUSTRATIVE · NOT A GRID MAP</span></div>
  </div>;
}
