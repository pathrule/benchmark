import { test } from "node:test";
import assert from "node:assert/strict";
import { App } from "./app.ts";
import { text } from "./http.ts";

test("an exact path matches its handler", async () => {
  const app = new App();
  app.route("/a", () => text(200, "a"));
  assert.equal((await app.handle({ method: "GET", target: "/a" })).body, "a");
});

test("an unknown path is 404", async () => {
  assert.equal((await new App().handle({ method: "GET", target: "/nope" })).status, 404);
});

test("the methods option restricts a route", async () => {
  const app = new App();
  app.route("/p", () => text(200, "ok"), { methods: ["POST"] });
  assert.equal((await app.handle({ method: "GET", target: "/p" })).status, 404);
  assert.equal((await app.handle({ method: "POST", target: "/p" })).status, 200);
});

test("a middleware wraps the handler", async () => {
  const app = new App();
  app.use(async (req, next) => {
    const res = await next(req);
    res.headers.set("X-Tagged", "yes");
    return res;
  });
  app.route("/t", () => text(200, "t"));
  assert.equal((await app.handle({ method: "GET", target: "/t" })).headers.get("X-Tagged"), "yes");
});

test("oversized headers answer 431", async () => {
  const app = new App({ maxHeaderBytes: 10 });
  assert.equal((await app.handle({ method: "GET", target: "/", headers: { "X-Long": "xxxxxxxxxxxxxxxxxxxx" } })).status, 431);
});
