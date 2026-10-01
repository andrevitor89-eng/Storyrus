import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { api } from "./api";
import { state } from "./test/server";

afterEach(() => {
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
});

describe("Fluxo E2E (sem login)", () => {
  it("criar livro só confirma que o pedido foi enviado", async () => {
    state.credits = 10;
    const user = userEvent.setup();
    const { container } = render(<App />);

    expect(await screen.findByText(/créditos: 10/i)).toBeInTheDocument();

    await user.type(screen.getByLabelText(/nome da criança/i), "Lila");
    await user.type(screen.getByLabelText(/idade/i), "5");
    await user.type(screen.getByLabelText(/título do livro/i), "Lila e as estrelas");
    await user.type(screen.getByLabelText(/insira o tema desejado/i), "Aventura no espaço");
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["x"], "foto.jpg", { type: "image/jpeg" });
    await user.upload(fileInput, file);
    await user.click(screen.getByRole("checkbox", { name: /responsável legal/i }));
    await user.click(screen.getByRole("button", { name: /criar livro/i }));

    const sent = await screen.findByTestId("studio-order-sent");
    expect(sent).toHaveTextContent(/pedido enviado/i);
    expect(sent).toHaveTextContent(/nossa equipe entrará em contato/i);
    expect(screen.queryByRole("button", { name: /gerar história com ia/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /^projeto$/i })).not.toBeInTheDocument();
  });

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
