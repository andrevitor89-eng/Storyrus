import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { Auth, accountGateHref, safeNextPath } from "./Auth";
import { VerifyEmail } from "./VerifyEmail";
import { getToken, setAuthFetchTimeoutMsForTests, setToken } from "./api";
import { state } from "./test/server";

afterEach(() => {
  setToken(null);
  setAuthFetchTimeoutMsForTests(15_000);
  state.reset();
});

function renderAuth(mode: "login" | "signup", next = "/app?tema=space") {
  const path = mode === "login" ? "/entrar" : "/cadastro";
  return render(
    <MemoryRouter initialEntries={[`${path}?next=${encodeURIComponent(next)}`]}>
      <Routes>
        <Route path="/entrar" element={<Auth mode="login" />} />
        <Route path="/cadastro" element={<Auth mode="signup" />} />
        <Route path="/verificar-email" element={<VerifyEmail />} />
        <Route path="/app" element={<div data-testid="studio-dest">studio</div>} />
        <Route path="/termos" element={<div>termos</div>} />
        <Route path="/privacidade" element={<div>privacidade</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

async function fillSignup(
  user: ReturnType<typeof userEvent.setup>,
  email = "nova@example.com",
) {
  await user.type(screen.getByTestId("auth-full-name"), "Ana Souza");
  await user.type(screen.getByTestId("auth-email"), email);
  await user.type(screen.getByTestId("auth-phone"), "11999999999");
  await user.type(screen.getByTestId("auth-password"), "password123");
  await user.type(screen.getByTestId("auth-password-confirm"), "password123");
  await user.type(screen.getByTestId("auth-postal-code"), "01310100");
  await user.type(screen.getByTestId("auth-street"), "Av Paulista");
  await user.type(screen.getByTestId("auth-number"), "1000");
  await user.type(screen.getByTestId("auth-complement"), "Sala 1");
  await user.type(screen.getByTestId("auth-district"), "Bela Vista");
  await user.type(screen.getByTestId("auth-city"), "Sao Paulo");
  await user.type(screen.getByTestId("auth-state"), "SP");
  await user.click(screen.getByTestId("auth-accept-terms"));
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
  it("cria conta e mostra tela de verificar e-mail (sem JWT)", async () => {
    const user = userEvent.setup();
    renderAuth("signup", "/app?tema=space");

    await fillSignup(user);
    await user.click(screen.getByTestId("auth-submit"));

    expect(await screen.findByTestId("auth-check-email")).toBeInTheDocument();
    expect(getToken()).toBeNull();
    expect(state.email).toBe("nova@example.com");
    expect(state.emailVerified).toBe(false);
    expect(screen.queryByTestId("studio-dest")).not.toBeInTheDocument();
  });

  it("confirma e-mail e entra no estúdio", async () => {
    state.isGuest = false;
    state.emailVerified = false;
    state.pendingVerifyToken = "test-verify-token";
    state.email = "verify@example.com";

    render(
      <MemoryRouter
        initialEntries={[
          `/verificar-email?token=test-verify-token&next=${encodeURIComponent("/app?tema=space")}`,
        ]}
      >
        <Routes>
          <Route path="/verificar-email" element={<VerifyEmail />} />
          <Route path="/app" element={<div data-testid="studio-dest">studio</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByTestId("studio-dest")).toBeInTheDocument();
    expect(getToken()).toBe("test-token");
    expect(state.emailVerified).toBe(true);
  });

  it("faz login e redireciona", async () => {
    const user = userEvent.setup();
    state.emailVerified = true;
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
    await fillSignup(user, "x@example.com");
    await user.click(screen.getByTestId("auth-submit"));
    expect(await screen.findByTestId("auth-error")).toHaveTextContent(/indisponível/i);
  });

  it("sai de Aguarde… quando o signup estoura o timeout", async () => {
    const user = userEvent.setup();
    setAuthFetchTimeoutMsForTests(80);
    const { http, delay } = await import("msw");
    const { server } = await import("./test/server");
    server.use(
      http.post("*/v1/auth/signup", async () => {
        await delay("infinite");
        return new Response();
      }),
    );
    renderAuth("signup", "/app");
    await fillSignup(user, "x@example.com");
    await user.click(screen.getByTestId("auth-submit"));
    expect(screen.getByTestId("auth-submit")).toHaveTextContent(/aguarde/i);
    expect(await screen.findByTestId("auth-error", {}, { timeout: 3000 })).toHaveTextContent(
      /indisponível/i,
    );
    expect(screen.getByTestId("auth-submit")).not.toBeDisabled();
  });
});
