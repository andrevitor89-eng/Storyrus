import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { api } from "./api";
import { ProgressList, Studio } from "./Studio";
import type { Job } from "./types";
import { state } from "./test/server";

afterEach(() => {
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
});

function ebookJob(overrides: Partial<Job> = {}): Job {
  return {
    id: "job-1",
    project_id: "p1",
    type: "EBOOK",
    status: "RUNNING",
    provider: null,
    cost_credits: 1,
    attempts: 1,
    error: null,
    created_at: "2026-01-01T00:00:00Z",
    result: { progress: { stage: "pages", done: 4, total: 11 } },
    ...overrides,
  };
}

describe("ProgressList", () => {
  it("mostra Ilustrando 4/11 no job EBOOK em andamento", () => {
    render(<ProgressList jobs={[ebookJob()]} />);
    expect(screen.getByText("Ilustrando 4/11")).toBeInTheDocument();
  });

  it("expõe progresso com role status e aria-live", () => {
    render(<ProgressList jobs={[ebookJob()]} />);
    const status = screen.getByRole("status", { name: /progresso das etapas/i });
    expect(status).toHaveAttribute("aria-live", "polite");
    expect(within(status).getByText("EBOOK")).toBeInTheDocument();
  });
});

describe("Studio — tema do banner", () => {
  it("preenche título e história e troca o nome do exemplo pelo da criança", async () => {
    window.history.replaceState(
      {},
      "",
      "/app?tema=princess&titulo=Emilia%20e%20os%20Primeiros%20Passos&historia=Primeiros%20passos%20no%20ballet&heroi=Emilia",
    );
    const user = userEvent.setup();
    render(<Studio />);

    expect(screen.getByLabelText(/título do livro/i)).toHaveValue("Emilia e os Primeiros Passos");
    expect(screen.getByLabelText(/insira o tema desejado/i)).toHaveValue("Primeiros passos no ballet");
    expect(screen.getByLabelText(/nome da criança/i)).toHaveValue("");
    expect(screen.getByLabelText(/^idade$/i)).toHaveValue(null);

    await user.type(screen.getByLabelText(/nome da criança/i), "Lia");
    expect(screen.getByLabelText(/título do livro/i)).toHaveValue("Lia e os Primeiros Passos");
    expect(screen.getByLabelText(/^idade$/i)).toHaveValue(null);
  });

  it("leva só o tema e deixa o nome da criança em branco", async () => {
    window.history.replaceState({}, "", "/app?tema=mothers_day&campos=tema&historia=Amor+de+m%C3%A3e");
    render(<Studio />);

    expect(screen.getByLabelText(/nome da criança/i)).toHaveValue("");
    expect(screen.getByLabelText(/título do livro/i)).toHaveValue("");
    expect(screen.getByLabelText(/insira o tema desejado/i)).toHaveValue("Amor de mãe");
  });

  it("abre o livro escolhido e pede só nome e idade", async () => {
    window.history.replaceState(
      {},
      "",
      "/app?tema=fathers_day&campos=nome&titulo=Papai%20her%C3%B3i&historia=Papai%20her%C3%B3i&tamanho=P&capa=soft&modo=cartoon",
    );
    render(<Studio />);

    expect(screen.getByText(/livro escolhido/i)).toBeInTheDocument();
    expect(screen.getByText(/papai herói/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/título do livro/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/insira o tema desejado/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/nome da criança/i)).toHaveValue("");
    expect(screen.getByLabelText(/^idade$/i)).toHaveValue(null);
    expect(screen.getByRole("button", { name: /15 × 15 cm/i, pressed: true })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /capa mole/i, pressed: true })).toBeInTheDocument();
    expect(screen.getByLabelText(/selecionar foto do protagonista/i)).toBeInTheDocument();
    expect(screen.getByTestId("studio-extra-names")).toBeInTheDocument();
  });

  it("manda o livro escolhido e os outros nomes no pedido, sem o bloco do dono", async () => {
    state.credits = 10;
    const upload = vi.spyOn(api, "uploadPhoto");
    window.history.replaceState(
      {},
      "",
      "/app?tema=fathers_day&campos=nome&titulo=Papai%20her%C3%B3i&historia=Papai%20her%C3%B3i&modo=cartoon",
    );
    const user = userEvent.setup();
    render(<Studio />);

    await user.type(screen.getByLabelText(/nome da criança/i), "Lia");
    await user.type(screen.getByLabelText(/^idade$/i), "4");
    await user.type(screen.getByTestId("studio-extra-names"), "Vovó, Totó");
    await user.upload(
      screen.getByTestId("studio-photo-input"),
      new File(["x"], "foto.jpg", { type: "image/jpeg" }),
    );
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(screen.getByRole("button", { name: /criar livro/i }));

    const sent = await screen.findByTestId("studio-order-sent");
    expect(sent).toHaveTextContent(/pedido enviado/i);
    expect(sent).toHaveTextContent(/nossa equipe entrará em contato/i);
    expect(screen.queryByTestId("studio-generate-story")).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/nome da criança/i)).not.toBeInTheDocument();
    expect(upload).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(File),
      expect.objectContaining({
        language: "pt-BR",
        themeLabel: "Papai herói",
        extraNames: "Vovó, Totó",
      }),
    );
  });

  it("preenche um tema sem livro único e deixa os campos editáveis", async () => {
    window.history.replaceState({}, "", "/app?tema=sport");
    const user = userEvent.setup();
    render(<Studio />);

    const title = screen.getByLabelText(/título do livro/i);
    expect(title).toHaveValue("Uma história de esporte");
    expect(screen.getByLabelText(/insira o tema desejado/i)).toHaveValue(
      "Esporte: treino, coragem e superação, com a criança no centro da própria história.",
    );
    await user.clear(title);
    await user.type(title, "Lia no gol");
    expect(title).toHaveValue("Lia no gol");
  });
});

describe("Studio a11y", () => {
  it("marca fluxos principais com landmark, alert e tabs", async () => {
    state.credits = 10;
    const user = userEvent.setup();
    render(<Studio />);

    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveAttribute("id", "studio-main");
    expect(screen.getByRole("heading", { name: /crie a sua história/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/nome da criança/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/título do livro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/insira o tema desejado/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/selecionar foto do protagonista/i)).toBeInTheDocument();

    await user.type(screen.getByLabelText(/nome da criança/i), "Lila");
    await user.type(screen.getByLabelText(/idade/i), "5");
    await user.type(screen.getByLabelText(/título do livro/i), "Lila e as estrelas");
    await user.type(screen.getByLabelText(/insira o tema desejado/i), "Aventura no espaço");
    const fileInput = screen.getByTestId("studio-photo-input");
    await user.upload(fileInput, new File(["x"], "foto.jpg", { type: "image/jpeg" }));
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(screen.getByRole("button", { name: /criar livro/i }));

    const sent = await screen.findByTestId("studio-order-sent");
    expect(sent).toHaveTextContent(/pedido enviado/i);
    expect(sent).toHaveTextContent(/nossa equipe entrará em contato/i);
    expect(screen.queryByTestId("studio-generate-story")).not.toBeInTheDocument();
  });
});

describe("Polling do estúdio", () => {
  it("não recria o interval a cada update de jobs", async () => {
    state.credits = 10;
    const spy = vi.spyOn(window, "setInterval");
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText(/nome da criança/i), "Lila");
    await user.type(screen.getByLabelText(/idade/i), "5");
    await user.type(screen.getByLabelText(/título do livro/i), "Lila e as estrelas");
    await user.type(screen.getByLabelText(/insira o tema desejado/i), "Aventura no espaço");
    await user.upload(screen.getByTestId("studio-photo-input"), new File(["x"], "foto.jpg", { type: "image/jpeg" }));
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(await screen.findByRole("button", { name: /criar livro/i }));
    const sent = await screen.findByTestId("studio-order-sent");
    expect(sent).toHaveTextContent(/pedido enviado/i);
    expect(sent).toHaveTextContent(/nossa equipe entrará em contato/i);
    expect(screen.queryByRole("button", { name: /gerar história com ia/i })).not.toBeInTheDocument();

    const pollTimers = spy.mock.calls.filter((c) => c[1] === 2500);
    expect(pollTimers.length).toBeLessThanOrEqual(2);
  }, 20000);
});
