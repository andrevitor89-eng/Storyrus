import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Landing } from "./Landing";
import { App } from "./App";
import { Legal } from "./Legal";
import { NotFound } from "./NotFound";
import { Usage } from "./Usage";

/**
 * Roteamento do site:
 *   /              → Landing
 *   /app           → Estúdio
 *   /gastos        → Painel privado de custos USD
 *   /landing       → Landing (compatibilidade)
 *   /privacidade   → Política de privacidade
 *   /termos        → Termos de uso
 *   *              → 404
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/app" element={<App />} />
      <Route path="/gastos" element={<Usage />} />
      <Route path="/landing" element={<Landing />} />
      <Route path="/privacidade" element={<Legal kind="privacy" />} />
      <Route path="/privacy" element={<Legal kind="privacy" />} />
      <Route path="/termos" element={<Legal kind="terms" />} />
      <Route path="/terms" element={<Legal kind="terms" />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export function Root() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
