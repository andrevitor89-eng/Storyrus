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

  it("mostra mensagem pt-BR no campo nome vazio", () => {
    renderAuth(<Register />);
    const name = screen.getByLabelText(/seu nome/i) as HTMLInputElement;
    name.dispatchEvent(new Event("invalid", { bubbles: true }));
    expect(name.validationMessage).toBe("Preencha este campo.");
  });

  it("mostra mensagem pt-BR no e-mail do login", () => {
    renderAuth(<Login />);
    const email = screen.getByLabelText(/e-mail/i) as HTMLInputElement;
    email.dispatchEvent(new Event("invalid", { bubbles: true }));
    expect(email.validationMessage).toBe("Preencha este campo.");
  });

  it("alterna as mensagens para inglês", async () => {
    const user = userEvent.setup();
    renderAuth(<Register />);
    await user.click(screen.getByRole("button", { name: "EN" }));
    const name = screen.getByLabelText(/your name/i) as HTMLInputElement;
    name.dispatchEvent(new Event("invalid", { bubbles: true }));
    expect(name.validationMessage).toBe("Please fill out this field.");
  });
});
