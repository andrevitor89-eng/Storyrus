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

function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

let token: string | null = readStoredToken();
let guestPromise: Promise<void> | null = null;

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

export async function ensureGuest(): Promise<void> {
  if (token) return;
  if (!guestPromise) {
    guestPromise = (async () => {
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
    })().finally(() => {
      guestPromise = null;
    });
  }
  await guestPromise;
}

function uuid(): string {
  return crypto.randomUUID();
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const skipGuest =
    path.startsWith("/v1/auth/signup") ||
    path.startsWith("/v1/auth/login") ||
    path.startsWith("/v1/auth/guest");
  if (!skipGuest) await ensureGuest();
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const resp = await fetch(`${BASE}${path}`, { ...init, headers });
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
  async startStep(
    id: string,
    step: "avatar" | "realistic" | "story" | "ebook" | "video" | "extra-character" | "narrated-video",
    body: Record<string, unknown> = {},
  ) {
    return req<JobAccepted>(`/v1/projects/${id}/${step}`, {
      method: "POST",
      headers: { "Idempotency-Key": uuid() },
      body: JSON.stringify(body),
    });
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
