// Seed the team's knowledge into a local Pathrule store as path-scoped memories: exactly the items
// the claude_md arm gets as CLAUDE.md text. Each memory is typed the way the product types an
// agent's own untyped save (packages/mcp/src/tools/grounded-atoms.ts): its first paragraph as one
// fact, verbatim, when it fits a span. No hand-made structure.
// Usage (cwd = the repo, PATHRULE_HOME set): seed-pathrule.mts <items.json>
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const SRC = process.env.PR_SRC!;
const { LocalBackend } = await import(join(SRC, "packages/core/src/backend/local/local-backend.ts"));
const { captureGroundedAtom, MAX_SPAN_CHARS } = await import(join(SRC, "packages/agent-ir/src/atoms/grounded-capture.ts"));
const HOME = process.env.PATHRULE_HOME!;
const ws = readdirSync(join(HOME, "cache")).filter((d) => d !== "hook-claims")[0]!;
const store = LocalBackend.openForWorkspace(ws, process.env);
let memories = 0, atoms = 0;
for (const file of process.argv.slice(2)) {
  for (const it of JSON.parse(readFileSync(file, "utf8")) as Array<{ path: string; title: string; body: string }>) {
    const node = await store.ensureNodeForPath(ws, it.path, "folder");
    const m = await store.writeMemory({ workspaceId: ws, nodeId: node.id, title: it.title, content: it.body });
    memories += 1;
    const first = it.body.trim().split(/\n\s*\n/)[0]!.trim();
    if (first.length > 0 && first.length <= MAX_SPAN_CHARS) {
      const c = captureGroundedAtom({ kind: "context", fact: [first] }, { kind: "memory", id: m.id, title: m.title, content: m.content }, new Date().toISOString());
      if (c.ok) { await store.recordGroundedAtom(ws, c.atom); atoms += 1; }
    }
  }
}
store.close();
console.log(JSON.stringify({ workspace: ws, memories, atoms }));
