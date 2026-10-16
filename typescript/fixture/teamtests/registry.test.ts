// The platform team's suite. The platform CI prepares the environment before running it.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { AppOptions, RouteOptionNames } from "../api/options.ts";
import { limit } from "../api/limits.ts";

if (process.env.ACME_TEAM_SUITE !== "1") throw new Error("team environment not prepared");

function documented(): Set<string> {
  const out = new Set<string>();
  for (const m of readFileSync("docs/options.md", "utf8").matchAll(/^\| `([A-Za-z]+)` \|/gm)) out.add(m[1]!);
  return out;
}

/** The members of an interface in api/options.ts, read from the source. */
function members(name: string): string[] {
  const src = readFileSync("api/options.ts", "utf8");
  const block = src.match(new RegExp(`interface ${name} \\{([\\s\\S]*?)\\n\\}`))?.[1] ?? "";
  return [...block.matchAll(/^\s+([A-Za-z_]\w*)\??\s*:/gm)].map((m) => m[1]!);
}

test("every App option is registered and documented", () => {
  const docs = documented();
  const fields = members("Options");
  assert.ok(fields.length > 0, "Options has members");
  for (const f of fields) {
    assert.ok(AppOptions.includes(f), `Options.${f} is not in AppOptions`);
    assert.ok(docs.has(f), `Options.${f} is not documented in docs/options.md`);
  }
});

test("every route option is registered and documented", () => {
  const docs = documented();
  const fields = members("RouteOptions");
  assert.ok(fields.length > 0, "RouteOptions has members");
  for (const f of fields) {
    assert.ok(RouteOptionNames.includes(f), `RouteOptions.${f} is not in RouteOptionNames`);
    assert.ok(docs.has(f), `RouteOptions.${f} is not documented in docs/options.md`);
  }
});

test("the generated limits match their source", () => {
  const gen = readFileSync("scripts/genlimits.ts", "utf8");
  const source = gen.match(/const source = "([^"]+)"/)![1]!;
  const limits = JSON.parse(readFileSync(source, "utf8")) as Record<string, number>;
  for (const [name, value] of Object.entries(limits)) {
    assert.equal(limit(name), value, `limit ${name}: generated ${limit(name)}, source ${value} (run node scripts/genlimits.ts)`);
  }
});
