import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Landing } from "./Landing";
import { App } from "./App";
import { Usage } from "./Usage";

/**
 * Roteamento do site:
 *   /         → Landing (home lúdica, bilíngue PT/EN)
 *   /app      → App (estúdio, sem login)
 *   /gastos   → Painel privado de custos USD
 *   /landing  → Landing (mesma home, mantido por compatibilidade)
 * O App e o Studio não dependem do router, para que os testes continuem
 * renderizando <App /> diretamente.
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/app" element={<App />} />
      <Route path="/gastos" element={<Usage />} />
      <Route path="/landing" element={<Landing />} />
      <Route path="*" element={<Landing />} />
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
