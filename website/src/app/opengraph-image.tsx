import { ImageResponse } from "next/og";
import { atlasRegions, atlasNodes, atlasEdges } from "@/lib/atlas-geography";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "Finnish Grid Atlas. Independent grid evidence and connection outlook. Geographic context for Finland, Sweden, Russia and the Baltic Sea, with illustrative network overlay.";

export default function OpenGraphImage() {
  return new ImageResponse(
    <div style={{
      width:"100%",height:"100%",display:"flex",position:"relative",
      background:"linear-gradient(110deg,#061e43 0%,#07346e 68%,#0e569a 100%)",
      color:"#fff",fontFamily:"Arial, sans-serif",overflow:"hidden"
    }}>
      <div style={{display:"flex",position:"absolute",top:45,left:64,width:605,height:535,flexDirection:"column",justifyContent:"center",zIndex:2}}>
        <div style={{display:"flex",fontSize:18,fontWeight:700,letterSpacing:2,color:"#8dccff",marginBottom:37}}>
          INDEPENDENT ENERGY SYSTEM RESEARCH
        </div>
        <div style={{display:"flex",fontSize:83,fontWeight:800,letterSpacing:-3,lineHeight:1.08,flexDirection:"column"}}>
          <span>Finnish</span><span style={{color:"#c1e2ff"}}>Grid Atlas</span>
        </div>
        <div style={{display:"flex",marginTop:38,fontSize:25,color:"#e4f1ff",lineHeight:1.48,flexDirection:"column"}}>
          <span>Grid connection evidence.</span><span>Source-linked national context.</span>
        </div>
        <div style={{display:"flex",marginTop:43,fontSize:14,fontWeight:700,letterSpacing:1.3,color:"#a3c8ed"}}>
          OPEN DATA · TRACEABLE METHODS · CLEAR LIMITS
        </div>
      </div>
      <svg viewBox="0 0 780 800" width="715" height="734" style={{position:"absolute",right:-105,top:-66,opacity:.98}}>
        <defs>
          <linearGradient id="finFill" x1="0" x2="1" y1="0" y2="1">
            <stop stopColor="#f5fcff"/><stop offset="1" stopColor="#b3dcff"/>
          </linearGradient>
        </defs>
        <path d={atlasRegions.norway} fill="#1b518b" stroke="#5c8cbd" strokeWidth="1.6"/>
        <path d={atlasRegions.sweden} fill="#16467f" stroke="#5484ba" strokeWidth="1.6"/>
        <path d={atlasRegions.russia} fill="#173b73" stroke="#4d84ba" strokeWidth="1.6"/>
        <path d={atlasRegions.estonia} fill="#1b518b" stroke="#5c8cbd" strokeWidth="1.6"/>
        <path d={atlasRegions.latvia} fill="#1b518b" stroke="#5c8cbd" strokeWidth="1.6"/>
        <path d={atlasRegions.finland} fill="url(#finFill)" stroke="#e8f6ff" strokeWidth="3.5" strokeLinejoin="round"/>
        {atlasEdges.map(([a,b],i)=><path key={i} d={`M${atlasNodes[a].x} ${atlasNodes[a].y} L${atlasNodes[b].x} ${atlasNodes[b].y}`} stroke="#1269c7" strokeWidth="3.3" strokeLinecap="round" opacity=".85"/>)}
        {atlasNodes.map((n,i)=><g key={i}><circle cx={n.x} cy={n.y} r="11" fill="#fff" opacity=".92"/><circle cx={n.x} cy={n.y} r="7" fill="#0d5cae"/></g>)}

        <circle cx="273.8" cy="529" r="4" fill="#d4edff" stroke="#529cea" strokeWidth="2"/>
      </svg>
      <div style={{position:"absolute",left:736,top:290,display:"flex",fontSize:13,fontWeight:700,letterSpacing:2,color:"#a4d0fa"}}>SWEDEN</div>
      <div style={{position:"absolute",left:1094,top:240,display:"flex",fontSize:12,fontWeight:700,letterSpacing:1.5,color:"#a4d0fa"}}>RUSSIA</div>
      <div style={{position:"absolute",left:763,top:492,display:"flex",fontSize:12,fontWeight:700,letterSpacing:1.5,color:"#a4d0fa"}}>BALTIC SEA</div>
      <div style={{position:"absolute",left:814,top:407,display:"flex",fontSize:11,fontWeight:700,color:"#a4d0fa"}}>ÅLAND</div>
      <div style={{position:"absolute",bottom:19,right:32,color:"#bed7f0",fontSize:10,display:"flex"}}>
        GEOGRAPHY: NATURAL EARTH 1:110M · NETWORK DECORATIVE, NOT ACTUAL TOPOLOGY
      </div>
    </div>, size
  );
}
