import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Landing } from "./Landing";
import { App } from "./App";

/**
 * Roteamento do site:
 *   /         → Landing (home lúdica, bilíngue PT/EN)
 *   /app      → App (estúdio, sem login)
 *   /landing  → Landing (mesma home, mantido por compatibilidade)
 * O App e o Studio não dependem do router, para que os testes continuem
 * renderizando <App /> diretamente.
 */
export function Root() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<App />} />
        <Route path="/landing" element={<Landing />} />
        <Route path="*" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  );
}
