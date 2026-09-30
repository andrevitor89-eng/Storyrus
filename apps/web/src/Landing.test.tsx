import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { Landing } from "./Landing";
import { AppRoutes } from "./Root";

function renderLanding() {
  return render(
    <MemoryRouter>
      <Landing />
    </MemoryRouter>,
  );
}

beforeAll(() => {
  class IO {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  vi.stubGlobal("IntersectionObserver", IO);

  Object.defineProperty(HTMLMediaElement.prototype, "play", {
    configurable: true,
    value: vi.fn().mockResolvedValue(undefined),
  });
  Object.defineProperty(HTMLMediaElement.prototype, "pause", {
    configurable: true,
    value: vi.fn(),
  });
});

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
  document.documentElement.lang = "en";
});

afterEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

describe("Landing — idioma", () => {
  it("inicia em PT e troca copy/document.lang/localStorage ao clicar EN e ES", async () => {
    const user = userEvent.setup();
    renderLanding();

    expect(await screen.findByTestId("landing-hero-cta")).toHaveTextContent(/criar meu livro/i);
    expect(screen.getByRole("heading", { name: /perguntas frequentes/i })).toBeInTheDocument();

    await user.click(screen.getByTestId("landing-lang-en"));
    expect(screen.getByTestId("landing-hero-cta")).toHaveTextContent(/create my book/i);
    expect(screen.getByRole("heading", { name: /frequently asked questions/i })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("en");
    expect(localStorage.getItem("lang")).toBe("en");
    expect(screen.getByTestId("landing-lang-en")).toHaveClass("on");
    expect(screen.getByTestId("landing-lang-pt")).not.toHaveClass("on");

    await user.click(screen.getByTestId("landing-lang-es"));
    expect(screen.getByTestId("landing-hero-cta")).toHaveTextContent(/crear mi libro/i);
    expect(screen.getByRole("heading", { name: /preguntas frecuentes/i })).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("es");
    expect(localStorage.getItem("lang")).toBe("es");
    expect(screen.getByTestId("landing-lang-es")).toHaveClass("on");
  });

  it("restaura idioma salvo no localStorage", async () => {
    localStorage.setItem("lang", "en");
    renderLanding();

    expect(await screen.findByTestId("landing-hero-cta")).toHaveTextContent(/create my book/i);
    expect(document.documentElement.lang).toBe("en");
    expect(screen.getByTestId("landing-lang-en")).toHaveClass("on");
  });
});

describe("Landing — tema", () => {
  it("alterna data-theme e persiste em localStorage", async () => {
    const user = userEvent.setup();
    renderLanding();

    await screen.findByTestId("landing-hero-cta");
    expect(screen.getByRole("button", { name: /alternar tema/i })).toHaveTextContent(/claro/i);
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(localStorage.getItem("theme")).toBe("dark");

    await user.click(screen.getByRole("button", { name: /alternar tema/i }));
    expect(screen.getByRole("button", { name: /alternar tema/i })).toHaveTextContent(/escuro/i);
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(localStorage.getItem("theme")).toBe("light");

    await user.click(screen.getByRole("button", { name: /alternar tema/i }));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("restaura tema claro do localStorage", async () => {
    localStorage.setItem("theme", "light");
    renderLanding();

    await screen.findByTestId("landing-hero-cta");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });
});

describe("Landing — promessa", () => {
  it("destaca presente no título e usa a nova copy em PT", async () => {
    renderLanding();

    await screen.findByTestId("landing-hero-cta");
    const heading = screen.getByRole("heading", { name: /um presente personalizado para eternizar momentos inesquecíveis/i });
    expect(within(heading).getByText(/^presente$/i)).toHaveClass("promise-mark");
    expect(
      screen.getByText(/da foto à prévia final, cada detalhe é criado com carinho, dando vida a um presente único para toda a vida\./i),
    ).toBeInTheDocument();
  });
});

describe("Landing — avaliações", () => {
  it("mostra a foto segurando o livro com só o nome da criança", async () => {
    renderLanding();

    const reviews = (await screen.findByRole("heading", { name: /o que as famílias dizem/i })).closest("section") as HTMLElement;
    const fotos = [
      "foto-martin-goleiro.jpg",
      "foto-nicolas-maefilho.jpg",
      "foto-emilia-bailarina.jpg",
      "foto-amordemae.jpg",
      "foto-antonio-bicicleta.jpg",
      "foto-mamaepapaimatteo-en.jpg",
      "foto-mariajesus-hockey.jpg",
      "foto-amordebisavo.jpg",
      "foto-facundo-motocross.jpg",
      "foto-natalmemetata.jpg",
      "foto-ester.png",
      "foto-raquel-papai.png",
      "foto-rebeca.png",
      "foto-maya-cachorra-pt.jpg",
      "foto-abigail.png",
      "foto-nanoaventuras.jpg",
      "foto-miriam.png",
      "foto-mako-amigofiel.jpg",
      "foto-noe.png",
    ];
    fotos.forEach((file, i) => {
      expect(within(reviews).getByTestId(`landing-review-cover-${i}`)).toHaveAttribute("src", expect.stringContaining(file));
    });
    expect(within(reviews).getByTestId("landing-review-name-0")).toHaveTextContent(/^Martin$/);
    expect(within(reviews).getByTestId("landing-review-name-1")).toHaveTextContent(/^Nicolas$/);
    expect(within(reviews).getByTestId("landing-review-name-2")).toHaveTextContent(/^Emilia$/);
    expect(within(reviews).getByTestId("landing-review-name-11")).toHaveTextContent(/^Raquel$/);
    expect(within(reviews).getByTestId("landing-review-name-18")).toHaveTextContent(/^Noé$/);
    expect(within(reviews).queryByTestId("landing-review-cover-19")).not.toBeInTheDocument();
    expect(within(reviews).queryByText(/o Grande Goleiro do Chile/i)).not.toBeInTheDocument();
  });
});

describe("Landing — catálogo", () => {
  it("usa PNG sem fundo de estúdio nas capas 3D e mantém JPG nas capas full-bleed", async () => {
    renderLanding();

    const catalog = (await screen.findByRole("heading", { name: /nossos livros/i })).closest("section") as HTMLElement;
    const imgs = within(catalog).getAllByRole("img");
    const srcs = imgs.map((img) => img.getAttribute("src") ?? "");
    expect(srcs.some((src) => src.includes("capa-nicolas-maefilho.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-amordemae.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-mamaepapaimatteo.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-sofia-alfabeto.png"))).toBe(false);
    expect(srcs.some((src) => src.includes("capa-bruno-animais.png"))).toBe(false);
    expect(srcs.some((src) => src.includes("capa-gael-es.png"))).toBe(false);
    expect(srcs.some((src) => src.includes("capa-matteo-rancho-es.png"))).toBe(false);
    expect(srcs.some((src) => src.includes("capa-ester.png"))).toBe(false);
    expect(srcs.some((src) => src.includes("capa-martin-goleiro.jpg"))).toBe(false);
    expect(srcs.some((src) => src.includes("capa-natalmemetata.jpg"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-amordetia.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-davi-pastor.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-meupai-heroi.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-enzo-primo.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-lucas-max.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-esther-higiene.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-nicolas-maefilho.jpg"))).toBe(false);
    expect(imgs).toHaveLength(14);
  });

  it("mostra os livros realistas com a mesma capa, o valor e sem o resumo", async () => {
    renderLanding();

    const catalog = (await screen.findByRole("heading", { name: /nossos livros/i })).closest("section") as HTMLElement;
    const cards = within(catalog).getAllByTestId("landing-catalog-card");
    expect(within(cards[0]).queryByText(/capa mole ou capa dura/i)).not.toBeInTheDocument();
    expect(within(cards[0]).getByText("Livro 16 páginas")).toBeInTheDocument();
    expect(within(cards[0]).getByText("M - 20 × 20 cm: R$ 177,00.")).toBeInTheDocument();
    expect(within(cards[0]).getByText("P - 15 × 15 cm: R$ 157,00.")).toBeInTheDocument();
    expect(within(cards[0]).getByText("HARD - Capa rígida")).toBeInTheDocument();
    expect(within(cards[0]).getByText(/mais pesada, resistente e durável/i)).toBeInTheDocument();
    expect(within(cards[0]).getByText("SOFT - Capa macia")).toBeInTheDocument();
    expect(within(cards[0]).getByText(/mais leve e flexível/i)).toBeInTheDocument();
    expect(within(catalog).getAllByText("HARD - Capa rígida")).toHaveLength(14);
    expect(cards).toHaveLength(14);
    cards.forEach((card) => {
      expect(card).toHaveAttribute("data-format", "catalog");
      expect(within(card).queryByText(/esporte e coragem/i)).not.toBeInTheDocument();
      expect(within(card).queryByText(/amizade e cuidado/i)).not.toBeInTheDocument();
    });
    expect(within(cards[0]).getByText("Meu Pai, Meu Herói")).toBeInTheDocument();
    expect(within(cards[1]).getByText("Davi, o Menino Pastor")).toBeInTheDocument();
    expect(within(cards[2]).getByText("Enzo, Meu Primo Predileto")).toBeInTheDocument();
    expect(within(cards[0]).getByTestId("landing-catalog-price")).toHaveTextContent("R$ 177,00");
    expect(within(cards[4]).getByTestId("landing-catalog-price")).toHaveTextContent("R$ 177,00");
    expect(within(catalog).queryByText(/Martin, o Grande Goleiro/i)).not.toBeInTheDocument();
    expect(within(catalog).queryByText(/Aniversário Especial de Ester/i)).not.toBeInTheDocument();
    expect(within(catalog).getByText("Amor de Tia")).toBeInTheDocument();
    expect(within(catalog).getByText("Lucas e seu amigo Max")).toBeInTheDocument();
    expect(within(catalog).getByText("Esther e os Superpoderes da Higiene")).toBeInTheDocument();
    expect(cards[0].querySelector(".cat-book img")).toHaveAttribute("src", expect.stringContaining("capa-meupai-heroi.png"));
    expect(cards[1].querySelector(".cat-book img")).toHaveAttribute("src", expect.stringContaining("capa-davi-pastor.png"));
    expect(cards[2].querySelector(".cat-book img")).toHaveAttribute("src", expect.stringContaining("capa-enzo-primo.png"));
    expect(within(cards[0]).getByRole("button", { name: "Hard", pressed: true })).toBeInTheDocument();
    expect(within(cards[0]).getByRole("button", { name: "Soft", pressed: false })).toBeInTheDocument();
    expect(within(cards[0]).getByRole("button", { name: "M", pressed: true })).toBeInTheDocument();
    expect(within(cards[0]).getByRole("button", { name: "P", pressed: false })).toBeInTheDocument();
    expect(within(cards[4]).getByRole("button", { name: "Hard", pressed: true })).toBeInTheDocument();
  });

  it("troca descrição e valor ao escolher capa e tamanho", async () => {
    const user = userEvent.setup();
    renderLanding();

    const catalog = (await screen.findByRole("heading", { name: /nossos livros/i })).closest("section") as HTMLElement;
    const card = within(catalog).getAllByTestId("landing-catalog-card")[0];

    await user.click(within(card).getByRole("button", { name: "Hard" }));
    expect(within(card).getByRole("button", { name: "Hard", pressed: true })).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "Soft", pressed: false })).toBeInTheDocument();
    expect(within(card).getByText("M - 20 × 20 cm: R$ 177,00.")).toBeInTheDocument();
    expect(within(card).getByText("P - 15 × 15 cm: R$ 157,00.")).toBeInTheDocument();
    expect(within(card).getByTestId("landing-catalog-price")).toHaveTextContent("R$ 177,00");

    await user.click(within(card).getByRole("button", { name: "Soft" }));
    expect(within(card).getByRole("button", { name: "Soft", pressed: true })).toBeInTheDocument();
    expect(within(card).getByTestId("landing-personalize")).toHaveAttribute("href", expect.stringContaining("capa=soft"));

    await user.click(within(card).getByRole("button", { name: "P" }));
    expect(within(card).getByRole("button", { name: "P", pressed: true })).toBeInTheDocument();
    expect(within(card).getByTestId("landing-personalize")).toHaveAttribute("href", expect.stringContaining("tamanho=P"));
    expect(within(card).getByRole("button", { name: "M", pressed: false })).toBeInTheDocument();
    expect(within(card).getByText("M - 20 × 20 cm: R$ 177,00.")).toBeInTheDocument();
    expect(within(card).getByText("P - 15 × 15 cm: R$ 157,00.")).toBeInTheDocument();
    expect(within(card).getByTestId("landing-catalog-price")).toHaveTextContent("R$ 157,00");
  });

  it("troca a capa localizada de Amor de Mãe ao mudar o idioma", async () => {
    const user = userEvent.setup();
    renderLanding();

    const catalog = (await screen.findByRole("heading", { name: /nossos livros/i })).closest("section") as HTMLElement;
    const ptSrcs = within(catalog).getAllByRole("img").map((img) => img.getAttribute("src") ?? "");
    expect(ptSrcs.some((src) => src.includes("capa-amordemae.png"))).toBe(true);
    expect(ptSrcs.some((src) => src.includes("capa-amordemae-en.png"))).toBe(false);

    await user.click(screen.getByTestId("landing-lang-en"));
    const enCatalog = (await screen.findByRole("heading", { name: /our books/i })).closest("section") as HTMLElement;
    const enSrcs = within(enCatalog).getAllByRole("img").map((img) => img.getAttribute("src") ?? "");
    expect(enSrcs.some((src) => src.includes("capa-amordemae-en.png"))).toBe(true);
    expect(enSrcs.some((src) => src.includes("capa-ester-en.png"))).toBe(false);

    await user.click(screen.getByTestId("landing-lang-es"));
    const esCatalog = (await screen.findByRole("heading", { name: /nuestros libros/i })).closest("section") as HTMLElement;
    const esSrcs = within(esCatalog).getAllByRole("img").map((img) => img.getAttribute("src") ?? "");
    expect(esSrcs.some((src) => src.includes("capa-amordemae-es.png"))).toBe(true);
    expect(esSrcs.some((src) => src.includes("capa-ester-es.png"))).toBe(false);
  });

  it("aponta os livros realistas para os temas existentes", async () => {
    renderLanding();
    await screen.findByTestId("landing-hero-cta");

    const personalize = screen.getAllByTestId("landing-personalize");
    expect(personalize).toHaveLength(14);
    expect(personalize[0].getAttribute("href")).toContain("tema=fathers_day");
    expect(personalize[0].getAttribute("href")).toContain("campos=nome");
    expect(personalize[0].getAttribute("href")).toContain("tamanho=M");
    expect(personalize[0].getAttribute("href")).toContain("capa=hard");
    expect(personalize[0].getAttribute("href")).toContain("modo=realista");
    expect(personalize[0].getAttribute("href")).toContain("titulo=");
    expect(personalize[0].getAttribute("href")).not.toContain("heroi=");
    expect(decodeURIComponent((personalize[0].getAttribute("href") ?? "").replace(/\+/g, " "))).toContain("Papai herói");
    expect(personalize[1].getAttribute("href")).toContain("tema=adventure");
    expect(personalize[2].getAttribute("href")).toContain("tema=family_love");
    expect(personalize[10].getAttribute("href")).toContain("tema=pets");
  });
});

describe("Landing — FAQ", () => {
  it("abre e fecha item; só um fica expandido por vez", async () => {
    const user = userEvent.setup();
    renderLanding();

    const faqSection = (await screen.findByRole("heading", { name: /perguntas frequentes/i })).closest(
      "section",
    ) as HTMLElement;
    const questions = within(faqSection).getAllByRole("button");
    expect(questions.length).toBeGreaterThanOrEqual(2);

    expect(questions[0]).toHaveAttribute("aria-expanded", "false");
    await user.click(questions[0]);
    expect(questions[0]).toHaveAttribute("aria-expanded", "true");
    expect(questions[1]).toHaveAttribute("aria-expanded", "false");

    await user.click(questions[1]);
    expect(questions[0]).toHaveAttribute("aria-expanded", "false");
    expect(questions[1]).toHaveAttribute("aria-expanded", "true");

    await user.click(questions[1]);
    expect(questions[1]).toHaveAttribute("aria-expanded", "false");
  });
});

describe("Landing — menu mobile e abas do hero", () => {
  it("fecha dropdown desktop com clique fora e Escape", async () => {
    const user = userEvent.setup();
    renderLanding();

    await screen.findByTestId("landing-hero-cta");
    const catButtons = screen.getAllByRole("button").filter((button) => button.getAttribute("aria-haspopup") === "true");
    expect(catButtons.length).toBeGreaterThan(0);

    fireEvent.mouseEnter(catButtons[0].parentElement as HTMLElement);
    expect(catButtons[0]).toHaveAttribute("aria-expanded", "true");

    await user.click(document.body);
    expect(catButtons[0]).toHaveAttribute("aria-expanded", "false");

    fireEvent.mouseEnter(catButtons[0].parentElement as HTMLElement);
    expect(catButtons[0]).toHaveAttribute("aria-expanded", "true");

    await user.keyboard("{Escape}");
    expect(catButtons[0]).toHaveAttribute("aria-expanded", "false");
  });

  it("abre/fecha o menu e Escape fecha", async () => {
    const user = userEvent.setup();
    renderLanding();

    const menuBtn = await screen.findByTestId("landing-menu");
    const siteMenu = screen.getByTestId("landing-site-menu");
    expect(menuBtn).toHaveAttribute("aria-expanded", "false");
    expect(siteMenu).not.toHaveClass("open");

    await user.click(menuBtn);
    expect(menuBtn).toHaveAttribute("aria-expanded", "true");
    expect(siteMenu).toHaveClass("open");

    await user.keyboard("{Escape}");
    expect(menuBtn).toHaveAttribute("aria-expanded", "false");
    expect(siteMenu).not.toHaveClass("open");
  });

  it("organiza o menu mobile com categorias e acessos rapidos", async () => {
    const user = userEvent.setup();
    renderLanding();

    const menuBtn = await screen.findByTestId("landing-menu");
    const siteMenu = screen.getByTestId("landing-site-menu");

    await user.click(menuBtn);

    expect(within(siteMenu).getByText(/categorias/i)).toBeInTheDocument();
    expect(within(siteMenu).getByText(/acessos r[aá]pidos/i)).toBeInTheDocument();

    const mobileCatButtons = within(siteMenu).getAllByRole("button");
    expect(mobileCatButtons.length).toBeGreaterThan(0);
    expect(mobileCatButtons[0]).toHaveAttribute("aria-expanded", "false");

    await user.click(mobileCatButtons[0]);
    expect(mobileCatButtons[0]).toHaveAttribute("aria-expanded", "true");
    expect(within(siteMenu).getByRole("link", { name: /ver todos/i })).toHaveAttribute("href", "/app");
  });

  it("abre o hero em Nano e duplica a faixa", async () => {
    const user = userEvent.setup();
    renderLanding();

    const cover = await screen.findByTestId("landing-hero-slide-0");
    expect(cover).toHaveAttribute("src", expect.stringContaining("capa-nanoaventuras.jpg"));
    expect(screen.getByTestId("landing-hero-slide-1")).toHaveAttribute("src", expect.stringContaining("pagina-nanoaventuras.jpg"));
    expect(screen.getByTestId("landing-hero-slide-2")).toHaveAttribute("src", expect.stringContaining("foto-nanoaventuras.jpg"));
    expect(screen.getByTestId("landing-hero-slide-3")).toHaveAttribute("src", expect.stringContaining("capa-amordebisavo.jpg"));
    expect(screen.getByTestId("landing-hero-slide-4")).toHaveAttribute("src", expect.stringContaining("pagina-amordebisavo.jpg"));
    expect(screen.getByTestId("landing-hero-slide-5")).toHaveAttribute("src", expect.stringContaining("foto-amordebisavo.jpg"));

    const firstFrame = cover.closest(".hero-slide-frame") as HTMLElement;
    expect(firstFrame).toContainElement(screen.getByTestId("landing-hero-slide-1"));
    expect(firstFrame).toContainElement(screen.getByTestId("landing-hero-slide-2"));
    expect(firstFrame).not.toContainElement(screen.getByTestId("landing-hero-slide-3"));

    const carousel = cover.closest(".hero-carousel") as HTMLElement;
    const natalCovers = [...carousel.querySelectorAll("img")].filter((img) => {
      const src = img.getAttribute("src") ?? "";
      return src.includes("capa-natalmemetata.jpg") && !src.includes("capa-natalmemetata-e");
    });
    expect(natalCovers).toHaveLength(2);
    expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("capa-nanoaventuras.jpg"));
    expect(screen.getByTestId("landing-hero-flip-dot-0")).toHaveAttribute("aria-selected", "true");
    await user.click(screen.getByRole("button", { name: /próxima página/i }));
    await waitFor(() => {
      expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("pagina-nanoaventuras.jpg"));
    }, { timeout: 2200 });
    expect(screen.getByTestId("landing-hero-flip-dot-1")).toHaveAttribute("aria-selected", "true");

    await user.click(screen.getByTestId("landing-hero-flip-dot-2"));
    await waitFor(() => {
      expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("foto-nanoaventuras.jpg"));
    }, { timeout: 2200 });

    await user.click(screen.getByTestId("landing-hero-pick-1"));
    expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("pagina-nanoaventuras.jpg"));

    await user.click(screen.getByTestId("landing-lang-es"));
    const heroImgs = [...carousel.querySelectorAll("img")].map((img) => img.getAttribute("src") ?? "");
    expect(heroImgs.some((src) => src.includes("capa-martin-goleiro"))).toBe(false);
    expect(heroImgs.some((src) => src.includes("capa-emilia-bailarina"))).toBe(false);
    expect(heroImgs.some((src) => src.includes("capa-antonio-bicicleta"))).toBe(false);
    expect(heroImgs.some((src) => src.includes("capa-mariajesus-hockey"))).toBe(false);
    expect(heroImgs.some((src) => src.includes("capa-amordetia.png"))).toBe(true);
    expect(heroImgs.some((src) => src.includes("capa-davi-pastor.png"))).toBe(true);
    expect(heroImgs.some((src) => src.includes("capa-meupai-heroi.png"))).toBe(true);
    expect(heroImgs.some((src) => src.includes("capa-enzo-primo.png"))).toBe(true);
    expect(heroImgs.some((src) => src.includes("capa-lucas-max.png"))).toBe(true);
    expect(heroImgs.some((src) => src.includes("pagina-lucas-max.png"))).toBe(true);
    expect(heroImgs.some((src) => src.includes("foto-lucas-max.png"))).toBe(true);
    expect(heroImgs.some((src) => src.includes("capa-esther-higiene.png"))).toBe(true);
    expect(heroImgs.some((src) => src.includes("pagina-esther-higiene.png"))).toBe(true);
    expect(heroImgs.some((src) => src.includes("foto-esther-higiene.png"))).toBe(true);

    expect(screen.getByTestId("landing-hero-slide-0")).toHaveAttribute("src", expect.stringContaining("capa-nanoaventuras-es.jpg"));
    expect(screen.getByTestId("landing-hero-slide-1")).toHaveAttribute("src", expect.stringContaining("pagina-nanoaventuras-es.jpg"));
    expect(screen.getByTestId("landing-hero-slide-2")).toHaveAttribute("src", expect.stringContaining("foto-nanoaventuras-es.jpg"));
    expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("pagina-nanoaventuras-es.jpg"));
  });

  it("coloca o texto Uma foto abaixo do titulo Transforme", async () => {
    renderLanding();

    const heading = await screen.findByRole("heading", { level: 1 });
    const intro = heading.closest(".khero-intro") as HTMLElement;
    expect(intro).toBeTruthy();
    expect(intro.firstElementChild).toBe(heading);
    expect(intro).toHaveTextContent(/uma foto\. uma história\. uma memória eterna/i);
    expect(heading.nextElementSibling).toHaveTextContent(/uma foto/i);
  });
});

describe("Landing — CTAs e links", () => {
  it("CTAs principais apontam para /app", async () => {
    renderLanding();

    expect(await screen.findByTestId("landing-hero-cta")).toHaveAttribute("href", "/app");
    expect(screen.getByTestId("landing-header-cta")).toHaveAttribute("href", "/app");
    expect(screen.getByTestId("landing-mobile-cta")).toHaveAttribute("href", "/app");
  });

  it("footer liga privacidade e termos", async () => {
    renderLanding();
    await screen.findByTestId("landing-hero-cta");

    expect(screen.getByRole("link", { name: /^privacidade$/i })).toHaveAttribute("href", "/privacidade");
    expect(screen.getByRole("link", { name: /^termos$/i })).toHaveAttribute("href", "/termos");
  });

  it("botão Personalizar leva tema no query", async () => {
    renderLanding();
    await screen.findByTestId("landing-hero-cta");

    const personalize = screen.getAllByTestId("landing-personalize");
    expect(personalize.length).toBeGreaterThan(0);
    for (const link of personalize) {
      expect(link.getAttribute("href")).toMatch(/^\/app\?tema=/);
    }
  });

  it("ordena as seções e aponta o Instagram para storyr.us", async () => {
    renderLanding();
    await screen.findByTestId("landing-hero-cta");

    const order = ["como", "catalogo", "promessa", "videos", "reviews", "faq"];
    const nodes = order.map((id) => document.getElementById(id));
    expect(nodes.every(Boolean)).toBe(true);
    for (let i = 0; i < nodes.length - 1; i++) {
      expect(nodes[i]!.compareDocumentPosition(nodes[i + 1]!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }

    expect(screen.getByRole("link", { name: /@storyr\.us/i })).toHaveAttribute("href", "https://www.instagram.com/storyr.us/");
    expect(screen.queryByRole("link", { name: /^cartoon$/i })).not.toBeInTheDocument();
    expect(screen.getByText(/escolha o tema e o formato do livro/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^a criança$/i })).toBeInTheDocument();
    expect(screen.queryByText(/dicas para a foto perfeita/i)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /envie a foto e defina os detalhes/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^dados do livro$/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /criamos o personagem e a história/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /você recebe e aprova o livro/i })).toBeInTheDocument();
    const como = document.getElementById("como") as HTMLElement;
    for (const file of ["como-envia.jpg", "como-cria.jpg", "como-recebe.jpg"]) {
      expect(como.querySelector(`img[alt][src*="${file}"]`)).toBeTruthy();
    }
    expect(como.querySelector(".howex-card-receive")).toBeTruthy();
  });

  it("mostra os livros do tema ao passar o mouse no submenu", () => {
    renderLanding();
    const panel = document.querySelector("#cat-panel") as HTMLElement;
    const nav = document.querySelector(".kcats") as HTMLElement;
    expect(within(nav).getByRole("button", { name: /^categorias$/i })).toBeInTheDocument();
    expect(within(nav).queryByRole("button", { name: /^aventuras$/i })).not.toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: /^como funciona$/i })).toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: /^vídeos$/i })).toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: /^avaliações$/i })).toBeInTheDocument();
    const subs = panel.querySelector(".kcat-subs") as HTMLElement;
    const princesas = within(panel).getByRole("link", { name: /^princesas$/i });
    const princesasHref = decodeURIComponent((princesas.getAttribute("href") ?? "").replace(/\+/g, " "));
    expect(princesasHref).toContain("tema=princess");
    expect(princesasHref).toContain("Emilia e os Primeiros Passos da Bailarina");
    expect(princesasHref).toContain("heroi=Emilia");
    expect(within(panel).getByRole("link", { name: /^esportes$/i })).toHaveAttribute("href", "/app?tema=sport");
    fireEvent.mouseEnter(princesas);
    const feats = screen.getByTestId("landing-cat-feats");
    expect(within(feats).getByRole("link", { name: /emilia/i })).toBeInTheDocument();
    expect(within(feats).queryByRole("link", { name: /nano/i })).not.toBeInTheDocument();

    fireEvent.mouseEnter(within(subs).getByRole("link", { name: /^esportes$/i }));
    expect(within(feats).getByRole("link", { name: /martin/i })).toBeInTheDocument();
    expect(within(feats).getByRole("link", { name: /cristobal/i })).toBeInTheDocument();
    expect(within(feats).queryByRole("link", { name: /emilia/i })).not.toBeInTheDocument();

    fireEvent.mouseEnter(within(panel).getByRole("link", { name: /^páscoa$/i }));
    expect(within(feats).getByText(/ainda não temos um exemplo neste tema/i)).toBeInTheDocument();
  });

  it("rota /cartoon não abre a landing", async () => {
    render(
      <MemoryRouter initialEntries={["/cartoon"]}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(await screen.findByTestId("not-found-title")).toHaveTextContent(/página não encontrada/i);
    expect(screen.queryByTestId("landing-hero-cta")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /^cartoon$/i })).not.toBeInTheDocument();
  });
});
