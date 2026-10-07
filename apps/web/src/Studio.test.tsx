import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { App } from "./App";
import { api, setToken } from "./api";
import { ProgressList, Studio } from "./Studio";
import type { Job } from "./types";
import { state } from "./test/server";

function renderApp(initial = "/app") {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <Routes>
        <Route path="/app" element={<App />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  state.isGuest = false;
  state.emailVerified = true;
  state.email = "ana@email.com";
  state.fullName = "Ana Souza";
  state.phone = "11999999999";
  state.postalCode = "01310100";
  state.street = "Av Paulista";
  state.number = "1000";
  state.complement = "Sala 1";
  state.district = "Bela Vista";
  state.city = "Sao Paulo";
  state.stateUf = "SP";
  state.credits = 10;
  setToken("test-token");
});

afterEach(() => {
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
});

async function openBook(_user: ReturnType<typeof userEvent.setup>) {
  expect(screen.queryByTestId("studio-client")).not.toBeInTheDocument();
  await screen.findByRole("checkbox", { name: /responsável legal/i });
}

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
    await openBook(user);

    expect(screen.getByLabelText(/título do livro/i)).toHaveValue("Emilia e os Primeiros Passos");
    expect(screen.getByLabelText(/insira o tema desejado/i)).toHaveValue("Primeiros passos no ballet");
    expect(screen.getByLabelText(/nome do protagonista/i)).toHaveValue("");
    expect(screen.getByLabelText(/^idade$/i)).toHaveValue(null);

    await user.type(screen.getByLabelText(/nome do protagonista/i), "Lia");
    expect(screen.getByLabelText(/título do livro/i)).toHaveValue("Lia e os Primeiros Passos");
    expect(screen.getByLabelText(/^idade$/i)).toHaveValue(null);
  });

  it("leva só o tema e deixa o nome do protagonista em branco", async () => {
    window.history.replaceState({}, "", "/app?tema=mothers_day&campos=tema&historia=Amor+de+m%C3%A3e");
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    expect(screen.getByLabelText(/nome do protagonista/i)).toHaveValue("");
    expect(screen.getByLabelText(/título do livro/i)).toHaveValue("");
    expect(screen.getByLabelText(/insira o tema desejado/i)).toHaveValue("Amor de mãe");
  });

  it("abre o livro escolhido e pede só nome e idade", async () => {
    window.history.replaceState(
      {},
      "",
      "/app?tema=fathers_day&campos=nome&titulo=Papai%20her%C3%B3i&historia=Papai%20her%C3%B3i&tamanho=P&capa=soft&modo=cartoon&quem=pai&genero=m",
    );
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    expect(screen.getByText(/livro escolhido/i)).toBeInTheDocument();
    expect(screen.getByText(/papai herói/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/título do livro/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/insira o tema desejado/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/nome do pai/i)).toHaveValue("");
    expect(screen.getByLabelText(/idade do pai/i)).toHaveValue(null);
    expect(screen.getByRole("button", { name: /^masculino$/i, pressed: true })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /15 × 15 cm/i, pressed: true })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /capa flexível/i, pressed: true })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^cartoon$/i, pressed: true })).toBeInTheDocument();
    expect(screen.queryByLabelText(/^quantidade de livros$/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/selecionar foto do protagonista/i)).toBeInTheDocument();
    expect(screen.getByText(/foto de um ou mais personagens/i)).toBeInTheDocument();
    expect(screen.getByTestId("studio-photo-drop")).toHaveTextContent(/envie fotos do protagonista da sua história/i);
    expect(screen.getByTestId("studio-photo-drop")).toHaveTextContent(/escolha quem fará parte do seu livro/i);
    expect(screen.getByTestId("studio-photo-drop")).toHaveTextContent(/adicione fotos de um ou mais personagens/i);
    expect(screen.getByTestId("studio-extra-names")).toBeInTheDocument();
  });

  it("manda o livro escolhido e os outros nomes no pedido, sem o bloco do dono", async () => {
    state.credits = 10;
    const upload = vi.spyOn(api, "uploadPhoto");
    window.history.replaceState(
      {},
      "",
      "/app?tema=fathers_day&campos=nome&titulo=Papai%20her%C3%B3i&historia=Papai%20her%C3%B3i&modo=cartoon&quem=pai&genero=m",
    );
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    await user.type(screen.getByLabelText(/nome do pai/i), "Lia");
    await user.type(screen.getByLabelText(/idade do pai/i), "4");
    await user.type(screen.getByTestId("studio-extra-names"), "Vovó, Totó");
    await user.upload(
      screen.getByTestId("studio-photo-input"),
      new File(["x"], "foto.jpg", { type: "image/jpeg" }),
    );
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(screen.getByRole("button", { name: /próxima página/i }));
    await user.click(screen.getByRole("button", { name: /gerar o livro/i }));

    const sent = await screen.findByTestId("studio-order-sent");
    expect(sent).toHaveTextContent(/projeto criado/i);
    expect(sent).toHaveTextContent(/prévia/i);
    expect(screen.getByTestId("studio-generate-preview")).toBeInTheDocument();
    expect(screen.getByTestId("studio-generate-story")).toBeInTheDocument();
    expect(screen.queryByLabelText(/nome do pai/i)).not.toBeInTheDocument();
    expect(upload).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(File),
      expect.objectContaining({
        language: "pt-BR",
        themeLabel: "Papai herói",
        extraNames: "Vovó, Totó",
        gender: "m",
        subject: "pai",
        clientName: "Ana Souza",
        clientEmail: "ana@email.com",
        clientPhone: "11999999999",
        clientAddress: "Av Paulista, 1000, Sala 1, Bela Vista, Sao Paulo, SP, BR, 01310100",
        clientNotes: undefined,
      }),
    );
  });

  it("envia cada foto e só fecha o pedido na última", async () => {
    state.credits = 10;
    const upload = vi.spyOn(api, "uploadPhoto");
    window.history.replaceState({}, "", "/app");
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    await user.type(screen.getByLabelText(/nome do protagonista/i), "Lila");
    await user.type(screen.getByLabelText(/^idade$/i), "5");
    await user.type(screen.getByLabelText(/título do livro/i), "Lila e as estrelas");
    await user.type(screen.getByLabelText(/insira o tema desejado/i), "Aventura no espaço");
    await user.upload(screen.getByTestId("studio-photo-input"), [
      new File(["a"], "frente.jpg", { type: "image/jpeg" }),
      new File(["b"], "sorriso.jpg", { type: "image/jpeg" }),
    ]);
    expect(screen.getByText("frente.jpg")).toBeInTheDocument();
    expect(screen.getByText("sorriso.jpg")).toBeInTheDocument();
    expect(screen.getByText(/2 fotos selecionadas/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /^feminino$/i }));
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(screen.getByRole("button", { name: /próxima página/i }));
    await user.click(screen.getByRole("button", { name: /gerar o livro/i }));

    await screen.findByTestId("studio-order-sent");
    expect(upload).toHaveBeenNthCalledWith(
      1,
      expect.any(String),
      expect.objectContaining({ name: "frente.jpg" }),
      expect.objectContaining({ finalize: false }),
    );
    expect(upload).toHaveBeenNthCalledWith(
      2,
      expect.any(String),
      expect.objectContaining({ name: "sorriso.jpg" }),
      expect.objectContaining({ finalize: true }),
    );
  });

  it("conta registrada vai direto ao livro", async () => {
    render(<Studio />);

    expect(await screen.findByRole("checkbox", { name: /responsável legal/i })).toBeInTheDocument();
    expect(screen.queryByTestId("studio-client")).not.toBeInTheDocument();
  });

  it("preenche um tema sem livro único e deixa os campos editáveis", async () => {
    window.history.replaceState({}, "", "/app?tema=sport");
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    const title = screen.getByLabelText(/título do livro/i);
    expect(title).toHaveValue("Uma História de Esporte");
    expect(screen.getByLabelText(/insira o tema desejado/i)).toHaveValue(
      "Esporte: treino, coragem e superação, com a criança no centro da própria história.",
    );
    await user.clear(title);
    await user.type(title, "Lia no gol");
    expect(title).toHaveValue("Lia no gol");
  });

  it("pede o nome do pet e deixa trocar o gênero no livro da Maya", async () => {
    window.history.replaceState(
      {},
      "",
      "/app?tema=pets&campos=nome&titulo=Maya%2C%20Minha%20Cachorra&historia=Amizade&quem=pet&genero=f&heroi=Maya",
    );
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    expect(screen.getByLabelText(/nome do pet/i)).toHaveValue("");
    expect(screen.getByLabelText(/idade do pet/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/nome do protagonista/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^feminino$/i, pressed: true })).toBeInTheDocument();
    expect(screen.getByText(/foto de um ou mais personagens/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^masculino$/i }));
    expect(screen.getByRole("button", { name: /^masculino$/i, pressed: true })).toBeInTheDocument();
    await user.type(screen.getByLabelText(/nome do pet/i), "Thor");
    expect(screen.getByText(/thor, minha cachorra/i)).toBeInTheDocument();
  });

  it("pede a criança e o pet quando o livro tem os dois", async () => {
    window.history.replaceState(
      {},
      "",
      "/app?tema=pets&campos=nome&titulo=Lucas%20e%20seu%20amigo%20Theo&quem=crianca&genero=m&quem2=pet&genero2=m&heroi=Lucas&heroi2=Theo",
    );
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    expect(screen.getByLabelText(/nome do protagonista/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/nome do pet/i)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /^masculino$/i, pressed: true })).toHaveLength(2);
  });

  it("troca o primo para prima quando a família escolhe feminino", async () => {
    window.history.replaceState(
      {},
      "",
      "/app?tema=family_love&campos=nome&titulo=Enzo%2C%20Meu%20Primo&quem=primo&genero=m&heroi=Enzo",
    );
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    expect(screen.getByLabelText(/nome do primo/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /^feminino$/i }));
    expect(screen.getByLabelText(/nome da prima/i)).toBeInTheDocument();
  });
});

describe("Studio a11y", () => {
  it("marca fluxos principais com landmark, alert e tabs", async () => {
    state.credits = 10;
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveAttribute("id", "studio-main");
    expect(screen.getByRole("heading", { name: /crie a sua história/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/nome do protagonista/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/título do livro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/insira o tema desejado/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/selecionar foto do protagonista/i)).toBeInTheDocument();

    await user.type(screen.getByLabelText(/nome do protagonista/i), "Lila");
    await user.type(screen.getByLabelText(/^idade$/i), "5");
    await user.type(screen.getByLabelText(/título do livro/i), "Lila e as estrelas");
    await user.type(screen.getByLabelText(/insira o tema desejado/i), "Aventura no espaço");
    const fileInput = screen.getByTestId("studio-photo-input");
    await user.upload(fileInput, new File(["x"], "foto.jpg", { type: "image/jpeg" }));
    await user.click(screen.getByRole("button", { name: /^feminino$/i }));
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(screen.getByRole("button", { name: /próxima página/i }));
    await user.click(screen.getByRole("button", { name: /gerar o livro/i }));

    const sent = await screen.findByTestId("studio-order-sent");
    expect(sent).toHaveTextContent(/projeto criado/i);
    expect(screen.getByTestId("studio-generate-preview")).toBeInTheDocument();
    expect(screen.getByTestId("studio-generate-story")).toBeInTheDocument();
  });
});

describe("Polling do estúdio", () => {
  it("não recria o interval a cada update de jobs", async () => {
    state.credits = 10;
    const spy = vi.spyOn(window, "setInterval");
    const user = userEvent.setup();
    renderApp("/app");
    await openBook(user);

    await user.type(screen.getByLabelText(/nome do protagonista/i), "Lila");
    await user.type(screen.getByLabelText(/^idade$/i), "5");
    await user.type(screen.getByLabelText(/título do livro/i), "Lila e as estrelas");
    await user.type(screen.getByLabelText(/insira o tema desejado/i), "Aventura no espaço");
    await user.upload(screen.getByTestId("studio-photo-input"), new File(["x"], "foto.jpg", { type: "image/jpeg" }));
    await user.click(screen.getByRole("button", { name: /^feminino$/i }));
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(screen.getByRole("button", { name: /próxima página/i }));
    await user.click(screen.getByRole("button", { name: /gerar o livro/i }));
    const sent = await screen.findByTestId("studio-order-sent");
    expect(sent).toHaveTextContent(/projeto criado/i);
    expect(screen.getByTestId("studio-generate-preview")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /gerar história com ia/i })).toBeInTheDocument();

    const pollTimers = spy.mock.calls.filter((c) => c[1] === 2500);
    expect(pollTimers.length).toBeLessThanOrEqual(2);
  }, 20000);
});

describe("Prévia automática", () => {
  it("dispara startPreview com brief ao clicar Gerar prévia", async () => {
    state.credits = 20;
    const preview = vi.spyOn(api, "startPreview");
    const user = userEvent.setup();
    render(<Studio />);
    await openBook(user);

    await user.type(screen.getByLabelText(/nome do protagonista/i), "Lila");
    await user.type(screen.getByLabelText(/^idade$/i), "5");
    await user.type(screen.getByLabelText(/título do livro/i), "Lila e as estrelas");
    await user.type(screen.getByLabelText(/insira o tema desejado/i), "Aventura no espaço");
    await user.upload(
      screen.getByTestId("studio-photo-input"),
      new File(["x"], "foto.jpg", { type: "image/jpeg" }),
    );
    await user.click(screen.getByRole("button", { name: /^feminino$/i }));
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(screen.getByRole("button", { name: /próxima página/i }));
    await user.click(screen.getByRole("button", { name: /gerar o livro/i }));
    await screen.findByTestId("studio-order-sent");

    await user.click(screen.getByTestId("studio-generate-preview"));
    expect(preview).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ brief: expect.stringMatching(/Lila|estrelas|espaço/i) }),
    );
    expect(await screen.findByText("AVATAR")).toBeInTheDocument();
  });

  it("MSW encadeia avatar → story → ebook → video na prévia", async () => {
    state.credits = 20;
    const p = {
      id: "proj-preview",
      status: "CREATED",
      style: "cartoon",
      story_text: null as string | null,
      ebook_url: null as string | null,
      video_url: null as string | null,
      narrated_video_url: null as string | null,
      character_approved_at: null as string | null,
      book_approved_at: null as string | null,
      print_requested_at: null as string | null,
      print_status: null as string | null,
      created_at: new Date().toISOString(),
    };
    state.projects.set(p.id, p);
    state.jobs.set(p.id, []);

    await api.startPreview(p.id, { brief: "aventura" });
    // Avança a cadeia via listJobs (cada call faz advance nos jobs ativos).
    for (let i = 0; i < 8; i += 1) {
      await api.listJobs(p.id);
    }
    const jobs = await api.listJobs(p.id);
    expect(jobs.some((j) => j.type === "AVATAR" && j.status === "DONE")).toBe(true);
    expect(jobs.some((j) => j.type === "STORY" && j.status === "DONE")).toBe(true);
    expect(jobs.some((j) => j.type === "EBOOK" && j.status === "DONE")).toBe(true);
    expect(jobs.some((j) => j.type === "VIDEO" && j.status === "DONE")).toBe(true);
    const project = await api.getProject(p.id);
    expect(project.story_text).toMatch(/Pagina/i);
    expect(project.ebook_url).toBeTruthy();
    expect(project.video_url).toBeTruthy();
    expect(project.character_approved_at).toBeTruthy();
    expect(project.book_approved_at).toBeTruthy();
  });
});
