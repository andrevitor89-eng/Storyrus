import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { state } from "./test/server";

describe("Fluxo E2E (sem login)", () => {
  it("estúdio → projeto → foto gera personagem → história", async () => {
    state.credits = 10;
    const user = userEvent.setup();
    const { container } = render(<App />);

    // o estúdio carrega direto, sem tela de login
    expect(await screen.findByText(/créditos: 10/i)).toBeInTheDocument();

    // escolhe estilo e cria projeto
    await user.click(screen.getByRole("button", { name: /desenho/i }));
    await user.click(screen.getByRole("button", { name: /criar projeto/i }));
    expect(await screen.findByRole("heading", { name: /^projeto$/i })).toBeInTheDocument();

    // envia a foto -> personagem é gerado automaticamente
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["x"], "foto.jpg", { type: "image/jpeg" });
    await user.upload(fileInput, file);
    await user.click(screen.getByRole("button", { name: /enviar foto/i }));
    expect(await screen.findByText("AVATAR")).toBeInTheDocument();

    // gera a história (modo "inventar com IA")
    await user.click(screen.getByRole("button", { name: /gerar história com ia/i }));
    expect(await screen.findByText("STORY")).toBeInTheDocument();

    // história aparece na plataforma (o mock leva alguns ciclos de polling)
    expect(
      await screen.findByText(/pagina 1: ola/i, undefined, { timeout: 9000 }),
    ).toBeInTheDocument();
  }, 20000);

  it("habilita 'Montar ebook' só depois de foto + história", async () => {
    state.credits = 10;
    const user = userEvent.setup();
    const { container } = render(<App />);

    await screen.findByText(/créditos: 10/i);
    await user.click(screen.getByRole("button", { name: /criar projeto/i }));

    // sem foto/história, o botão de ebook fica desabilitado
    const ebookBtn = await screen.findByRole("button", { name: /montar ebook/i });
    expect(ebookBtn).toBeDisabled();

    // envia foto (gera personagem) e a história
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, new File(["x"], "foto.jpg", { type: "image/jpeg" }));
    await user.click(screen.getByRole("button", { name: /enviar foto/i }));
    await user.click(screen.getByRole("button", { name: /gerar história com ia/i }));
    await screen.findByText(/pagina 1: ola/i, undefined, { timeout: 9000 });

    // agora o ebook pode ser montado
    await waitFor(
      () => expect(screen.getByRole("button", { name: /montar ebook/i })).toBeEnabled(),
      { timeout: 9000 },
    );
  }, 20000);
});
