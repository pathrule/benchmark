import type { AppResponse } from "./http.ts";

/** The prefix of every problem type URI. */
export const TYPE_BASE = "https://errors.acme.dev/";

/** An error the toolkit itself answers, in the problem format (RFC 9457). */
export function problem(status: number, title: string, detail: string, slug: string): AppResponse {
  const body = JSON.stringify({ type: TYPE_BASE + slug, title, status, detail });
  return { status, body, headers: new Headers({ "Content-Type": "application/problem+json" }) };
}
