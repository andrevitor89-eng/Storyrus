import { describe, expect, it, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AppRoutes } from "./Root";
import { Usage } from "./Usage";

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
