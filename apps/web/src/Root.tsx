import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Landing } from "./Landing";
import { App } from "./App";
import { Login, Register } from "./Auth";
import { Privacy, Terms } from "./Legal";
import { NotFound } from "./NotFound";
import { LangProvider } from "./i18n";

/**
 * Roteamento do site:
 *   /              → Landing
 *   /app           → Estúdio
 *   /login|/register
 *   /privacidade|/termos (e aliases EN)
 *   *              → 404 (não reaproveita a home)
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/app" element={<App />} />
      <Route path="/landing" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/privacidade" element={<Privacy />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/termos" element={<Terms />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export function Root() {
  return (
    <BrowserRouter>
      <LangProvider>
        <AppRoutes />
      </LangProvider>
    </BrowserRouter>
  );
}
