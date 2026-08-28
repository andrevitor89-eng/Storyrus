import { Studio } from "./Studio";

/**
 * Sem tela de login: o estúdio pede um JWT de convidado isolado
 * (POST /v1/auth/guest) na primeira chamada à API.
 */
export function App() {
  return <Studio />;
}
