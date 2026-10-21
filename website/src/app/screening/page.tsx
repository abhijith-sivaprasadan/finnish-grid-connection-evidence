import type {Metadata} from "next";
import Link from "next/link";
import {evidenceCatalogue} from "@/lib/catalogue";
import {parseScreening} from "@/lib/screening";
import {BadInput} from "@/lib/params";
import {ScreeningWorkbench} from "@/components/screening-workbench";

export const dynamic="force-dynamic";
export const metadata:Metadata={title:"Connection screening · research evidence"};
type SP=Promise<Record<string,string|string[]|undefined>>;
export default async function Screening({searchParams}:{searchParams:SP}){
 const sp=await searchParams;
 const q=new URLSearchParams();
 for(const [key,value] of Object.entries(sp)){
  if(typeof value==="string")q.set(key,value);
  else if(value!==undefined){q.set(key,"INVALID_MULTIPLE");}
 }
 let error:string|null=null;
 let initial:ReturnType<typeof parseScreening>={demand_mw:100,year:2030,direction:"consumption",voltage:"all",connection_type:"switchyard"};
 try{initial=parseScreening(q);}catch(e){error=e instanceof BadInput?e.message:"Invalid screening input";}
 let evidence:Awaited<ReturnType<typeof evidenceCatalogue>>|null=null;
 try{evidence=await evidenceCatalogue();}catch{error="The read-only evidence store is unavailable. No sample numbers were substituted.";}
 return <section className="sc-page">
  <header className="sc-hero">
    <div className="sc-eyebrow">CONNECTION ASSESSMENT / FINLAND / SOURCE QUALIFIED</div>
    <h1>Assess a <em>connection request.</em></h1>
    <p>Start with a proposed load, target year and connection arrangement. The results separate published MW estimates, engineering connection-pathway guidance and the evidence still needed for an operator enquiry.</p>
    <div className="sc-hero-links"><Link href="/connections">Inspect capacity records ↗</Link><Link href="/stations">Historical station names ↗</Link><Link href="/method">Source limitations ↗</Link></div>
  </header>
  {error&&<p className="notice warn" role="alert">{error}</p>}
  {evidence&&<ScreeningWorkbench points={evidence.stations} observations={evidence.observations} initial={initial}/>}
  <section className="sc-handoff">
   <p className="sc-eyebrow">NEXT ENGINEERING CHECK</p><h2>Before treating a point as developable</h2>
   <p>A source figure is only an initial lead. A real 100 MW load enquiry requires a precise site location, requested connection point, import profile, target commissioning date, voltage and connection configuration, reactive-power or power-factor requirements, operating flexibility and an operator-led network assessment. N-1 capability, protection, project dependencies and queue conditions remain unverified here.</p>
   <a href="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/" target="_blank" rel="noreferrer">Fingrid Grid Scope and operator caveats ↗</a>
  </section>
 </section>;
}
