import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";
import type { Job, Project, UploadUrl } from "./types";

const TOKEN_KEY = "storyrus_token";

/**
 * API base: production BFF at https://storyrus.ai (same-origin /v1 proxy).
 * Local override (highest → lowest):
 *   1. EXPO_PUBLIC_API_BASE env (e.g. EXPO_PUBLIC_API_BASE=http://10.0.2.2:8000 npx expo start)
 *   2. expo.extra.apiBase in app.json
 */
const BASE: string =
  (typeof process !== "undefined" && process.env?.EXPO_PUBLIC_API_BASE) ||
  (Constants.expoConfig?.extra as { apiBase?: string } | undefined)?.apiBase ||
  "https://storyrus.ai";

let token: string | null = null;
let guestPromise: Promise<void> | null = null;
let hydratePromise: Promise<void> | null = null;

export function getToken(): string | null {
  return token;
}

export function setToken(t: string | null) {
  token = t;
  void (t
    ? AsyncStorage.setItem(TOKEN_KEY, t)
    : AsyncStorage.removeItem(TOKEN_KEY)
  ).catch(() => {
    /* ignore persistence failures */
  });
}

/** Load persisted JWT into memory. Call once at app boot before API use. */
export function hydrateToken(): Promise<void> {
  if (!hydratePromise) {
    hydratePromise = (async () => {
      try {
        const stored = await AsyncStorage.getItem(TOKEN_KEY);
        if (stored) token = stored;
      } catch {
        /* ignore */
      }
    })();
  }
  return hydratePromise;
}

/** Guest-first: mint an isolated JWT via POST /v1/auth/guest when none is stored. */
export async function ensureGuest(): Promise<void> {
  await hydrateToken();
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

/** Clear session and mint a fresh guest (studio "Sair"). */
export async function resetToGuest(): Promise<void> {
  setToken(null);
  await ensureGuest();
}

function uuid(): string {
  // RFC4122 v4 simples (suficiente para Idempotency-Key).
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
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

function isHttpErrorMessage(message: string): boolean {
  return /^\d{3}:/.test(message);
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const skipGuest =
    path.startsWith("/v1/auth/signup") ||
    path.startsWith("/v1/auth/login") ||
    path.startsWith("/v1/auth/guest");
  if (!skipGuest) await ensureGuest();

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
  guest: () =>
    req<{ access_token: string }>("/v1/auth/guest", { method: "POST" }),
  signup: async (email: string, password: string) => {
    const out = await req<{ access_token: string }>("/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(out.access_token);
    return out;
  },
  login: async (email: string, password: string) => {
    const out = await req<{ access_token: string }>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(out.access_token);
    return out;
  },
  credits: () => req<{ credits: number }>("/v1/credits"),
  createProject: () =>
    req<Project>("/v1/projects", { method: "POST", body: JSON.stringify({ style: "cgi_3d" }) }),
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
  startStep(id: string, step: "avatar" | "story" | "ebook" | "video", body: object = {}) {
    // Clique duplo / retry em voo: mesma promise + mesma Idempotency-Key.
    const cacheKey = stepCacheKey(id, step);
    const inFlight = stepInFlight.get(cacheKey);
    if (inFlight) {
      return inFlight as Promise<{ job_id: string; estimated_cost_credits: number }>;
    }

    const idempotencyKey = getOrCreateStepIdempotencyKey(id, step);
    const promise = (async () => {
      try {
        const accepted = await req<{ job_id: string; estimated_cost_credits: number }>(
          `/v1/projects/${id}/${step}`,
          {
            method: "POST",
            headers: { "Idempotency-Key": idempotencyKey },
            body: JSON.stringify(body),
          },
        );
        releaseStepIdempotencyKey(id, step);
        return accepted;
      } catch (err) {
        const message = err instanceof Error ? err.message : "";
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
};
