import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { Auth, accountGateHref, safeNextPath } from "./Auth";
import { getToken, setToken } from "./api";
import { state } from "./test/server";

afterEach(() => {
  setToken(null);
  state.reset();
});

function renderAuth(mode: "login" | "signup", next = "/app?tema=space") {
  const path = mode === "login" ? "/entrar" : "/cadastro";
  return render(
    <MemoryRouter initialEntries={[`${path}?next=${encodeURIComponent(next)}`]}>
      <Routes>
        <Route path="/entrar" element={<Auth mode="login" />} />
        <Route path="/cadastro" element={<Auth mode="signup" />} />
        <Route path="/app" element={<div data-testid="studio-dest">studio</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("safeNextPath / accountGateHref", () => {
  it("bloqueia open redirects", () => {
    expect(safeNextPath("https://evil.com")).toBe("/app");
    expect(safeNextPath("//evil.com")).toBe("/app");
    expect(safeNextPath("/app?tema=pets")).toBe("/app?tema=pets");
    expect(accountGateHref("/app?tema=pets")).toBe(
      `/cadastro?next=${encodeURIComponent("/app?tema=pets")}`,
    );
  });
});

describe("Auth", () => {
  it("cria conta e redireciona para next", async () => {
    const user = userEvent.setup();
    renderAuth("signup", "/app?tema=space");

    await user.type(screen.getByTestId("auth-email"), "nova@example.com");
    await user.type(screen.getByTestId("auth-password"), "password123");
    await user.click(screen.getByTestId("auth-submit"));

    expect(await screen.findByTestId("studio-dest")).toBeInTheDocument();
    expect(getToken()).toBe("test-token");
    expect(state.isGuest).toBe(false);
    expect(state.email).toBe("nova@example.com");
  });

  it("faz login e redireciona", async () => {
    const user = userEvent.setup();
    renderAuth("login", "/app");

    await user.type(screen.getByTestId("auth-email"), "ja@example.com");
    await user.type(screen.getByTestId("auth-password"), "password123");
    await user.click(screen.getByTestId("auth-submit"));

    expect(await screen.findByTestId("studio-dest")).toBeInTheDocument();
    await waitFor(() => expect(getToken()).toBe("test-token"));
  });

  it("alterna entre login e cadastro preservando next", async () => {
    const user = userEvent.setup();
    renderAuth("login", "/app?tema=pets");
    await user.click(screen.getByTestId("auth-switch"));
    expect(screen.getByTestId("auth-submit")).toHaveTextContent(/criar conta/i);
    expect(screen.getByTestId("auth-switch")).toHaveAttribute(
      "href",
      expect.stringContaining("next="),
    );
  });

  it("mostra erro legível quando a API responde 502", async () => {
    const user = userEvent.setup();
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("./test/server");
    server.use(
      http.post("*/v1/auth/signup", () => HttpResponse.text("bad gateway", { status: 502 })),
    );
    renderAuth("signup", "/app");
    await user.type(screen.getByTestId("auth-email"), "x@example.com");
    await user.type(screen.getByTestId("auth-password"), "password123");
    await user.click(screen.getByTestId("auth-submit"));
    expect(await screen.findByTestId("auth-error")).toHaveTextContent(/indisponível/i);
  });
});
