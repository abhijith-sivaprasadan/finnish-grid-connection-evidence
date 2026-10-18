import type { Direction, Source } from "./types";

export class BadInput extends Error {
  constructor(public readonly parameter: string, detail = "invalid value") {
    super(parameter + ": " + detail);
    this.name = "BadInput";
  }
}

export function integerParam(q: URLSearchParams, name: string, fallback: number, max: number) {
  const raw = q.get(name);
  if (raw === null || raw === "") return fallback;
  if (!/^\d+$/.test(raw)) throw new BadInput(name, "must be a nonnegative integer");
  const number = Number(raw);
  if (!Number.isSafeInteger(number) || number > max) throw new BadInput(name, "out of range");
  return number;
}

export function pageParams(q: URLSearchParams, maximum = 100) {
  const limit = integerParam(q, "limit", Math.min(50, maximum), maximum);
  const offset = integerParam(q, "offset", 0, 100000);
  if (limit < 1) throw new BadInput("limit", "must be positive");
  return { limit, offset };
}

export function directionParam(q: URLSearchParams): Direction | null {
  const direction = q.get("direction");
  if (direction === null || direction === "") return null;
  if (direction !== "consumption" && direction !== "production")
    throw new BadInput("direction", "must be consumption or production");
  return direction;
}

export function sourceParam(q: URLSearchParams): Source | null {
  const source = q.get("source");
  if (source === null || source === "") return null;
  if (source !== "fingrid" && source !== "entsoe")
    throw new BadInput("source", "must be fingrid or entsoe");
  return source;
}
export function pointParam(q: URLSearchParams): string | null {
  const point = q.get("point_id");
  if (!point) return null;
  if (!/^FI-FINGRID-[A-Z0-9-]{3,60}$/.test(point))
    throw new BadInput("point_id", "invalid point identifier");
  return point;
}
export function yearParam(q: URLSearchParams): number | null {
  const raw = q.get("year");
  if (!raw) return null;
  if (!/^\d{4}$/.test(raw)) throw new BadInput("year");
  const year = Number(raw);
  if (year < 1900 || year > 2200) throw new BadInput("year");
  return year;
}
export function intervalParam(raw: string | null, name: string, fallback: Date) {
  if (!raw) return fallback.toISOString().replace(/Z$/, "000Z");
  if (!/(Z|[+-]\d{2}:\d{2})$/.test(raw)) throw new BadInput(name, "timezone required");
  const date = new Date(raw);
  if (!Number.isFinite(date.getTime())) throw new BadInput(name, "invalid date");
  return date.toISOString().replace(/Z$/, "000Z");
}
export function operationsParams(q: URLSearchParams, now = new Date()) {
  const { limit, offset } = pageParams(q, 500);
  const source = sourceParam(q);
  const dataset = q.get("dataset_id");
  if (dataset && !["124", "74", "A65"].includes(dataset))
    throw new BadInput("dataset_id", "unsupported source dataset");
  if (dataset && source && ((dataset === "A65") !== (source === "entsoe")))
    throw new BadInput("dataset_id", "dataset and source do not match");
  const from = intervalParam(q.get("from"), "from", new Date(now.getTime()-14*86400000));
  const to = intervalParam(q.get("to"), "to", now);
  const begin = Date.parse(from), end = Date.parse(to);
  if (begin >= end || end - begin > 31*86400000)
    throw new BadInput("from/to", "window must be positive and at most 31 days");
  return { limit, offset, source, dataset: dataset || null, from, to };
}
