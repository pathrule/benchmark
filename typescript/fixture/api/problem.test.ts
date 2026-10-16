import { test } from "node:test";
import assert from "node:assert/strict";
import { problem, TYPE_BASE } from "./problem.ts";

test("a problem response has the problem shape", () => {
  const res = problem(418, "Teapot", "short and stout", "teapot");
  assert.equal(res.status, 418);
  assert.equal(res.headers.get("Content-Type"), "application/problem+json");
  assert.equal(JSON.parse(res.body).type, TYPE_BASE + "teapot");
});
