/** Sessão compartilhada dos painéis do dono (/gastos, /pedidos, /usuarios). */

import { getToken } from "./api";

export const OWNER_PASSWORD_KEY = "storyrus.usage.password";
/** Marca que o painel abriu com o JWT do estúdio (sem senha do dashboard). */
export const OWNER_SESSION_KEY = "storyrus.usage.session";
export const OWNER_SESSION_TOKEN = "__session__";

export function readOwnerSecret(): string {
  try {
    const stored = sessionStorage.getItem(OWNER_PASSWORD_KEY);
    if (stored) return stored;
    if (sessionStorage.getItem(OWNER_SESSION_KEY) === "1") return OWNER_SESSION_TOKEN;
  } catch {
    /* ignore */
  }
  return "";
}

export function persistOwnerSecret(secret: string | null | undefined): void {
  try {
    const cleaned = (secret ?? "").trim();
    if (!cleaned || cleaned === OWNER_SESSION_TOKEN) {
      sessionStorage.removeItem(OWNER_PASSWORD_KEY);
      sessionStorage.setItem(OWNER_SESSION_KEY, "1");
      return;
    }
    sessionStorage.setItem(OWNER_PASSWORD_KEY, cleaned);
    sessionStorage.removeItem(OWNER_SESSION_KEY);
  } catch {
    /* ignore */
  }
}

export function clearOwnerSecret(): void {
  try {
    sessionStorage.removeItem(OWNER_PASSWORD_KEY);
    sessionStorage.removeItem(OWNER_SESSION_KEY);
  } catch {
    /* ignore */
  }
}

/** Valor enviado à API: senha real ou undefined (só Bearer). */
export function apiOwnerPassword(secret: string | null | undefined): string | undefined {
  const cleaned = (secret ?? "").trim();
  if (!cleaned || cleaned === OWNER_SESSION_TOKEN) return undefined;
  return cleaned;
}

export function canTryOwnerSession(): boolean {
  return Boolean(getToken());
}

export function ownerGateError(status: number | undefined, fallback: string): string {
  if (status === 401) return "Senha inválida. Use a senha do painel (Render), não a da conta.";
  if (status === 429) return "Muitas tentativas. Aguarde alguns minutos ou entre com a conta do dono.";
  if (status === 503) return "Painel ainda não configurado no servidor.";
  return fallback;
}
