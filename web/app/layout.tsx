import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "Finnish Grid Atlas · Evidence-first research", description: "Source-linked Finnish grid connection estimates and national operating context. Independent research, not connection offers.", robots:{index:true,follow:true} };
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="en"><body>{children}</body></html>}
