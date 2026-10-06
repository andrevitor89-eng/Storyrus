import { describe, expect, it, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AppRoutes } from "./Root";
import { Usage } from "./Usage";
import { Pedidos } from "./Pedidos";
import { Usuarios } from "./Usuarios";

describe("Pedidos", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("abre o pedido detalhado depois da senha", async () => {
    const user = userEvent.setup();
    render(<Pedidos />);
    await user.type(screen.getByLabelText(/senha/i), "segredo");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByRole("heading", { name: /novo livro story r us realista/i })).toBeInTheDocument();
    const detail = screen.getByTestId("order-detail");
    expect(detail).toHaveTextContent("Matteo");
    expect(detail).toHaveTextContent("Português");
    expect(detail).toHaveTextContent("Matteo e o vale dos dinossauros");
    expect(detail).toHaveTextContent("Fotos anexadas");
    expect(detail).toHaveTextContent("Idade");
    expect(detail).toHaveTextContent("6");
    expect(detail).toHaveTextContent("M — 20 × 20 cm");
    expect(detail).toHaveTextContent("Capa dura");
    expect(detail).toHaveTextContent("Realista");
    expect(detail).toHaveTextContent("SR-TESTE001");
    expect(detail).toHaveTextContent("AA123BR");
    expect(detail.querySelector("img")).toHaveAttribute("src", "https://fotos.test/crianca.jpg");
    expect(detail.querySelector("a")).toHaveAttribute("href", "https://fotos.test/crianca.jpg");
  });
});

describe("Painel /usuarios", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("rota /usuarios nao cai na landing", async () => {
    render(
      <MemoryRouter initialEntries={["/usuarios"]}>
        <AppRoutes />
      </MemoryRouter>,
    );
    expect(await screen.findByRole("heading", { name: /^usuários$/i })).toBeInTheDocument();
    expect(screen.queryByText(/escolha um livro/i)).not.toBeInTheDocument();
  });

  it("pede senha e mostra contas depois do ok", async () => {
    const user = userEvent.setup();
    render(<Usuarios />);
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument();

    await user.type(screen.getByLabelText(/senha/i), "errada");
    await user.click(screen.getByRole("button", { name: /entrar/i }));
    expect(await screen.findByText(/senha inválida/i)).toBeInTheDocument();

    await user.clear(screen.getByLabelText(/senha/i));
    await user.type(screen.getByLabelText(/senha/i), "segredo");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByText(/2 no total/i)).toBeInTheDocument();
    expect(screen.getByText("ana@example.com")).toBeInTheDocument();
    expect(screen.getByText("bruno@example.com")).toBeInTheDocument();
    expect(screen.getByText("Ana Souza")).toBeInTheDocument();
    expect(screen.getByText("12 créditos")).toBeInTheDocument();
    expect(screen.getByRole("list", { name: /lista de usuários/i })).toBeInTheDocument();
    const nav = screen.getByTestId("owner-nav");
    expect(nav).toHaveTextContent("Gastos");
    expect(nav).toHaveTextContent("Pedidos");
    expect(nav.querySelector('a[aria-current="page"]')).toHaveAttribute("href", "/usuarios");
  });

  it("abre os dados do usuario e permite editar", async () => {
    const user = userEvent.setup();
    render(<Usuarios />);
    await user.type(screen.getByLabelText(/senha/i), "segredo");
    await user.click(screen.getByRole("button", { name: /entrar/i }));
    expect(await screen.findByText(/2 no total/i)).toBeInTheDocument();

    await user.click(screen.getByTestId("owner-user-open-u1"));
    expect(await screen.findByTestId("owner-user-street")).toHaveValue("Avenida Paulista");
    expect(screen.getByTestId("owner-user-city")).toHaveValue("Sao Paulo");
    expect(screen.getByTestId("owner-user-credits")).toHaveValue(12);

    await user.clear(screen.getByTestId("owner-user-full-name"));
    await user.type(screen.getByTestId("owner-user-full-name"), "Ana Silva");
    await user.clear(screen.getByTestId("owner-user-credits"));
    await user.type(screen.getByTestId("owner-user-credits"), "40");
    await user.click(screen.getByTestId("owner-user-save"));

    expect(await screen.findByTestId("owner-user-saved")).toHaveTextContent(/salvas/i);
    expect(screen.getByText("Ana Silva")).toBeInTheDocument();
    expect(screen.getByText("40 créditos")).toBeInTheDocument();
    expect(screen.getByText("bruno@example.com")).toBeInTheDocument();
    expect(screen.getByRole("list", { name: /lista de usuários/i })).toBeInTheDocument();
  });

  it("mantem a lista visivel se o detalhe da API ainda nao existir", async () => {
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("./test/server");
    server.use(
      http.get("*/v1/users/:id", () =>
        HttpResponse.json({ detail: "Not Found" }, { status: 404 }),
      ),
    );
    const user = userEvent.setup();
    render(<Usuarios />);
    await user.type(screen.getByLabelText(/senha/i), "segredo");
    await user.click(screen.getByRole("button", { name: /entrar/i }));
    expect(await screen.findByText("ana@example.com")).toBeInTheDocument();

    await user.click(screen.getByTestId("owner-user-open-u1"));

    expect(screen.getByRole("list", { name: /lista de usuários/i })).toBeInTheDocument();
    expect(screen.getByText("ana@example.com")).toBeInTheDocument();
    expect(screen.getByText("bruno@example.com")).toBeInTheDocument();
    expect(screen.getByTestId("owner-user-full-name")).toHaveValue("Ana Souza");
    expect(screen.getByTestId("owner-user-credits")).toHaveValue(12);
    expect(screen.queryByText(/falha ao abrir/i)).not.toBeInTheDocument();
  });

  it("filtra a lista e exclui um usuario depois da confirmacao", async () => {
    const user = userEvent.setup();
    render(<Usuarios />);
    await user.type(screen.getByLabelText(/senha/i), "segredo");
    await user.click(screen.getByRole("button", { name: /entrar/i }));
    expect(await screen.findByText("ana@example.com")).toBeInTheDocument();

    await user.type(screen.getByTestId("owner-user-search"), "bruno");
    expect(screen.getByText("bruno@example.com")).toBeInTheDocument();
    expect(screen.queryByText("ana@example.com")).not.toBeInTheDocument();

    await user.clear(screen.getByTestId("owner-user-search"));
    expect(screen.getByText("ana@example.com")).toBeInTheDocument();

    await user.click(screen.getByTestId("owner-user-open-u1"));
    await user.click(screen.getByTestId("owner-user-delete"));
    expect(screen.getByText(/não volta atrás/i)).toBeInTheDocument();
    await user.click(screen.getByTestId("owner-user-delete-confirm"));

    expect(await screen.findByText(/1 no total/i)).toBeInTheDocument();
    expect(screen.queryByText("ana@example.com")).not.toBeInTheDocument();
    expect(screen.getByText("bruno@example.com")).toBeInTheDocument();
    expect(screen.queryByTestId("owner-user-detail")).not.toBeInTheDocument();
  });
});

describe("Painel /gastos", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("rota /gastos nao cai na landing", async () => {
    render(
      <MemoryRouter initialEntries={["/gastos"]}>
        <AppRoutes />
      </MemoryRouter>,
    );
    expect(
      await screen.findByRole("heading", { name: /gastos da plataforma/i }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/escolha um livro/i)).not.toBeInTheDocument();
  });

  it("pede senha e mostra totais depois do ok", async () => {
    const user = userEvent.setup();
    render(<Usage />);
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument();

    await user.type(screen.getByLabelText(/senha/i), "errada");
    await user.click(screen.getByRole("button", { name: /entrar/i }));
    expect(await screen.findByText(/senha inválida/i)).toBeInTheDocument();

    await user.clear(screen.getByLabelText(/senha/i));
    await user.type(screen.getByLabelText(/senha/i), "segredo");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByText(/hoje/i)).toBeInTheDocument();
    expect(screen.getByText(/ticket médio/i)).toBeInTheDocument();
    expect(screen.getAllByText(/matteo/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/página 3 — geração/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /extrato/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^pedidos$/i })).toBeInTheDocument();
    expect(screen.getByText(/NOVO LIVRO STORY R US REALISTA/)).toBeInTheDocument();
    expect(screen.getByText(/Fotos anexadas: 1 \(arquivo recebido\)/)).toBeInTheDocument();
    expect(screen.getByText(/Projeto p1/)).toBeInTheDocument();
  });

  it("mostra alerta de lockout quando a API devolve 429", async () => {
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("./test/server");
    server.use(
      http.get("*/v1/usage", () =>
        HttpResponse.json(
          { detail: "Muitas tentativas; tente mais tarde" },
          { status: 429 },
        ),
      ),
    );
    const user = userEvent.setup();
    render(<Usage />);
    await user.type(screen.getByLabelText(/senha/i), "qualquer");
    await user.click(screen.getByRole("button", { name: /entrar/i }));
    expect(await screen.findByText(/muitas tentativas/i)).toBeInTheDocument();
  });

  it("mostra alertas de custo quando a API devolve anomalies", async () => {
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("./test/server");
    server.use(
      http.get("*/v1/usage", () =>
        HttpResponse.json({
          timezone: "America/Sao_Paulo",
          from_at: new Date().toISOString(),
          to_at: new Date().toISOString(),
          today_usd: 9.5,
          month_usd: 9.5,
          range_usd: 9.5,
          books_count: 0,
          avg_book_usd: null,
          by_type: [],
          by_provider: [],
          books: [],
          recent_jobs: [],
          events: [],
          events_count: 0,
          daily_spend_usd_ceiling: 10,
          anomalies: [
            {
              kind: "daily_usd_warn",
              severity: "warn",
              message: "Burn do dia em 95% do teto (9.5000 / 10.0000)",
            },
          ],
        }),
      ),
    );
    const user = userEvent.setup();
    render(<Usage />);
    await user.type(screen.getByLabelText(/senha/i), "segredo");
    await user.click(screen.getByRole("button", { name: /entrar/i }));
    expect(await screen.findByRole("heading", { name: /alertas de custo/i })).toBeInTheDocument();
    expect(screen.getByText(/95% do teto/i)).toBeInTheDocument();
  });
});
