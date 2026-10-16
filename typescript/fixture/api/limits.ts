import { limits } from "./limits.gen.ts";

/** A platform limit by name; see scripts/genlimits.ts. */
export function limit(name: string): number {
  return limits[name] ?? 0;
}
