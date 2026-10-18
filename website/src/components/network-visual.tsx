/**
 * Abstract information architecture, NOT a map or electricity-network topology.
 * The three labels indicate separate analytical stages, not physical locations.
 */
export function NetworkVisual() {
  return <div className="network-panel">
    <div className="network-head"><span><span className="network-light" aria-hidden="true" /> EVIDENCE PIPELINE</span><span>INDEPENDENT RESEARCH</span></div>
    <svg className="network-visual" viewBox="0 0 540 430" role="img"
      aria-label="Conceptual evidence workflow: two source families pass through validation and provenance checks to a qualified screening result. Connections are conceptual, not physical transmission lines.">
      <defs>
        <linearGradient id="flowLine" x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#8bd6ff"/><stop offset=".5" stopColor="#36a1f0"/><stop offset="1" stopColor="#d7f2ff"/>
        </linearGradient>
        <radialGradient id="focusGlow"><stop stopColor="#60caff" stopOpacity=".28"/><stop offset="1" stopColor="#60caff" stopOpacity="0"/></radialGradient>
        <pattern id="pipelineGrid" width="29" height="29" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1.1" fill="#8bcaff" opacity=".22"/></pattern>
      </defs>
      <rect width="540" height="430" fill="url(#pipelineGrid)"/>
      <circle cx="273" cy="210" r="173" fill="none" stroke="#93cfff" strokeOpacity=".19" strokeWidth="1.5" strokeDasharray="3 11"/>
      <circle cx="273" cy="210" r="115" fill="url(#focusGlow)"/>
      <g fill="none" stroke="url(#flowLine)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <path d="M106 131 205 153 272 210 363 128 448 151"/>
        <path d="M106 295 204 277 272 210 363 301 448 280"/>
        <path d="M205 153 204 277 M363 128 363 301"/>
        <path d="M205 153 363 301 M204 277 363 128" strokeWidth="1.4" opacity=".3"/>
      </g>
      <g fill="#1a6cb5" stroke="#d9f5ff" strokeWidth="3">
        {[[106,131],[106,295],[205,153],[204,277],[363,128],[363,301],[448,151],[448,280]].map(([x,y],i)=><circle key={i} cx={x} cy={y} r={i===2||i===5?9:7}/>)}
      </g>
      <circle cx="272" cy="210" r="43" fill="#d9f4ff" fillOpacity=".12" stroke="#80ceff" strokeWidth="2"/>
      <circle cx="272" cy="210" r="27" fill="#effaff"/>
      <circle cx="272" cy="210" r="15" fill="#0d79dd"/>
      <g fill="#e6f5ff" fontFamily="Arial, sans-serif" textAnchor="middle">
        <text x="106" y="102" fontWeight="700" fontSize="11" letterSpacing="1.3">SOURCES</text>
        <text x="273" y="273" fontWeight="700" fontSize="11" letterSpacing="1.2">VERIFY</text>
        <text x="449" y="102" fontWeight="700" fontSize="11" letterSpacing="1.3">SCREEN</text>
      </g>
      <g fill="#b9dbfa" fontFamily="Arial, sans-serif" fontSize="10">
        <text x="56" y="326">Grid Scope</text>
        <text x="55" y="342">Operations</text>
        <text x="394" y="323">Provenance</text>
        <text x="394" y="339">Limitations</text>
      </g>
    </svg>
    <div className="network-foot"><span><span className="foot-square" aria-hidden="true"/> SOURCES → VALIDATION → SCREENING</span><span>CONCEPTUAL · NOT GRID TOPOLOGY</span></div>
  </div>;
}
