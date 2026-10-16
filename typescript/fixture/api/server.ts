import type { IncomingMessage, ServerResponse } from "node:http";
import type { App } from "./app.ts";

/** Adapts an App to node:http: `http.createServer(toNodeHandler(app))`. */
export function toNodeHandler(app: App): (req: IncomingMessage, res: ServerResponse) => void {
  return (req, res) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", async () => {
      const headers: Record<string, string> = {};
      for (const [name, value] of Object.entries(req.headers)) {
        if (typeof value === "string") headers[name] = value;
        else if (Array.isArray(value)) headers[name] = value.join(", ");
      }
      const out = await app.handle({ method: req.method ?? "GET", target: req.url ?? "/", headers, body: Buffer.concat(chunks).toString("utf8") });
      for (const [name, value] of out.headers) res.setHeader(name, value);
      res.writeHead(out.status);
      res.end(out.body);
    });
  };
}
