/** Deliberately abstract network mark — neither an official insignia nor transmission topology. */
export function GridMark({size=34}:{size?:number}) {
  return <svg width={size} height={size} viewBox="0 0 128 128" focusable="false" aria-hidden="true">
    <defs><linearGradient id="gridMarkLine" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#8de1ff"/><stop offset=".55" stopColor="#fff"/><stop offset="1" stopColor="#17a1ff"/></linearGradient></defs>
    <circle cx="64" cy="64" r="54" fill="none" stroke="#8ecfff" strokeOpacity=".35" strokeDasharray="16 10" strokeWidth="3"/>
    <path d="M64 24 97 44 97 84 64 104 31 84 31 44Z" fill="none" stroke="#8bccf5" strokeWidth="3" opacity=".8"/>
    <path d="M64 64V24 M64 64 97 44 M64 64 97 84 M64 64 64 104 M64 64 31 84 M64 64 31 44" fill="none" stroke="url(#gridMarkLine)" strokeWidth="6" strokeLinecap="round"/>
    <g fill="#fff" stroke="#0c81eb" strokeWidth="5">
      <circle cx="64" cy="24" r="8"/><circle cx="97" cy="44" r="8"/>
      <circle cx="97" cy="84" r="8"/><circle cx="64" cy="104" r="8"/>
      <circle cx="31" cy="84" r="8"/><circle cx="31" cy="44" r="8"/>
    </g>
    <circle cx="64" cy="64" r="17" fill="#fff"/>
    <circle cx="64" cy="64" r="11" fill="#0a85ef"/>
  </svg>;
}
