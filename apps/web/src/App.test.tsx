import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { api } from "./api";
import { state } from "./test/server";

afterEach(() => {
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
});

describe("Fluxo E2E (sem login)", () => {
  it("respeita ?paginas=5 no e-book do Studio", async () => {
    window.history.replaceState({}, "", "/app?paginas=5");
    const start = vi.spyOn(api, "startStep").mockResolvedValue({
      job_id: "j1",
      status: "PENDING",
      type: "EBOOK",
      estimated_cost_credits: 1,
    } as never);
    vi.spyOn(api, "listJobs").mockResolvedValue([]);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: /criar projeto/i }));
    expect(await screen.findByText(/gerando até a página/i)).toBeInTheDocument();
    start.mockRestore();
  });

  it("estúdio → projeto → foto gera personagem → história", async () => {
    state.credits = 10;
    const user = userEvent.setup();
    const { container } = render(<App />);

    // o estúdio carrega direto, sem tela de login
    expect(await screen.findByText(/créditos: 10/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /criar projeto/i }));
    expect(await screen.findByRole("heading", { name: /^projeto$/i })).toBeInTheDocument();
    expect(screen.queryByText(/criança igual à foto/i)).not.toBeInTheDocument();
    expect(
      screen.getByText(/travamos o rosto da foto no personagem/i),
    ).toBeInTheDocument();

    // envia a foto -> personagem é gerado automaticamente
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["x"], "foto.jpg", { type: "image/jpeg" });
    await user.upload(fileInput, file);
    const sendPhoto = screen.getByRole("button", { name: /enviar foto/i });
    expect(sendPhoto).toBeDisabled();
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    expect(sendPhoto).toBeEnabled();
    await user.click(sendPhoto);
    expect(await screen.findByText("AVATAR")).toBeInTheDocument();

    // gera a história (modo "inventar com IA")
    await user.click(screen.getByRole("button", { name: /gerar história com ia/i }));
    expect(await screen.findByText("STORY")).toBeInTheDocument();

    // história aparece na plataforma (o mock leva alguns ciclos de polling)
    expect(
      await screen.findByText(/pagina 1: ola/i, undefined, { timeout: 9000 }),
    ).toBeInTheDocument();
  }, 20000);

  it("habilita 'Montar ebook' depois de aprovar o personagem", async () => {
    state.credits = 10;
    const user = userEvent.setup();
    const { container } = render(<App />);

    await screen.findByText(/créditos: 10/i);
    await user.click(screen.getByRole("button", { name: /criar projeto/i }));

    // sem foto/história, o botão de ebook fica desabilitado
    const ebookBtn = await screen.findByRole("button", { name: /montar ebook/i });
    expect(ebookBtn).toBeDisabled();

    // envia foto (gera personagem) e a história
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, new File(["x"], "foto.jpg", { type: "image/jpeg" }));
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(screen.getByRole("button", { name: /enviar foto/i }));
    await user.click(screen.getByRole("button", { name: /gerar história com ia/i }));
    await screen.findByText(/pagina 1: ola/i, undefined, { timeout: 9000 });

    // ebook continua travado até aprovar o personagem
    expect(screen.getByRole("button", { name: /montar ebook/i })).toBeDisabled();
    await user.click(
      await screen.findByRole("button", { name: /aprovar personagem/i }, { timeout: 9000 }),
    );

    // agora o ebook pode ser montado
    await waitFor(
      () => expect(screen.getByRole("button", { name: /montar ebook/i })).toBeEnabled(),
      { timeout: 9000 },
    );
  }, 20000);

  it("abre exemplo pronto sem criar projeto", async () => {
    state.credits = 10;
    const create = vi.spyOn(api, "createProject");
    window.history.pushState({}, "", "/app?exemplo=dinosaurs");
    render(<App />);

    expect(await screen.findByText(/você está vendo um exemplo pronto/i)).toBeInTheDocument();
    expect(await screen.findByDisplayValue("Matteo")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: /^personagem$/i })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: /vídeo narrado/i })).toBeInTheDocument();
    expect(screen.getByAltText(/página 1/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /montar ebook/i })).toBeDisabled();
    expect(create).not.toHaveBeenCalled();
  });
});
