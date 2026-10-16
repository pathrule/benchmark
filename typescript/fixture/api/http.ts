// The request a handler receives and the response it returns. Standard library only.

/** What a caller passes to `app.handle()`: the target is the path with its optional query string. */
export interface RequestInput {
  method: string;
  target: string;
  headers?: HeadersInit;
  body?: string;
}

/** The request a handler receives. */
export class AppRequest {
  readonly method: string;
  readonly target: string;
  readonly headers: Headers;
  readonly body: string;

  constructor(input: RequestInput) {
    this.method = input.method;
    this.target = input.target;
    this.headers = new Headers(input.headers ?? {});
    this.body = input.body ?? "";
  }

  /** The request's path without the query string. */
  get path(): string {
    return new URL(this.target, "http://acme.local").pathname;
  }

  /** The parsed query string. */
  get query(): URLSearchParams {
    return new URL(this.target, "http://acme.local").searchParams;
  }

  /** A request header, or "" when absent. */
  get(name: string): string {
    return this.headers.get(name) ?? "";
  }
}

/** What a handler returns. */
export interface AppResponse {
  status: number;
  body: string;
  headers: Headers;
}

/** A plain-text response. */
export function text(status: number, body: string): AppResponse {
  return { status, body, headers: new Headers({ "Content-Type": "text/plain; charset=utf-8" }) };
}

/** An application/json response. */
export function json(status: number, value: unknown): AppResponse {
  return { status, body: JSON.stringify(value), headers: new Headers({ "Content-Type": "application/json" }) };
}

export function headerBytes(headers: Headers): number {
  let n = 0;
  for (const [name, value] of headers) n += name.length + value.length;
  return n;
}
