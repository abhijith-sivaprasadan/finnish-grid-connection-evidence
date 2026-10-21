import type {Metadata} from "next";
import {ProxyNetworkMap} from "@/components/proxy-network-map";
export const metadata:Metadata={title:"Finnish network geography · 2024 OSM proxy",description:"Interactive ODbL-labelled 2024 OSM virtual Finnish 220/400 kV bus map, deliberately separate from Fingrid capacity claims."};
export default function ProxyMap(){return <><section className="page-hero"><div className="wrap">
<p className="eyebrow">2024 OSM SOURCE GEOGRAPHY / INDEPENDENT PROXY</p>
<h1>Explore <em>network geography.</em></h1>
<p className="lede">A clickable coordinate diagram of 107 source bus positions (104 high-voltage AC, three DC) and 137 domestic AC line graph records from the OpenStreetMap-derived PyPSA-Eur prebuilt v0.6 archive. These are not 107 verified Fingrid substations, nor present-day available capacity.</p>
</div></section><section className="section"><div className="wrap"><ProxyNetworkMap/></div></section></>}