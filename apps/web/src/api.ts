import type {
  Job,
  JobAccepted,
  Project,
  StoryTemplate,
  Theme,
  UploadUrl,
  UsageReport,
  UserVoice,
  VoiceList,
} from "./types";

const BASE = ""; // mesmo host (proxy do Vite cobre /v1)
const TOKEN_KEY = "storyrus_token";
/** Renova o JWT se faltar menos que isto para o `exp` (STO-26). */
const REFRESH_SKEW_SEC = 60 * 60 * 2;

function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

let token: string | null = readStoredToken();
let guestPromise: Promise<void> | null = null;
let refreshPromise: Promise<boolean> | null = null;
let resumePromise: Promise<boolean> | null = null;

export function setToken(t: string | null) {
  token = t;
  try {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}
export function getToken() {
  return token;
}

/** Decodifica payload JWT (sem verificar assinatura — so para `exp` local). */
export function readJwtPayload(t: string): { exp?: number; sub?: string } | null {
  try {
    const parts = t.split(".");
    if (parts.length < 2) return null;
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(b64.padEnd(b64.length + ((4 - (b64.length % 4)) % 4), "="));
    return JSON.parse(json) as { exp?: number; sub?: string };
  } catch {
    return null;
  }
}

function tokenExpired(t: string, nowSec = Date.now() / 1000): boolean {
  const payload = readJwtPayload(t);
  if (!payload?.exp) return false;
  return payload.exp <= nowSec;
}

function tokenExpiresSoon(t: string, skewSec = REFRESH_SKEW_SEC, nowSec = Date.now() / 1000): boolean {
  const payload = readJwtPayload(t);
  if (!payload?.exp) return false;
  return payload.exp <= nowSec + skewSec;
}

async function postToken(
  path: string,
  init: RequestInit = {},
): Promise<string | null> {
  const resp = await fetch(`${BASE}${path}`, init);
  if (!resp.ok) return null;
  const data = (await resp.json()) as { access_token?: string };
  return data.access_token ?? null;
}

/** Reemite JWT enquanto o atual ainda e aceito pela API. */
export async function refreshSession(): Promise<boolean> {
  if (!token) return false;
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const next = await postToken("/v1/auth/refresh", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!next) return false;
      setToken(next);
      return true;
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

/** Recupera o mesmo user_id a partir de um JWT expirado (evita orfaos). */
export async function resumeSession(oldToken: string): Promise<boolean> {
  if (!resumePromise) {
    resumePromise = (async () => {
      const next = await postToken("/v1/auth/resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_token: oldToken }),
      });
      if (!next) return false;
      setToken(next);
      return true;
    })().finally(() => {
      resumePromise = null;
    });
  }
  return resumePromise;
}

async function mintGuest(): Promise<void> {
  const resp = await fetch(`${BASE}/v1/auth/guest`, { method: "POST" });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      detail = (await resp.json()).detail ?? detail;
    } catch {
      /* corpo vazio */
    }
    throw new Error(`${resp.status}: ${detail}`);
  }
  const data = (await resp.json()) as { access_token: string };
  setToken(data.access_token);
}

export async function ensureGuest(): Promise<void> {
  if (token) {
    if (tokenExpired(token)) {
      const old = token;
      const ok = await resumeSession(old);
      if (ok) return;
      setToken(null);
    } else {
      if (tokenExpiresSoon(token)) {
        void refreshSession();
      }
      return;
    }
  }
  if (!guestPromise) {
    guestPromise = mintGuest().finally(() => {
      guestPromise = null;
    });
  }
  await guestPromise;
}

function uuid(): string {
  return crypto.randomUUID();
}

/** Idempotency-Key estável por projeto+etapa enquanto a tentativa estiver viva. */
const stepIdempotencyKeys = new Map<string, string>();
const stepInFlight = new Map<string, Promise<unknown>>();

function stepCacheKey(projectId: string, step: string): string {
  return `${projectId}:${step}`;
}

function getOrCreateStepIdempotencyKey(projectId: string, step: string): string {
  const cacheKey = stepCacheKey(projectId, step);
  let key = stepIdempotencyKeys.get(cacheKey);
  if (!key) {
    key = uuid();
    stepIdempotencyKeys.set(cacheKey, key);
  }
  return key;
}

function releaseStepIdempotencyKey(projectId: string, step: string): void {
  stepIdempotencyKeys.delete(stepCacheKey(projectId, step));
}

/** Erros HTTP do `req` (ex.: "402: ...") vs falha de rede/ambígua. */
function isHttpErrorMessage(message: string): boolean {
  return /^\d{3}:/.test(message);
}

/** Limpa estado de idempotência (só para testes). */
export function resetStepIdempotencyState(): void {
  stepIdempotencyKeys.clear();
  stepInFlight.clear();
}

async function reqOnce<T>(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(`${BASE}${path}`, { ...init, headers });
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const skipGuest =
    path.startsWith("/v1/auth/signup") ||
    path.startsWith("/v1/auth/login") ||
    path.startsWith("/v1/auth/guest") ||
    path.startsWith("/v1/auth/resume");
  if (!skipGuest) await ensureGuest();

  let resp = await reqOnce(path, init);
  // Token morto: tenta resume do JWT antigo antes de mintar outro guest (STO-26).
  if (resp.status === 401 && token && !path.startsWith("/v1/auth/")) {
    const old = token;
    const resumed = await resumeSession(old);
    if (resumed) {
      resp = await reqOnce(path, init);
    } else {
      setToken(null);
      await ensureGuest();
      resp = await reqOnce(path, init);
    }
  }

  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      detail = (await resp.json()).detail ?? detail;
    } catch {
      /* corpo vazio */
    }
    throw new Error(`${resp.status}: ${detail}`);
  }
  return resp.status === 204 ? (undefined as T) : ((await resp.json()) as T);
}

export const api = {
  async signup(email: string, password: string) {
    const out = await req<{ access_token: string }>("/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(out.access_token);
    return out;
  },
  async login(email: string, password: string) {
    const out = await req<{ access_token: string }>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(out.access_token);
    return out;
  },
  /** Guest → conta real no mesmo user_id (mantem projetos). */
  async upgrade(email: string, password: string) {
    const out = await req<{ access_token: string }>("/v1/auth/upgrade", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(out.access_token);
    return out;
  },
  async me() {
    return req<{
      id: string;
      email: string;
      credits: number;
      created_at: string;
      is_guest: boolean;
    }>("/v1/auth/me");
  },
  async refresh() {
    return refreshSession();
  },
  async credits() {
    return req<{ credits: number }>("/v1/credits");
  },
  async createProject(
    theme?: Theme, extraTheme?: Theme, childName?: string, dedication?: string,
    childAge?: number,
  ) {
    return req<Project>("/v1/projects", {
      method: "POST",
      body: JSON.stringify({
        style: "cgi_3d", theme,
        extra_theme: extraTheme || undefined,
        child_name: childName?.trim() || undefined,
        child_age: childAge ?? undefined,
        dedication: dedication?.trim() || undefined,
      }),
    });
  },
  async getProject(id: string) {
    return req<Project>(`/v1/projects/${id}`);
  },
  // URLs (assinadas) dos resultados de cada etapa.
  async getAssets(id: string) {
    return req<{
      character_url: string | null;
      realistic_url: string | null;
      extra_characters: { name: string; url: string }[];
      page_images: string[];
      ebook_url: string | null;
      video_url: string | null;
      narrated_video_url: string | null;
    }>(`/v1/projects/${id}/assets`);
  },
  // Upload da foto via API (servidor grava no storage). Evita PUT do navegador.
  async uploadPhoto(id: string, file: File) {
    await ensureGuest();
    const fd = new FormData();
    fd.append("file", file);
    const headers = new Headers();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const resp = await fetch(`${BASE}/v1/projects/${id}/photo`, {
      method: "POST",
      body: fd,
      headers,
    });
    if (!resp.ok) {
      let detail = resp.statusText;
      try {
        detail = (await resp.json()).detail ?? detail;
      } catch {
        /* corpo vazio */
      }
      throw new Error(`${resp.status}: ${detail}`);
    }
    return resp.json();
  },
  // Usar uma história fornecida pelo usuário (digitada/colada). Sem IA.
  async setStoryText(id: string, story_text: string) {
    return req<Project>(`/v1/projects/${id}/story/text`, {
      method: "POST",
      body: JSON.stringify({ story_text }),
    });
  },
  // Catálogo de histórias prontas da plataforma.
  async storyTemplates() {
    return req<StoryTemplate[]>("/v1/projects/story-templates");
  },
  // Usar uma história pronta do catálogo, personalizada com o nome. Sem IA, sem créditos.
  async applyStoryTemplate(id: string, template_id: string) {
    return req<Project>(`/v1/projects/${id}/story/template`, {
      method: "POST",
      body: JSON.stringify({ template_id }),
    });
  },
  // Extrair o texto de um arquivo (PDF/DOCX/TXT) enviado pelo usuário.
  async extractStory(id: string, file: File) {
    await ensureGuest();
    const fd = new FormData();
    fd.append("file", file);
    const headers = new Headers();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const resp = await fetch(`${BASE}/v1/projects/${id}/story/extract`, {
      method: "POST",
      body: fd,
      headers,
    });
    if (!resp.ok) {
      let detail = resp.statusText;
      try {
        detail = (await resp.json()).detail ?? detail;
      } catch {
        /* corpo vazio */
      }
      throw new Error(`${resp.status}: ${detail}`);
    }
    return (await resp.json()) as { text: string };
  },
  async listJobs(id: string) {
    return req<Job[]>(`/v1/projects/${id}/jobs`);
  },
  async requestPhotoUpload(id: string, contentType: string, ext: string) {
    return req<UploadUrl>(`/v1/projects/${id}/photos`, {
      method: "POST",
      body: JSON.stringify({ content_type: contentType, ext }),
    });
  },
  async uploadToSignedUrl(url: string, file: File) {
    // PUT direto no storage (URL assinada). Em dev (stub) pode falhar silenciosamente.
    try {
      await fetch(url, { method: "PUT", body: file, headers: { "Content-Type": file.type } });
    } catch {
      /* storage stub local */
    }
  },
  startStep(
    id: string,
    step: "avatar" | "realistic" | "story" | "ebook" | "video" | "extra-character" | "narrated-video",
    body: Record<string, unknown> = {},
  ): Promise<JobAccepted> {
    // Clique duplo / retry em voo: mesma promise + mesma Idempotency-Key.
    const cacheKey = stepCacheKey(id, step);
    const inFlight = stepInFlight.get(cacheKey);
    if (inFlight) return inFlight as Promise<JobAccepted>;

    const idempotencyKey = getOrCreateStepIdempotencyKey(id, step);
    const promise = (async () => {
      try {
        const accepted = await req<JobAccepted>(`/v1/projects/${id}/${step}`, {
          method: "POST",
          headers: { "Idempotency-Key": idempotencyKey },
          body: JSON.stringify(body),
        });
        // Sucesso: libera a chave para um próximo start intencional (regenerar).
        releaseStepIdempotencyKey(id, step);
        return accepted;
      } catch (err) {
        const message = err instanceof Error ? err.message : "";
        // Resposta HTTP definitiva: libera. Falha de rede: mantém a chave no retry.
        if (isHttpErrorMessage(message)) {
          releaseStepIdempotencyKey(id, step);
        }
        throw err;
      } finally {
        stepInFlight.delete(cacheKey);
      }
    })();

    stepInFlight.set(cacheKey, promise);
    return promise;
  },
  async listVoices() {
    return req<VoiceList>("/v1/voices");
  },
  async uploadVoice(file: File, name: string, makeDefault = false) {
    await ensureGuest();
    const fd = new FormData();
    fd.append("file", file);
    fd.append("name", name);
    fd.append("make_default", makeDefault ? "true" : "false");
    const headers = new Headers();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const resp = await fetch(`${BASE}/v1/voices`, { method: "POST", body: fd, headers });
    if (!resp.ok) {
      let detail = resp.statusText;
      try {
        detail = (await resp.json()).detail ?? detail;
      } catch {
        /* corpo vazio */
      }
      throw new Error(`${resp.status}: ${detail}`);
    }
    return (await resp.json()) as UserVoice;
  },
  async setDefaultVoice(id: string) {
    return req<UserVoice>(`/v1/voices/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_default: true }),
    });
  },
  async deleteVoice(id: string) {
    return req<void>(`/v1/voices/${id}`, { method: "DELETE" });
  },
  async approveCharacter(id: string) {
    return req<Project>(`/v1/projects/${id}/avatar/approve`, { method: "POST" });
  },
  async approveBook(id: string) {
    return req<Project>(`/v1/projects/${id}/book/approve`, { method: "POST" });
  },
  async requestPrint(id: string) {
    return req<Project>(`/v1/projects/${id}/print-request`, { method: "POST" });
  },
  // Upload de foto de personagem extra
  async uploadExtraCharacter(id: string, file: File, name: string) {
    await ensureGuest();
    const fd = new FormData();
    fd.append("file", file);
    fd.append("name", name);
    const headers = new Headers();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const resp = await fetch(`${BASE}/v1/projects/${id}/extra-character`, {
      method: "POST",
      body: fd,
      headers,
    });
    if (!resp.ok) {
      let detail = resp.statusText;
      try {
        detail = (await resp.json()).detail ?? detail;
      } catch {
        /* corpo vazio */
      }
      throw new Error(`${resp.status}: ${detail}`);
    }
    return resp.json();
  },
  async usage(password: string, from?: string, to?: string) {
    const q = new URLSearchParams();
    if (from) q.set("from", from);
    if (to) q.set("to", to);
    const suffix = q.toString() ? `?${q}` : "";
    const headers = new Headers();
    headers.set("X-Usage-Password", password);
    const resp = await fetch(`${BASE}/v1/usage${suffix}`, { headers });
    if (!resp.ok) {
      let detail = resp.statusText;
      try {
        detail = (await resp.json()).detail ?? detail;
      } catch {
        /* corpo vazio */
      }
      const err = new Error(`${resp.status}: ${detail}`) as Error & { status?: number };
      err.status = resp.status;
      throw err;
    }
    return (await resp.json()) as UsageReport;
  },
};
