import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server, state } from "./server";

// crypto.randomUUID em ambiente de teste (caso o jsdom não exponha).
if (!globalThis.crypto?.randomUUID) {
  // @ts-expect-error polyfill simples para os testes
  globalThis.crypto = { ...globalThis.crypto, randomUUID: () => `uuid-${Math.random()}` };
}

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  state.reset();
});
afterAll(() => server.close());
