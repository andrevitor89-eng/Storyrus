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
    expect(srcs.some((src) => src.includes("capa-ester.png"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-martin-goleiro.jpg"))).toBe(false);
    expect(srcs.some((src) => src.includes("capa-natalmemetata.jpg"))).toBe(true);
    expect(srcs.some((src) => src.includes("capa-nicolas-maefilho.jpg"))).toBe(false);
    expect(imgs).toHaveLength(9);
  });

  it("mostra os livros realistas com a mesma capa, o valor e sem o resumo", async () => {
    renderLanding();

    const catalog = (await screen.findByRole("heading", { name: /nossos livros/i })).closest("section") as HTMLElement;
    const cards = within(catalog).getAllByTestId("landing-catalog-card");
    const desc = "Capa dura ou mole, 15 × 15 cm ou 20 × 20 cm. 16 páginas.";
    expect(cards).toHaveLength(9);
    cards.forEach((card) => {
      expect(card).toHaveAttribute("data-format", "catalog");
      expect(within(card).getByText(desc)).toBeInTheDocument();
      expect(within(card).getByTestId("landing-catalog-price")).toHaveTextContent("Sob consulta");
      expect(within(card).queryByText(/esporte e coragem/i)).not.toBeInTheDocument();
    });
    expect(within(catalog).queryByText(/Martin, o Grande Goleiro/i)).not.toBeInTheDocument();
    expect(within(catalog).queryByText(/Aprendendo o Alfabeto/i)).not.toBeInTheDocument();
    expect(cards[0].querySelector(".cat-book img")).toHaveAttribute("src", expect.stringContaining("capa-nicolas-maefilho.png"));
    expect(cards[1].querySelector(".cat-book img")).toHaveAttribute("src", expect.stringContaining("capa-amordemae.png"));
  });

  it("troca capas localizadas de Amor de Mãe e Ester ao mudar o idioma", async () => {
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
    expect(enSrcs.some((src) => src.includes("capa-ester-en.png"))).toBe(true);

    await user.click(screen.getByTestId("landing-lang-es"));
    const esCatalog = (await screen.findByRole("heading", { name: /nuestros libros/i })).closest("section") as HTMLElement;
    const esSrcs = within(esCatalog).getAllByRole("img").map((img) => img.getAttribute("src") ?? "");
    expect(esSrcs.some((src) => src.includes("capa-amordemae-es.png"))).toBe(true);
    expect(esSrcs.some((src) => src.includes("capa-ester-es.png"))).toBe(true);
  });

  it("aponta os livros realistas para os temas existentes", async () => {
    renderLanding();
    await screen.findByTestId("landing-hero-cta");

    const personalize = screen.getAllByTestId("landing-personalize");
    expect(personalize).toHaveLength(9);
    expect(personalize[0]).toHaveAttribute("href", "/app?tema=mothers_day");
    expect(personalize[8]).toHaveAttribute("href", "/app?tema=birthday");
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

  it("abre o hero na capa de Natal e duplica a faixa", async () => {
    const user = userEvent.setup();
    renderLanding();

    const cover = await screen.findByTestId("landing-hero-slide-0");
    expect(cover).toHaveAttribute("src", expect.stringContaining("capa-natalmemetata.jpg"));
    expect(screen.getByTestId("landing-hero-slide-1")).toHaveAttribute("src", expect.stringContaining("capa-nanoaventuras.jpg"));

    const carousel = cover.closest(".hero-carousel") as HTMLElement;
    const carouselSrcs = [...carousel.querySelectorAll("img")].map((img) => img.getAttribute("src") ?? "");
    expect(carouselSrcs.every((src) => /\/capa-/.test(src))).toBe(true);
    const natalCovers = carouselSrcs.filter((src) => src.includes("capa-natalmemetata.jpg") && !src.includes("capa-natalmemetata-e"));
    expect(natalCovers).toHaveLength(2);
    expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("capa-natalmemetata.jpg"));

    await user.click(screen.getByRole("button", { name: /próxima página/i }));
    await waitFor(() => {
      expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("pagina-natalmemetata.jpg"));
    });
    await user.click(screen.getByRole("button", { name: /próxima página/i }));
    await waitFor(() => {
      expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("foto-natalmemetata.jpg"));
    });

    await user.click(screen.getByTestId("landing-hero-pick-1"));
    expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("capa-nanoaventuras.jpg"));

    await user.click(screen.getByTestId("landing-lang-es"));
    expect(screen.getByTestId("landing-hero-slide-0")).toHaveAttribute("src", expect.stringContaining("capa-natalmemetata-es.jpg"));
    expect(screen.getByTestId("landing-hero-slide-1")).toHaveAttribute("src", expect.stringContaining("capa-nanoaventuras-es.jpg"));
    expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("capa-nanoaventuras-es.jpg"));
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
    const cartoonLinks = screen.getAllByRole("link", { name: /^cartoon$/i });
    expect(cartoonLinks.length).toBeGreaterThan(0);
    for (const link of cartoonLinks) {
      expect(link).toHaveAttribute("href", "/cartoon");
    }
    expect(screen.getByText(/cada tema se transforma em uma narrativa ilustrada/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^a criança$/i })).toBeInTheDocument();
    expect(screen.queryByText(/dicas para a foto perfeita/i)).not.toBeInTheDocument();
  });

  it("rota /cartoon renderiza a cópia da landing com o como funciona antigo", async () => {
    render(
      <MemoryRouter initialEntries={["/cartoon"]}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(await screen.findByTestId("landing-hero-cta")).toBeInTheDocument();
    const cartoonLinks = screen.getAllByRole("link", { name: /^cartoon$/i });
    expect(cartoonLinks.length).toBeGreaterThan(0);
    for (const link of cartoonLinks) {
      expect(link).toHaveAttribute("href", "/cartoon");
    }
    expect(screen.getByRole("heading", { name: /dicas para a foto perfeita/i })).toBeInTheDocument();
    expect(screen.getByText(/nítida, bem iluminada e centralizada/i)).toBeInTheDocument();
    expect(screen.getByText(/uma foto da criança já basta para começar/i)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /^a criança$/i })).not.toBeInTheDocument();

    const cover = screen.getByTestId("landing-hero-slide-0");
    expect(cover).toHaveAttribute("src", expect.stringContaining("capa-floresta.jpg"));
    const carousel = cover.closest(".hero-carousel") as HTMLElement;
    const carouselSrcs = [...carousel.querySelectorAll("img")].map((img) => img.getAttribute("src") ?? "");
    for (const file of ["capa-floresta.jpg", "capa-dino2.jpg", "capa-circo.jpg", "capa-oceano.jpg", "capa-amazonia.jpg"]) {
      expect(carouselSrcs.some((src) => src.includes(file))).toBe(true);
    }
    expect(carouselSrcs.some((src) => /capa-(natal|martin|emilia|nano|mako|amor|antonio|mariajesus|facundo)/.test(src))).toBe(false);
    expect(screen.getByTestId("landing-hero-flip")).toHaveAttribute("src", expect.stringContaining("capa-floresta.jpg"));

    const catalog = (screen.getByRole("heading", { name: /nossos livros/i })).closest("section") as HTMLElement;
    const cards = within(catalog).getAllByTestId("landing-catalog-card");
    const drawingCovers = ["capa-floresta.jpg", "capa-dino2.jpg", "capa-circo.jpg", "capa-oceano.jpg", "capa-amazonia.jpg"];
    expect(cards).toHaveLength(drawingCovers.length);
    cards.forEach((card, i) => {
      expect(card.querySelector(".cat-book img")).toHaveAttribute("src", expect.stringContaining(drawingCovers[i]));
    });
    const catalogSrcs = within(catalog).getAllByRole("img").map((img) => img.getAttribute("src") ?? "");
    expect(catalogSrcs.some((src) => /capa-(martin|emilia|antonio|sofia|bruno|cristobal|nicolas|amor|natal|nano|maya|mako|ester|raquel|rebeca|abigail|miriam|noe)/.test(src))).toBe(false);
    expect(within(catalog).getAllByTestId("landing-personalize")[0]).toHaveAttribute("href", "/app?tema=fantasy");
    expect(within(catalog).getAllByTestId("landing-personalize")[1]).toHaveAttribute("href", "/app?tema=dinosaurs");
    expect(within(catalog).getAllByTestId("landing-personalize")[3]).toHaveAttribute("href", "/app?tema=underwater");
  });
});
