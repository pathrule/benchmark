# acme

The platform team's HTTP toolkit: an `App` with routes, options and middleware (`api/`), a
problem-format error helper, generated platform limits and a small CLI (`cli/`). Node's standard
library only (`node:test`, `node:assert`, `node:http`); no dependencies, no build step: Node 24 runs
the TypeScript files directly.

```ts
import { App, text } from "./api/index.ts";

const app = new App({ requestLog: true });
app.route("/hello", () => text(200, "hello"));
const res = await app.handle({ method: "GET", target: "/hello" });
```

- Options: `docs/options.md`
- Errors: `docs/errors.md`
- Tests: `node --test "api/*.test.ts"` (or `npm test`)
- Team suite (platform CI): `node --test "teamtests/*.test.ts"`
- Limits: edit `config/limits.json`, then `node scripts/genlimits.ts`
- CLI: `node cli/acme.ts limits <name>`
