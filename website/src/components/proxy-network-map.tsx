"use client";
import {useMemo,useState} from "react";
import {osmProxyNodes,osmProxyEdges,OSM_2024_MAP_SOURCE} from "@/lib/osm-2024-proxy-map-odbl";
import type {ProxyNode} from "@/lib/osm-2024-proxy-map-odbl";

const project=(node:ProxyNode)=>({
 x:75+(node.lon-21.0)*45,
 y:700-(node.lat-59.8)*57.5
});

export function ProxyNetworkMap(){
 const [voltage,setVoltage]=useState<"all"|"400"|"220">("all");
 const [selected,setSelected]=useState<number|null>(null);
 const [zoom,setZoom]=useState(1);
 const visible=useMemo(()=>osmProxyNodes.filter(n=>!n.dc && (voltage==="all"||n.kv===Number(voltage))),[voltage]);
 const validIds=useMemo(()=>new Set(visible.map(n=>n.id)),[visible]);
 const focus=selected!==null?osmProxyNodes[selected]:null;
 const boxW=520/zoom,boxH=740/zoom;
 const centre=focus&&zoom>1?project(focus):{x:260,y:370};
 const x0=centre.x-boxW/2,y0=centre.y-boxH/2;
 return <div className="grid-2" style={{alignItems:"start"}}>
  <div style={{minWidth:0}}>
   <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",gap:8,flexWrap:"wrap",marginBottom:12}}>
    <label style={{fontSize:13}}>Voltage source filter{" "}
     <select value={voltage} onChange={e=>{setVoltage(e.target.value as typeof voltage);setSelected(null);}}>
      <option value="all">220 + 400 kV AC</option><option value="400">400 kV</option><option value="220">220 kV</option>
     </select>
    </label>
    <div style={{display:"flex",alignItems:"center",gap:8}}>
     <button type="button" aria-label="Zoom out" onClick={()=>setZoom(z=>Math.max(1,z/1.4))}>−</button>
     <span style={{fontSize:12}}>{zoom.toFixed(1)}×</span>
     <button type="button" aria-label="Zoom in" onClick={()=>setZoom(z=>Math.min(4,z*1.4))}>+</button>
     <button type="button" onClick={()=>{setZoom(1);setSelected(null);}}>Reset</button>
    </div>
   </div>
   <svg role="img" aria-label="Interactive geographic scatter of OpenStreetMap-derived Finnish high-voltage proxy buses and reconstructed line links, not Fingrid-certified substations" width="100%" viewBox={x0+" "+y0+" "+boxW+" "+boxH}
    style={{background:"#10253a",borderRadius:12,border:"1px solid #43566d",display:"block",maxHeight:700}}>
    <rect x={0} y={0} width={520} height={740} fill="#10253a"/>
    {[60,62,64,66,68,70].map(lat=><g key={lat}>
      <line x1={40} x2={470} y1={700-(lat-59.8)*57.5} y2={700-(lat-59.8)*57.5} stroke="#335165" strokeWidth={.6} strokeDasharray="4 8"/>
      <text x={15} y={700-(lat-59.8)*57.5-4} fontSize={11} fill="#92aab9">{lat}°N</text>
    </g>)}
    {[22,24,26,28].map(lon=><g key={lon}>
      <line x1={75+(lon-21)*45} x2={75+(lon-21)*45} y1={55} y2={710} stroke="#335165" strokeWidth={.6} strokeDasharray="4 8"/>
      <text x={75+(lon-21)*45+3} y={724} fontSize={11} fill="#92aab9">{lon}°E</text>
    </g>)}
    {osmProxyEdges.map(([i,j],idx)=>{
      if(!validIds.has(i)||!validIds.has(j))return null;
      const a=project(osmProxyNodes[i]),b=project(osmProxyNodes[j]);
      return <line key={idx} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
       stroke={osmProxyNodes[i].kv===220?"#66c9bc":"#6d98da"} strokeWidth={selected===i||selected===j?2.6:1.15}
       strokeOpacity={(selected===i||selected===j)?0.95:0.5}/>;
    })}
    {visible.map(n=>{
      const a=project(n),active=n.id===selected;
      return <circle key={n.id} cx={a.x} cy={a.y} r={active?6:3}
        fill={n.kv===220?"#40d7a7":"#accbf4"} stroke={active?"#ffffff":"#183854"}
        strokeWidth={active?2:0.7} role="button" tabIndex={0}
        aria-label={"Select 2024 OSM proxy node "+n.id+", "+n.kv+" kilovolts"}
        onClick={()=>setSelected(n.id)}
        onKeyDown={e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();setSelected(n.id);}}}
        style={{cursor:"pointer"}}/>;
    })}
    <text x={30} y={32} fontSize={15} fill="white" fontWeight="bold">2024 OSM-derived · Finland proxy</text>
    <text x={30} y={52} fontSize={10} fill="#b6cbd9">Spatial source graph only · Not Fingrid as-built or site headroom</text>
   </svg>
  </div>
  <div style={{minWidth:0}}>
   <p className="eyebrow">Clickable approximate source points</p>
   <h3>{visible.length} source AC bus nodes</h3>
   <p>Inspect a node by clicking its point on the map. Locations are rounded from the independently source-verified 2024 OSM/PyPSA-Eur v0.6 dataset. Lines show its 137 reconstructed domestic 220/400 kV source graph records, not operator-identified equipment.</p>
   {focus&&!focus.dc? <div className="research-card" style={{marginBottom:16}}>
     <span className="kicker">Selected source record · number {focus.id+1}</span>
     <h3>OSM virtual AC bus {focus.id+1}</h3>
     <p><strong>{focus.kv} kV</strong> · Approx. {focus.lat.toFixed(3)}°N, {focus.lon.toFixed(3)}°E</p>
     <p><strong>Operator substation match:</strong> Not independently established.</p>
     <p><strong>Connection rights / available MW:</strong> Unknown.</p>
     <button type="button" onClick={()=>setSelected(null)}>Clear selection</button>
   </div> : <div className="limit-box"><p>Select one of the 2024 source points; it is not a named or source-approved Fingrid connection point.</p></div>}
   <div className="limit-box"><span className="kicker">Not the five named Grid Scope points</span>
    <p>The five **source-reviewed named** substations used by the capacity screener have no independently verified original-coordinates-to-OSM-ID crosswalk. Deliberately, they are **not pinned as matching** these proxy nodes. See the <a href="/connections">actual named connection evidence</a> separately.</p>
   </div>
   <p className="footnote">Adapted source under ODbL 1.0: © OpenStreetMap contributors and Xiong et al., <a href={OSM_2024_MAP_SOURCE} target="_blank" rel="noreferrer">PyPSA-Eur OSM prebuilt v0.6</a>. Source precision reduced to 0.001° for this visualization; 2025 operational state, full 110 kV and circuit identity remain unverified.</p>
  </div>
 </div>;
}
