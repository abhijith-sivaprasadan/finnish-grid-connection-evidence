"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { GridMark } from "@/components/grid-mark";

type Status = {mode:"neon"|"compiled_snapshot"|"unavailable"; latest:string|null; ageHours:number|null};
const nav = [
  {href:"/",label:"Overview",hint:"What the evidence shows",icon:"overview",group:"START"},
  {href:"/screening",label:"Connection screen",hint:"Explore a project request",icon:"nodes",group:"START"},
  {href:"/connections",label:"Connection evidence",hint:"Recorded point estimates",icon:"nodes",group:"START"},
  {href:"/operations",label:"System operations",hint:"Historical national data",icon:"chart",group:"ANALYSE"},
  {href:"/engineering",label:"Electrical studies",hint:"AC, N−1 and sensitivity",icon:"chart",group:"ANALYSE"},
  {href:"/network-map",label:"Network geography",hint:"2024 source proxy map",icon:"nodes",group:"ANALYSE"},
  {href:"/analysis",label:"System scenarios",hint:"PyPSA sensitivity",icon:"chart",group:"ANALYSE"},
  {href:"/quality",label:"Data & quality",hint:"Coverage and revisions",icon:"check",group:"SOURCES"},
  {href:"/netherlands",label:"Netherlands pilot",hint:"Official congestion sources",icon:"chart",group:"SOURCES"},
  {href:"/stations",label:"Station archive",hint:"Historical inventory",icon:"nodes",group:"SOURCES"},
  {href:"/case-study",label:"Project walkthrough",hint:"Decisions and limitations",icon:"book",group:"ABOUT"},
  {href:"/method",label:"Methods & sources",hint:"Evidence definitions",icon:"book",group:"ABOUT"},
  {href:"/api",label:"Data API",hint:"Read-only endpoints",icon:"code",group:"ABOUT"}
] as const;
type IconName=typeof nav[number]["icon"];
function NavIcon({name}:{name:IconName}){
 const paths:Record<IconName,React.ReactNode>={
  overview:<><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
  nodes:<><circle cx="5" cy="12" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="m7 11 10-5M7 13l10 5"/></>,
  chart:<><path d="M3 3v18h18"/><path d="m6 16 5-6 4 3 5-8"/></>,
  check:<><path d="M9 4h11v16H4V9z"/><path d="m4 9 5-5"/><path d="m9 14 3 3 5-6"/></>,
  book:<><path d="M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1Z"/><path d="M12 5v15"/></>,
  code:<><path d="m8 7-5 5 5 5m8-10 5 5-5 5m-3-13-2 16"/></>
 };
 return <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6">{paths[name]}</svg>;
}
function isActivePage(path:string,href:string){return path===href||(href!=="/"&&path.startsWith(href+"/"));}
function Navigation({close}:{close?:()=>void}){
 const path=usePathname();
 return <nav className="shell-nav" aria-label="Main sections">
  {(["START","ANALYSE","SOURCES","ABOUT"] as const).map(group=><div className="shell-nav-group" key={group}>
    <p className="shell-group-label">{group}</p>
    {nav.filter(item=>item.group===group).map(item=><Link key={item.href} href={item.href}
       aria-current={isActivePage(path,item.href)?"page":undefined}
       onClick={close} className={"shell-nav-link"+(isActivePage(path,item.href)?" current":"")}>
      <span className="shell-nav-icon"><NavIcon name={item.icon}/></span>
      <span className="shell-nav-text"><strong>{item.label}</strong><small>{item.hint}</small></span>
      {isActivePage(path,item.href)&&<span className="shell-nav-indicator" aria-hidden="true"/>}
    </Link>)}
  </div>)}
 </nav>;
}
export function DashboardShell({children,status}:{children:React.ReactNode;status:Status}){
 const pathname=usePathname(),router=useRouter();
 const [menu,setMenu]=useState(false),[palette,setPalette]=useState(false),[search,setSearch]=useState("");
 const inputRef=useRef<HTMLInputElement>(null);
 useEffect(()=>{
  const key=(event:KeyboardEvent)=>{
   const element=event.target as HTMLElement|null;
   const writing=element?.tagName==="INPUT"||element?.tagName==="TEXTAREA"||element?.tagName==="SELECT"||element?.isContentEditable;
   if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==="k"){event.preventDefault();setPalette(x=>!x);}
   else if(event.key==="/"&&!writing&&!palette){event.preventDefault();setPalette(true);}
   else if(event.key==="Escape"){setPalette(false);setMenu(false);}
  };
  window.addEventListener("keydown",key);return()=>window.removeEventListener("keydown",key);
 },[palette]);
 useEffect(()=>{if(palette){inputRef.current?.focus();}},[palette]);
 useEffect(()=>{setMenu(false);},[pathname]);
 const matches=nav.filter(x=>(x.label+" "+x.hint).toLowerCase().includes(search.toLowerCase()));
 const current=nav.find(n=>n.href===pathname)??nav.find(n=>isActivePage(pathname,n.href));
 const connected=status.mode==="neon";
 const ageLabel=status.ageHours!==null?status.ageHours>=24?Math.floor(status.ageHours/24)+"d old":status.ageHours+"h old":null;
 const go=(href:string)=>{router.push(href);setPalette(false);setSearch("");};
 return <div className="app-shell">
  <a className="skip" href="#main">Skip to main content</a>
  <aside className="shell-sidebar" aria-label="Workspace navigation">
    <Link className="shell-brand" href="/" aria-label="Finnish Grid Atlas overview">
      <span className="shell-brand-icon"><GridMark size={42}/></span>
      <span><strong>Finnish Grid Atlas</strong><small>GRID EVIDENCE DEMONSTRATOR</small></span>
    </Link>
    <div className="shell-workspace"><span className="shell-workspace-dot"/><span>SOURCE-LINKED ANALYSIS</span><span className="shell-workspace-version">MVP</span></div>
    <div className="shell-nav-viewport" tabIndex={0} aria-label="Scroll through dashboard pages"><Navigation/></div>
    <div className="shell-sidebar-bottom">
      <div className="shell-source-note"><span className="shell-source-indicator"/> <strong>Source integrity first</strong>
        <p>Published estimates are not connection rights. National measurements are historical.</p>
        <Link href="/method">Evidence policy <span aria-hidden="true">↗</span></Link>
      </div>
      <a className="shell-github" href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence" target="_blank" rel="noreferrer">GitHub repository <span aria-hidden="true">↗</span></a>
    </div>
  </aside>
  {menu&&<button className="shell-mobile-backdrop" type="button" aria-label="Close menu" onClick={()=>setMenu(false)}/>}
  {menu&&<aside id="mobile-atlas-nav" className="shell-mobile-sidebar open" aria-label="Mobile workspace navigation">
    <div className="shell-mobile-header"><span>SECTIONS</span><button type="button" onClick={()=>setMenu(false)} aria-label="Close navigation">×</button></div><div className="shell-nav-viewport" tabIndex={0} aria-label="Scroll through mobile pages"><Navigation close={()=>setMenu(false)}/></div>
  </aside>}
  <div className="shell-main">
    <header className="shell-topbar">
      <div className="shell-topbar-left">
        <button className="shell-menu-button" type="button" aria-label="Open navigation" aria-controls="mobile-atlas-nav" aria-expanded={menu} onClick={()=>setMenu(true)}>☰</button>
        <span className="shell-breadcrumb-root">ATLAS</span><span className="shell-breadcrumb-slash">/</span>
        <strong>{current?.label??"Overview"}</strong>
      </div>
      <div className="shell-topbar-actions">
        <span className={"shell-db-status"+(connected?" connected":" degraded")}>
          <span className="shell-status-light"/>{connected?"Historical data · connected":status.mode==="compiled_snapshot"?"Source snapshot":"Data unavailable"}
        </span>
        <button className="shell-command-button" type="button" onClick={()=>setPalette(true)} aria-label="Search pages, keyboard shortcut Control K">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><circle cx="10.7" cy="10.7" r="6.4"/><path d="m15.4 15.4 5 5"/></svg>
          <span>Quick navigation</span><kbd>⌘ K</kbd>
        </button>
      </div>
    </header>
    <div className="shell-ribbon"><span><span className="ribbon-square"/> Independent research · not affiliated with Fingrid or a TSO</span>
      <span>{status.latest ? "Latest historical interval · "+status.latest.slice(0,10)+" UTC"+(ageLabel?" · "+ageLabel:"") : "No verified current interval available"}</span>
    </div>
    <main id="main" className="shell-page">{children}</main>
    <footer className="shell-footer"><span>Finnish Grid Atlas · Source-linked evidence demo</span><span>Indicative ≠ available connection capacity <span aria-hidden="true">·</span> <Link href="/method">Limitations</Link></span></footer>
  </div>
  {palette&&<div className="command-layer" role="presentation" onMouseDown={event=>{if(event.target===event.currentTarget){setPalette(false);setSearch("");}}}>
    <div role="dialog" aria-modal="true" aria-label="Search workspace" className="command-dialog">
      <div className="command-field"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" strokeWidth="1.8" aria-hidden="true"><circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/></svg>
        <input ref={inputRef} value={search} onChange={event=>setSearch(event.target.value)} placeholder="Find a page, source or analysis…" aria-label="Search pages"
         onKeyDown={event=>{if(event.key==="Enter"&&matches[0])go(matches[0].href);}}/>
        <button type="button" onClick={()=>{setPalette(false);setSearch("");}}>Esc</button>
      </div>
      <p className="command-caption">PAGES</p>
      <div className="command-results">{matches.length?matches.map(item=><button type="button" key={item.href} onClick={()=>go(item.href)}>
          <NavIcon name={item.icon}/><span><strong>{item.label}</strong><small>{item.hint}</small></span><span aria-hidden="true">↗</span>
        </button>):<p>No matching workspace pages.</p>}</div>
      <div className="command-help">Press Enter for first result · Esc to close · / to open</div>
    </div>
  </div>}
 </div>;
}
