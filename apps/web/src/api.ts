import type { Job, JobAccepted, Project, Style, Theme, UploadUrl } from "./types";

const BASE = ""; // mesmo host (proxy do Vite cobre /v1)

let token: string | null = null;
export function setToken(t: string | null) {
  token = t;
}
export function getToken() {
  return token;
}

function uuid(): string {
  return crypto.randomUUID();
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
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
    return req<{ access_token: string }>("/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
  async login(email: string, password: string) {
    return req<{ access_token: string }>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
  async credits() {
    return req<{ credits: number }>("/v1/credits");
  },
  async createProject(
    style: Style, theme?: Theme, childName?: string, dedication?: string, childAge?: number,
  ) {
    return req<Project>("/v1/projects", {
      method: "POST",
      body: JSON.stringify({
        style, theme,
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
    }>(`/v1/projects/${id}/assets`);
  },
  // Upload da foto via API (servidor grava no storage). Evita PUT do navegador.
  async uploadPhoto(id: string, file: File) {
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
  // Extrair o texto de um arquivo (PDF/DOCX/TXT) enviado pelo usuário.
  async extractStory(id: string, file: File) {
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
    step: "avatar" | "realistic" | "story" | "ebook" | "video" | "extra-character",
    body: Record<string, unknown> = {},
  ) {
    return req<JobAccepted>(`/v1/projects/${id}/${step}`, {
      method: "POST",
      headers: { "Idempotency-Key": uuid() },
      body: JSON.stringify(body),
    });
  },
  // Upload de foto de personagem extra
  async uploadExtraCharacter(id: string, file: File, name: string) {
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
};
