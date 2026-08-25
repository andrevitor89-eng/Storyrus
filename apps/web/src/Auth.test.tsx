import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { Login, Register } from "./Auth";
import { LangProvider } from "./i18n";

function renderAuth(ui: ReactElement) {
  return render(
    <MemoryRouter>
      <LangProvider>{ui}</LangProvider>
    </MemoryRouter>,
  );
}

describe("cadastro e login", () => {
  it("exige o nome no cadastro", () => {
    renderAuth(<Register />);
    const name = screen.getByLabelText(/seu nome/i);
    expect(name).toBeRequired();
  });

  it("mostra mensagem pt-BR no campo nome vazio", async () => {
    const user = userEvent.setup();
    renderAuth(<Register />);
    await user.click(screen.getByRole("button", { name: /começar/i }));
    const alerts = screen.getAllByRole("alert");
    expect(alerts[0]).toHaveTextContent("Preencha este campo.");
    expect(screen.getByLabelText(/seu nome/i)).toHaveFocus();
  });

  it("envio vazio valida o nome antes do e-mail", async () => {
    const user = userEvent.setup();
    renderAuth(<Register />);
    await user.click(screen.getByRole("button", { name: /começar/i }));
    expect(screen.getByRole("alert")).toHaveTextContent("Preencha este campo.");
    expect(screen.getByLabelText(/seu nome/i)).toHaveFocus();
  });

  it("mostra mensagem pt-BR no e-mail do login", async () => {
    const user = userEvent.setup();
    renderAuth(<Login />);
    await user.click(screen.getByRole("button", { name: /^entrar$/i }));
    expect(screen.getByRole("alert")).toHaveTextContent("Preencha este campo.");
    expect(screen.getByLabelText(/e-mail/i)).toHaveFocus();
  });

  it("alterna as mensagens para inglês", async () => {
    const user = userEvent.setup();
    renderAuth(<Register />);
    await user.click(screen.getByRole("button", { name: "EN" }));
    await user.click(screen.getByRole("button", { name: /get started/i }));
    expect(screen.getByRole("alert")).toHaveTextContent("Please fill out this field.");
  });
});
