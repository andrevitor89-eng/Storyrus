import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { ProgressList, Studio } from "./Studio";
import { BookApprovalBlock } from "./studio/ApprovalBlocks";
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

describe("Livro impresso", () => {
  it("mostra miolo e capas ao lado do e-book, sem preço", () => {
    render(
      <BookApprovalBlock
        pageImages={[]}
        ebookUrl="https://cdn.test/livro.pdf"
        printInteriorUrl="https://cdn.test/miolo.pdf"
        printCoversUrl="https://cdn.test/capas.pdf"
        bookApproved={false}
        locked={false}
        canMountEbook
        printRequested={false}
        onApprove={() => undefined}
        onRegenerate={() => undefined}
        onRequestPrint={() => undefined}
      />,
    );

    expect(screen.getByRole("link", { name: /abrir e-book/i })).toHaveAttribute(
      "href",
      "https://cdn.test/livro.pdf",
    );
    expect(screen.getByRole("link", { name: /miolo para gráfica/i })).toHaveAttribute(
      "href",
      "https://cdn.test/miolo.pdf",
    );
    expect(screen.getByRole("link", { name: /capas para gráfica/i })).toHaveAttribute(
      "href",
      "https://cdn.test/capas.pdf",
    );
    expect(screen.queryByText(/R\$/)).not.toBeInTheDocument();
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

    expect(await screen.findByTestId("studio-project")).toBeInTheDocument();
    expect(screen.getByTestId("studio-generate-story")).toBeInTheDocument();
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
    await user.click(screen.getByRole("button", { name: /gerar história com ia/i }));
    expect(await screen.findByText("STORY")).toBeInTheDocument();

    await waitFor(
      () => expect(screen.getByText(/pagina 1: ola/i)).toBeInTheDocument(),
      { timeout: 9000 },
    );

    const pollTimers = spy.mock.calls.filter((c) => c[1] === 2500);
    expect(pollTimers.length).toBeLessThanOrEqual(2);
  }, 20000);
});
