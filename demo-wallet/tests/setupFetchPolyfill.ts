/*
 * Polyfill fetch for Node-based Jest runs.
 * Node 20 provides fetch globally, but Jest may execute in contexts where it is not defined.
 * This loader ensures fetch and related classes exist before integration tests run.
 */

import fetch, { Headers, Request, Response } from "node-fetch";

const globalScope = globalThis as typeof globalThis & {
  fetch?: typeof fetch;
  Headers?: typeof Headers;
  Request?: typeof Request;
  Response?: typeof Response;
};

if (typeof globalScope.fetch !== "function") {
  globalScope.fetch = fetch as unknown as typeof globalScope.fetch;
}

if (typeof globalScope.Headers !== "function") {
  globalScope.Headers = Headers as unknown as typeof globalScope.Headers;
}

if (typeof globalScope.Request !== "function") {
  globalScope.Request = Request as unknown as typeof globalScope.Request;
}

if (typeof globalScope.Response !== "function") {
  globalScope.Response = Response as unknown as typeof globalScope.Response;
}
