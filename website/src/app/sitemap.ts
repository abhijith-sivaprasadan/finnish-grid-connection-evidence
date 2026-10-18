import type { MetadataRoute } from "next";
export default function sitemap():MetadataRoute.Sitemap {return ["/","/connections","/operations","/method","/api"].map(path=>({url:"https://finnish-grid-atlas.vercel.app"+path}));}
