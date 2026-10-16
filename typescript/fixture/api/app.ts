import { AppRequest, headerBytes, text, type AppResponse, type RequestInput } from "./http.ts";
import { logger } from "./log.ts";
import type { Options, RouteOptions } from "./options.ts";

/** A handler takes a request and returns a response, directly or through a promise. */
export type Handler = (req: AppRequest) => AppResponse | Promise<AppResponse>;

/** A middleware wraps the next step. */
export type Middleware = (req: AppRequest, next: Handler) => AppResponse | Promise<AppResponse>;

/** A registered path with its handler and options. */
export interface Route {
  path: string;
  handler: Handler;
  options: RouteOptions;
}

function accepts(route: Route, method: string): boolean {
  return !route.options.methods || route.options.methods.length === 0 || route.options.methods.includes(method);
}

/** An App holds routes, options and middleware. */
export class App {
  readonly options: Options;
  readonly #routes: Route[] = [];
  readonly #middlewares: Middleware[] = [];

  constructor(options: Options = {}) {
    this.options = { ...options, maxHeaderBytes: options.maxHeaderBytes ?? 8192 };
  }

  /** Registers a handler for an exact path. */
  route(path: string, handler: Handler, options: RouteOptions = {}): Route {
    const route: Route = { path, handler, options };
    this.#routes.push(route);
    return route;
  }

  /** The registered routes. */
  routes(): Route[] {
    return [...this.#routes];
  }

  /** Adds a middleware; middlewares run in the order added, outermost first. */
  use(middleware: Middleware): void {
    this.#middlewares.push(middleware);
  }

  #match(req: AppRequest): Route | undefined {
    return this.#routes.find((r) => r.path === req.path && accepts(r, req.method));
  }

  /** Runs a request through the pipeline. */
  async handle(input: RequestInput | AppRequest): Promise<AppResponse> {
    const req = input instanceof AppRequest ? input : new AppRequest(input);
    if (headerBytes(req.headers) > (this.options.maxHeaderBytes ?? 8192)) {
      return text(431, "Request Header Fields Too Large");
    }
    const route = this.#match(req);
    if (!route) return text(404, "Not Found");
    let next: Handler = route.handler;
    for (let i = this.#middlewares.length - 1; i >= 0; i -= 1) {
      const m = this.#middlewares[i]!;
      const following = next;
      next = (r) => m(r, following);
    }
    const res = await next(req);
    if (this.options.requestLog) logger.log(`${req.method} ${req.path} -> ${res.status}`);
    return res;
  }
}
