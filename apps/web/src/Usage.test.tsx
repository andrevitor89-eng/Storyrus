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

  it("rota /gastos nao cai na landing", () => {
    render(
      <MemoryRouter initialEntries={["/gastos"]}>
        <AppRoutes />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: /gastos da plataforma/i })).toBeInTheDocument();
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
    expect(screen.getByText(/matteo/i)).toBeInTheDocument();
  });
});
