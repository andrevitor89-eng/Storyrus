import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { catalogCategory, catalogEntry } from "./Landing";
import { AppRoutes } from "./Root";
import { parsePtCatalog } from "./catalogSeo";
import {
  CATALOG_CATEGORIES,
  NOT_FOUND_PAGE,
  applyPageMeta,
  htmlFileForPath,
  publicHtmlPages,
  renderSitemap,
  staticPageMeta,
} from "./pageMeta";

const INDEX = `<!doctype html>
<html lang="pt-BR">
  <head>
    <title>Story R Us — histórias ilustradas com a foto do seu filho</title>
    <meta name="description" content="Envie uma foto." />
    <link rel="canonical" href="https://storyrus.ai/" />
    <meta property="og:url" content="https://storyrus.ai/" />
    <meta property="og:title" content="Story R Us — histórias ilustradas com a foto do seu filho" />
    <meta property="og:description" content="Uma foto vira personagem." />
    <meta name="twitter:title" content="Story R Us" />
    <meta name="twitter:description" content="Transforme uma foto." />
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>`;

describe("catálogo no sitemap", () => {
  const source = readFileSync(resolve(process.cwd(), "src/Landing.tsx"), "utf8");
  const books = parsePtCatalog(source);

  it("acompanha as fichas públicas de livro", () => {
    expect(catalogEntry("pt", 13)).toBeNull();
    expect(books.some((book) => book.index === 13)).toBe(false);
    for (const book of books) {
      expect(catalogEntry("pt", book.index)?.t).toBe(book.title);
    }
    expect(books.some((book) => book.title === "Davi, o Menino Pastor")).toBe(true);
  });

  it("inclui categorias que o app conhece", () => {
    for (const category of CATALOG_CATEGORIES) {
      expect(catalogCategory("pt", category.id)?.name).toBeTruthy();
    }
  });

  it("gera sitemap com páginas que vendem e sem painel admin", () => {
    const pages = publicHtmlPages(books);
    const xml = renderSitemap(pages);
    expect(xml).toContain("https://storyrus.ai/cartoon");
    expect(xml).toContain("https://storyrus.ai/catalogo");
    expect(xml).toContain("https://storyrus.ai/catalogo/aventuras");
    expect(xml).toContain("https://storyrus.ai/livro/20");
    expect(xml).toContain("https://storyrus.ai/privacidade");
    expect(xml).toContain("https://storyrus.ai/exemplos");
    expect(xml).not.toContain("https://storyrus.ai/livro/13");
    expect(xml).not.toContain("/gastos");
    expect(xml).not.toContain("/pedidos");
    expect(xml).not.toContain("/usuarios");
    expect(htmlFileForPath("/catalogo/aventuras")).toBe("catalogo/aventuras.html");
    expect(htmlFileForPath("/")).toBe("index.html");
  });
});

describe("HTML por rota", () => {
  it("troca title, open graph e coloca texto no #root", () => {
    const page = staticPageMeta("/cartoon");
    expect(page).not.toBeNull();
    const html = applyPageMeta(INDEX, page!);
    expect(html).toContain(`<title>${page!.title}</title>`);
    expect(html).toContain(`property="og:title" content="${page!.title}"`);
    expect(html).toContain(`property="og:url" content="https://storyrus.ai/cartoon"`);
    expect(html).toContain(`<h1>${page!.title}</h1>`);
    expect(html).not.toContain("histórias ilustradas com a foto do seu filho");
  });

  it("marca a página 404 com noindex", () => {
    const html = applyPageMeta(INDEX, NOT_FOUND_PAGE);
    expect(html).toContain('name="robots" content="noindex, nofollow"');
    expect(html).toContain("Página não encontrada");
  });
});

describe("rotas públicas", () => {
  it("mostra exemplos em vez de página inexistente", async () => {
    render(
      <MemoryRouter initialEntries={["/exemplos"]}>
        <AppRoutes />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("exemplos-title")).toBeInTheDocument();
    expect(document.title).toMatch(/exemplos da plataforma/i);
  });

  it("coloca noindex na tela de não encontrado", async () => {
    render(
      <MemoryRouter initialEntries={["/nao-existe"]}>
        <AppRoutes />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("not-found-title")).toBeInTheDocument();
    expect(document.querySelector('meta[name="robots"]')).toHaveAttribute(
      "content",
      "noindex, nofollow",
    );
  });
});
