// Every member of Options is listed in AppOptions and documented in docs/options.md; the team suite
// reads the interface's members from this file and checks both.

/** Options configure an App. */
export interface Options {
  /** Log every handled request on the toolkit's logger. */
  requestLog?: boolean;
  /** Requests whose headers exceed this many bytes answer 431. */
  maxHeaderBytes?: number;
}

/** The registry of Options members. */
export const AppOptions: string[] = ["requestLog", "maxHeaderBytes"];

/** RouteOptions configure one route. Every member is listed in RouteOptionNames and documented. */
export interface RouteOptions {
  /** The methods the route accepts; absent means all. */
  methods?: string[];
}

/** The registry of RouteOptions members. */
export const RouteOptionNames: string[] = ["methods"];
