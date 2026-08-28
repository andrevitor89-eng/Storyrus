import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Landing } from "./Landing";
import { App } from "./App";
import { Legal } from "./Legal";
import { NotFound } from "./NotFound";

/**
 * Roteamento do site:
 *   /              → Landing
 *   /app           → Estúdio
 *   /landing       → Landing (compatibilidade)
 *   /privacidade   → Política de privacidade
 *   /termos        → Termos de uso
 *   *              → 404
 */
export function Root() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<App />} />
        <Route path="/landing" element={<Landing />} />
        <Route path="/privacidade" element={<Legal kind="privacy" />} />
        <Route path="/privacy" element={<Legal kind="privacy" />} />
        <Route path="/termos" element={<Legal kind="terms" />} />
        <Route path="/terms" element={<Legal kind="terms" />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
