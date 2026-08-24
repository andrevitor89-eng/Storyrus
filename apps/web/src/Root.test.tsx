import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppRoutes } from "./Root";
import { LangProvider } from "./i18n";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <LangProvider>
        <AppRoutes />
      </LangProvider>
    </MemoryRouter>,
  );
}

describe("rotas do site", () => {
  it("mostra 404 em rota desconhecida em vez da home em branco", () => {
    renderAt("/nao-existe");
    expect(screen.getByRole("heading", { name: /página não encontrada/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /voltar para o início/i })).toHaveAttribute("href", "/");
  });

  it("renderiza privacidade e termos", () => {
    renderAt("/privacidade");
    expect(screen.getByRole("heading", { name: /política de privacidade/i })).toBeInTheDocument();
    expect(screen.getByText(/não usamos a imagem para divulgação/i)).toBeInTheDocument();
  });

  it("alias /privacy aponta para a mesma política", () => {
    renderAt("/privacy");
    expect(screen.getByRole("heading", { name: /política de privacidade/i })).toBeInTheDocument();
  });

  it("renderiza termos com aviso sobre foto de criança", () => {
    renderAt("/termos");
    expect(screen.getByRole("heading", { name: /termos de uso/i })).toBeInTheDocument();
    expect(screen.getByText(/pai, mãe ou responsável/i)).toBeInTheDocument();
  });

  it("footer da home em pt-BR, com links legais", () => {
    renderAt("/");
    expect(screen.getByText(/onde memórias viram magia/i)).toBeInTheDocument();
    expect(screen.queryByText(/where memories become magic/i)).not.toBeInTheDocument();
    const footer = screen.getByRole("contentinfo");
    expect(footer).toHaveTextContent(/privacidade/i);
    expect(footer).toHaveTextContent(/termos/i);
  });
});
