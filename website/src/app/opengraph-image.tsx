import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "Finnish Grid Atlas — independent grid evidence platform. Abstract connected research network, not a geographic map or physical grid topology.";

const points = [
  [70,510],[180,445],[280,485],[365,380],[475,405],[573,308],
  [675,345],[760,205],[852,287],[975,175],[1075,230],[1170,115],
  [1025,445],[1140,500],[850,495],
] as const;
const edges = [[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10],[10,11],[8,12],[12,13],[12,14],[14,6],[7,9],[5,8],[3,5]] as const;

export default function OpenGraphImage() {
  return new ImageResponse(
    <div style={{display:"flex",position:"relative",width:"100%",height:"100%",overflow:"hidden",
      background:"linear-gradient(120deg,#fff 0%,#f6fbff 52%,#eaf5ff 100%)",fontFamily:"Arial,sans-serif",color:"#061e48"}}>
      <svg viewBox="0 0 1200 630" width="1200" height="630" style={{position:"absolute",inset:0}}>
        <defs>
          <linearGradient id="wire" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#0044a3"/><stop offset="1" stopColor="#48aeff"/></linearGradient>
          <radialGradient id="bloom"><stop stopColor="#a0d8ff" stopOpacity=".65"/><stop offset="1" stopColor="#a0d8ff" stopOpacity="0"/></radialGradient>
        </defs>
        <circle cx="912" cy="326" r="360" fill="url(#bloom)" />
        <circle cx="910" cy="329" r="248" fill="none" stroke="#a5d2fa" strokeWidth="1.5" strokeDasharray="5 14"/>
        <circle cx="910" cy="329" r="325" fill="none" stroke="#bcddfb" strokeWidth="1.6"/>
        {edges.map(([a,b],i)=><path key={i} d={`M${points[a][0]} ${points[a][1]} L${points[b][0]} ${points[b][1]}`}
          fill="none" stroke="url(#wire)" strokeWidth={i===3||i===7||i===10?4:2} opacity={i%3===0?.78:.48}/>)}
        {points.map(([x,y],i)=><g key={i}>
          <circle cx={x} cy={y} r={i%4===0?15:10} fill="#fff" stroke="#a9d9ff" strokeWidth="2"/>
          <circle cx={x} cy={y} r={i%4===0?9:6} fill={i%3===0?"#0651aa":"#1585ec"}/>
        </g>)}
        <path d="M0 563 Q160 505 325 573 T650 553 T1200 550 L1200 630 L0 630Z" fill="#e1f0ff" opacity=".73"/>
      </svg>
      <div style={{position:"absolute",left:70,top:120,width:585,height:365,display:"flex",flexDirection:"column",zIndex:2}}>
        <span style={{fontSize:17,fontWeight:700,letterSpacing:2,color:"#1667b6",marginBottom:33}}>INDEPENDENT RESEARCH PLATFORM</span>
        <div style={{display:"flex",fontSize:88,fontWeight:800,letterSpacing:-4,lineHeight:1.08,flexDirection:"column"}}>
          <span>Finnish</span><span style={{color:"#096fdf"}}>Grid Atlas</span>
        </div>
        <span style={{fontSize:27,color:"#4b6686",marginTop:31,lineHeight:1.4}}>Independent grid evidence platform</span>
      </div>
      <div style={{position:"absolute",left:72,bottom:33,color:"#4b729e",fontSize:14,letterSpacing:1,fontWeight:700,display:"flex"}}>
        SOURCE-LINKED · READ-ONLY · CLEAR LIMITS
      </div>
      <div style={{position:"absolute",right:26,bottom:24,color:"#487db7",fontSize:12,fontWeight:700,display:"flex"}}>
        ABSTRACT DATA NETWORK · NOT A MAP
      </div>
    </div>,size
  );
}
