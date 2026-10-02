import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Legal } from "./Legal";
import { NotFound } from "./NotFound";

const Landing = lazy(() =>
  import("./Landing").then((m) => ({ default: m.Landing })),
);
const CatalogPage = lazy(() =>
  import("./CatalogPages").then((m) => ({ default: m.CatalogPage })),
);
const CategoryCatalogPage = lazy(() =>
  import("./CatalogPages").then((m) => ({ default: m.CategoryCatalogPage })),
);
const BookPage = lazy(() =>
  import("./CatalogPages").then((m) => ({ default: m.BookPage })),
);
const App = lazy(() => import("./App").then((m) => ({ default: m.App })));
const Usage = lazy(() =>
  import("./Usage").then((m) => ({ default: m.Usage })),
);
const Pedidos = lazy(() =>
  import("./Pedidos").then((m) => ({ default: m.Pedidos })),
);

/**
 * Roteamento do site:
 *   /              → Landing
 *   /cartoon       → Landing (mesma página, fotos em desenho)
 *   /catalogo      → Catálogo completo
 *   /catalogo/:categoria → Catálogo de uma categoria
 *   /livro/:indice → Página do livro
 *   /app           → Estúdio
 *   /gastos        → Painel privado de custos USD
 *   /landing       → Landing (compatibilidade)
 *   /privacidade   → Política de privacidade
 *   /termos        → Termos de uso
 *   *              → 404
 *
 * Landing / Studio (via App) / Usage are lazy-loaded into separate chunks.
 * Suspense fallback is null so the landing visual stays unchanged.
 */
export function AppRoutes() {
  return (
    <Suspense fallback={null}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/cartoon" element={<Landing variant="cartoon" />} />
        <Route path="/catalogo" element={<CatalogPage />} />
        <Route path="/catalogo/:categoria" element={<CategoryCatalogPage />} />
        <Route path="/livro/:indice" element={<BookPage />} />
        <Route path="/app" element={<App />} />
        <Route path="/gastos" element={<Usage />} />
        <Route path="/pedidos" element={<Pedidos />} />
        <Route path="/landing" element={<Landing />} />
        <Route path="/privacidade" element={<Legal kind="privacy" />} />
        <Route path="/privacy" element={<Legal kind="privacy" />} />
        <Route path="/termos" element={<Legal kind="terms" />} />
        <Route path="/terms" element={<Legal kind="terms" />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

export function Root() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
