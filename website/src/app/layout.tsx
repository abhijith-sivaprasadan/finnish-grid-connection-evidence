import type { Metadata } from "next";
import { DashboardShell } from "@/components/dashboard-shell";
import { overview } from "@/lib/repository";
import "./globals.css";

export const dynamic="force-dynamic";
export const metadata:Metadata={
  metadataBase:new URL("https://finnish-grid-atlas.vercel.app"),
  title:{default:"Finnish Grid Atlas — Independent grid research",template:"%s | Finnish Grid Atlas"},
  description:"An independent Finnish grid evidence workspace. Explore conditional connection estimates, national historical operations, completeness and source provenance.",
  robots:{index:true,follow:true},
  openGraph:{title:"Finnish Grid Atlas",description:"Independent grid evidence and connection outlook for Finland.",type:"website",siteName:"Finnish Grid Atlas"},
  twitter:{card:"summary_large_image"}
};
export default async function RootLayout({children}:{children:React.ReactNode}){
 let status:{mode:"neon"|"compiled_snapshot"|"unavailable";latest:string|null;ageHours:number|null}={
   mode:"unavailable",latest:null,ageHours:null
 };
 try{
   const state=await overview();
   const t=state.newest_operational_interval_utc?Date.parse(state.newest_operational_interval_utc):NaN;
   status={mode:state.data_mode==="neon"?"neon":"compiled_snapshot",
      latest:state.newest_operational_interval_utc,
      ageHours:Number.isFinite(t)?Math.max(0,Math.floor((Date.now()-t)/3600000)):null};
 }catch{ /* Do not misrepresent database availability. */ }
 return <html lang="en"><body><DashboardShell status={status}>{children}</DashboardShell></body></html>;
}
