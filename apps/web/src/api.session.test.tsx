import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { readJwtPayload, setToken } from "./api";
import { state } from "./test/server";

afterEach(() => {
  vi.restoreAllMocks();
  setToken(null);
  state.reset();
});

function fakeJwt(exp: number): string {
  const header = btoa(JSON.stringify({ alg: "none", typ: "JWT" }));
  const payload = btoa(JSON.stringify({ sub: "u1", exp }));
  return `${header}.${payload}.sig`;
}

describe("readJwtPayload", () => {
  it("decodes exp from a JWT-shaped token", () => {
    const exp = Math.floor(Date.now() / 1000) + 3600;
    const payload = readJwtPayload(fakeJwt(exp));
    expect(payload?.exp).toBe(exp);
  });

  it("returns null for garbage", () => {
    expect(readJwtPayload("not-a-jwt")).toBeNull();
  });
});

describe("Studio guest upgrade (STO-26)", () => {
  it("shows Criar conta for guests and upgrades in place", async () => {
    const user = userEvent.setup();
    render(<App />);

    const open = await screen.findByTestId("studio-upgrade-open");
    await user.click(open);

    expect(await screen.findByTestId("studio-upgrade-form")).toBeInTheDocument();
    await user.type(screen.getByTestId("studio-upgrade-email"), "parent@example.com");
    await user.type(screen.getByTestId("studio-upgrade-password"), "password123");
    await user.click(screen.getByTestId("studio-upgrade-submit"));

    await waitFor(() => {
      expect(state.isGuest).toBe(false);
      expect(state.email).toBe("parent@example.com");
    });
    await waitFor(() => {
      expect(screen.queryByTestId("studio-upgrade-form")).not.toBeInTheDocument();
      expect(screen.queryByTestId("studio-upgrade-open")).not.toBeInTheDocument();
    });
  });
});
