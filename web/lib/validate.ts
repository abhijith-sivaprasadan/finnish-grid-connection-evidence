export function choice(value: string | null, allowed: readonly string[]): string | null {
  return value && allowed.includes(value) ? value : null;
}
export function boundedInt(value: string | null, fallback: number, max: number): number | null {
  if (value === null) return fallback;
  if (!/^\d+$/.test(value)) return null;
  const n=Number(value);
  return Number.isSafeInteger(n) && n >= 1 && n <= max ? n : null;
}
export function year(value:string|null): number|null {
  if(value===null) return null;
  if(!/^20\d{2}$/.test(value)) return NaN;
  return Number(value);
}
export const API_VERSION="v1";
