// Writes api/limits.gen.ts from config/limits.json. Run it after editing the limits list:
// node scripts/genlimits.ts
import { readFileSync, writeFileSync } from "node:fs";

const source = "config/limits.json";
const target = "api/limits.gen.ts";

const limits = JSON.parse(readFileSync(source, "utf8")) as Record<string, number>;
const names = Object.keys(limits).sort();
let out = `// Code generated from ${source} by scripts/genlimits.ts. DO NOT EDIT.\n\nexport const limits: Record<string, number> = {\n`;
for (const name of names) out += `  ${JSON.stringify(name)}: ${limits[name]},\n`;
out += "};\n";
writeFileSync(target, out);
process.stdout.write(`wrote ${target} with ${names.length} limits\n`);
