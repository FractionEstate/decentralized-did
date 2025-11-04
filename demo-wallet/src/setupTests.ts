// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import "@testing-library/jest-dom";
import { Crypto } from "@peculiar/webcrypto";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { TextDecoder, TextEncoder, ReadableStream } = require("node:util");

Reflect.set(globalThis, "TextDecoder", TextDecoder);
Reflect.set(globalThis, "TextEncoder", TextEncoder);
Reflect.set(globalThis, "ReadableStream", { ...ReadableStream, prototype: {} });

Object.defineProperty(global, "crypto", {
  value: new Crypto(),
  writable: true,
});

global.structuredClone = (v) => JSON.parse(JSON.stringify(v));

// Polyfill matchMedia for components using responsive checks (only in DOM environment)
if (typeof window !== 'undefined' && !window.matchMedia) {
  // @ts-ignore
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => { }, // deprecated
    removeListener: () => { }, // deprecated
    addEventListener: () => { },
    removeEventListener: () => { },
    dispatchEvent: () => false,
  });
}

// Polyfill ResizeObserver & IntersectionObserver for layout-dependent components (only in DOM environment)
class NoopObserver {
  observe() { }
  unobserve() { }
  disconnect() { }
}
// @ts-ignore
if (typeof window !== 'undefined') {
  if (!("ResizeObserver" in window)) window.ResizeObserver = NoopObserver as any;
  // @ts-ignore
  if (!("IntersectionObserver" in window)) window.IntersectionObserver = NoopObserver as any;
  // @ts-ignore
  if (!window.scrollTo) window.scrollTo = () => { };
}

// Mock navigator.clipboard for tests that copy values (only in DOM environment)
if (typeof navigator !== 'undefined' && !navigator.clipboard) {
  // @ts-ignore
  navigator.clipboard = {
    writeText: async () => { },
    readText: async () => "",
  };
}
