import { Studio } from "./Studio";

/**
 * Sem autenticação: o app abre direto no estúdio.
 * O acesso ao backend é feito como usuário convidado (ver backend/app/deps.py).
 */
export function App() {
  return <Studio />;
}
