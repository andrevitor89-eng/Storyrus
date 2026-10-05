import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { Auth } from "./Auth";
import { Conta } from "./Conta";
import { getToken, setToken } from "./api";
import { AppRoutes } from "./Root";
import { state } from "./test/server";

function asRegistered(email = "ana@email.com") {
  state.isGuest = false;
  state.email = email;
  state.credits = 12;
  setToken("test-token");
}

function renderConta(initial = "/conta") {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <Routes>
        <Route path="/conta" element={<Conta />} />
        <Route path="/cadastro" element={<Auth mode="signup" />} />
        <Route path="/entrar" element={<Auth mode="login" />} />
        <Route path="/app" element={<div data-testid="studio-stub">Estúdio</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  setToken(null);
  state.reset();
});

describe("Conta", () => {
  it("redireciona para cadastro sem sessão", async () => {
    setToken(null);
    renderConta();
    expect(await screen.findByTestId("auth-page")).toBeInTheDocument();
    expect(screen.getByTestId("auth-submit")).toHaveTextContent(/criar conta/i);
  });

  it("mostra e-mail, créditos e projetos com conta registrada", async () => {
    asRegistered("lia@storyrus.app");
    state.projects.set("proj-1", {
      id: "proj-1",
      status: "EBOOK_READY",
      style: "cgi_3d",
      child_name: "Lila",
      story_text: null,
      ebook_url: null,
      video_url: null,
      created_at: "2026-02-01T12:00:00Z",
    });
    state.voices = [
      {
        id: "voice-1",
        name: "Voz da avó",
        is_default: true,
        mime_type: "audio/mpeg",
        created_at: "2026-02-02T12:00:00Z",
      },
    ];
    state.customVoiceAvailable = true;

    renderConta();

    expect(await screen.findByTestId("conta-page")).toBeInTheDocument();
    expect(screen.getByTestId("conta-email")).toHaveTextContent("lia@storyrus.app");
    expect(screen.getByTestId("conta-credits")).toHaveTextContent("12");
    expect(screen.getByTestId("conta-projects")).toHaveTextContent("Lila");
    expect(screen.getByTestId("conta-projects")).toHaveTextContent("EBOOK_READY");
    expect(screen.getByTestId("conta-voices")).toHaveTextContent("Voz da avó");
    expect(screen.getByRole("link", { name: /abrir no estúdio/i })).toHaveAttribute("href", "/app");
  });

  it("rota /conta nao cai na landing", async () => {
    asRegistered();
    render(
      <MemoryRouter initialEntries={["/conta"]}>
        <AppRoutes />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("conta-page")).toBeInTheDocument();
    expect(screen.queryByText(/escolha um livro/i)).not.toBeInTheDocument();
  });

  it("sair limpa o token e vai para entrar", async () => {
    asRegistered();
    const user = userEvent.setup();
    renderConta();
    expect(await screen.findByTestId("conta-page")).toBeInTheDocument();

    await user.click(screen.getByTestId("conta-logout"));
    expect(getToken()).toBeNull();
    await waitFor(() => {
      expect(screen.getByTestId("auth-page")).toBeInTheDocument();
    });
  });

  it("remove voz clonada", async () => {
    asRegistered();
    state.customVoiceAvailable = true;
    state.voices = [
      {
        id: "voice-rm",
        name: "Narradora",
        is_default: true,
        mime_type: "audio/mpeg",
        created_at: "2026-03-01T00:00:00Z",
      },
    ];
    const user = userEvent.setup();
    renderConta();

    expect(await screen.findByText(/Narradora/)).toBeInTheDocument();
    await user.click(screen.getByTestId("conta-voice-remove-voice-rm"));
    await waitFor(() => {
      expect(screen.queryByText(/Narradora/)).not.toBeInTheDocument();
    });
  });
});
