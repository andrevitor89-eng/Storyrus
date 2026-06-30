import Constants from "expo-constants";
import type { Job, Project, Style, UploadUrl } from "./types";

// Base da API: use o IP da máquina ao testar em device físico (ex.: http://192.168.0.10:8000).
const BASE: string =
  (Constants.expoConfig?.extra as { apiBase?: string } | undefined)?.apiBase ??
  "http://localhost:8000";

let token: string | null = null;
export function setToken(t: string | null) {
  token = t;
}

function uuid(): string {
  // RFC4122 v4 simples (suficiente para Idempotency-Key).
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
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
  signup: (email: string, password: string) =>
    req<{ access_token: string }>("/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    req<{ access_token: string }>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  credits: () => req<{ credits: number }>("/v1/credits"),
  createProject: (style: Style) =>
    req<Project>("/v1/projects", { method: "POST", body: JSON.stringify({ style }) }),
  getProject: (id: string) => req<Project>(`/v1/projects/${id}`),
  listJobs: (id: string) => req<Job[]>(`/v1/projects/${id}/jobs`),
  requestPhotoUpload: (id: string, contentType: string, ext: string) =>
    req<UploadUrl>(`/v1/projects/${id}/photos`, {
      method: "POST",
      body: JSON.stringify({ content_type: contentType, ext }),
    }),
  async uploadToSignedUrl(url: string, uri: string, contentType: string) {
    try {
      const blob = await (await fetch(uri)).blob();
      await fetch(url, { method: "PUT", body: blob, headers: { "Content-Type": contentType } });
    } catch {
      /* storage stub em dev */
    }
  },
  startStep: (id: string, step: "avatar" | "story" | "ebook" | "video", body: object = {}) =>
    req<{ job_id: string; estimated_cost_credits: number }>(`/v1/projects/${id}/${step}`, {
      method: "POST",
      headers: { "Idempotency-Key": uuid() },
      body: JSON.stringify(body),
    }),
};
