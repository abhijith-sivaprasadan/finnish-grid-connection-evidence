import { atlasRegions, atlasNodes, atlasEdges } from "@/lib/atlas-geography";

/**
 * Geographic overview based on public-domain Natural Earth boundaries.
 * Decorative lines and dots are NOT transmission topology or actual substations.
 * The separate /connections catalogue is the source for named sample points.
 */
export function NetworkVisual() {
  return <div className="network-panel">
    <div className="network-head">
      <span><span className="network-light" aria-hidden="true" /> FINLAND / REGIONAL CONTEXT</span>
      <span>OPEN EVIDENCE ATLAS</span>
    </div>
    <svg className="network-visual" viewBox="100 100 550 485" preserveAspectRatio="xMidYMid meet"
      role="img" aria-label="Simplified geographic boundaries: Finland with Sweden to the west, Norway to the northwest, Russia to the east, Åland and the Baltic Sea in the southwest. Decorative blue network overlay is not transmission-grid topology or actual substation locations.">
      <defs>
        <linearGradient id="atlasLand" x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#fff"/><stop offset="1" stopColor="#b6dfff"/>
        </linearGradient>
      </defs>
      <path d={atlasRegions.norway} fill="#215797" opacity=".94" stroke="#7cadde" strokeWidth="1.3"/>
      <path d={atlasRegions.sweden} fill="#194a88" opacity=".97" stroke="#73a4d5" strokeWidth="1.3"/>
      <path d={atlasRegions.russia} fill="#183e76" opacity=".97" stroke="#73a4d5" strokeWidth="1.3"/>
      <path d={atlasRegions.estonia} fill="#245f9d" opacity=".97" stroke="#73a4d5" strokeWidth="1.3"/>
      <path d={atlasRegions.finland} fill="url(#atlasLand)" stroke="#eefaff" strokeWidth="3.2" strokeLinejoin="round"/>
      {atlasEdges.map(([a,b],i)=><path key={i}
        d={`M${atlasNodes[a].x} ${atlasNodes[a].y} L${atlasNodes[b].x} ${atlasNodes[b].y}`}
        fill="none" stroke="#1471c8" strokeWidth="3" strokeLinecap="round" opacity=".8"/>)}
      {atlasNodes.map((n,i)=><g key={i}>
        <circle cx={n.x} cy={n.y} r="10" fill="#e1f3ff" stroke="#4384ca" strokeWidth="2"/>
        <circle cx={n.x} cy={n.y} r="5.4" fill="#0a5ead"/>
      </g>)}
      <circle cx="273.8" cy="529" r="3.7" fill="#e7f8ff"/>
      <g fill="#9fcef3" fontFamily="Arial, sans-serif" fontSize="15" fontWeight="700" letterSpacing="1.5">
        <text x="166" y="398">SWEDEN</text>
        <text x="549" y="335">RUSSIA</text>
        <text x="173" y="551" fontSize="12">BALTIC SEA</text>
        <text x="253" y="520" fontSize="11">ÅLAND</text>
      </g>
    </svg>
    <div className="network-foot">
      <span><span className="foot-square" aria-hidden="true" /> NATURAL EARTH · SIMPLIFIED GEOGRAPHY</span>
      <span>NETWORK IS ILLUSTRATIVE</span>
    </div>
  </div>;
}
