import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

// --------------------------------------------------------------------------- //
// Estado em memória que imita o backend (suficiente para os testes de fluxo).
// --------------------------------------------------------------------------- //
type Job = {
  id: string;
  project_id: string;
  type: string;
  status: string;
  provider: string | null;
  cost_credits: number;
  attempts: number;
  error: string | null;
  created_at: string;
  _polls: number;
};
type Project = {
  id: string;
  status: string;
  style: string | null;
  story_text: string | null;
  ebook_url: string | null;
  video_url: string | null;
  created_at: string;
};

const COST: Record<string, number> = { AVATAR: 1, REALISTIC: 1, STORY: 1, EBOOK: 1, VIDEO: 5 };

export const state = {
  credits: 0,
  projects: new Map<string, Project>(),
  jobs: new Map<string, Job[]>(),
  reset() {
    this.credits = 0;
    this.projects.clear();
    this.jobs.clear();
  },
};

let seq = 0;
const id = () => `id-${++seq}`;

function advance(job: Job, project: Project) {
  job._polls += 1;
  if (job._polls === 1) job.status = "RUNNING";
  else if (job._polls >= 2) {
    job.status = "DONE";
    if (job.type === "STORY") {
      project.story_text = "Pagina 1: ola.\nPagina 2: fim.";
      project.status = "STORY_READY";
    }
    if (job.type === "AVATAR") project.status = "AVATAR_READY";
    if (job.type === "EBOOK") {
      project.ebook_url = `projects/${project.id}/ebook/x.pdf`;
      project.status = "EBOOK_READY";
    }
    if (job.type === "VIDEO") {
      project.video_url = `projects/${project.id}/video/x.mp4`;
      project.status = "VIDEO_READY";
    }
  }
}

export const handlers = [
  http.post("*/v1/auth/signup", async () => {
    state.credits = 10;
    return HttpResponse.json({ access_token: "test-token" }, { status: 201 });
  }),
  http.post("*/v1/auth/login", async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };
    if (body.password === "wrongpass") {
      return HttpResponse.json({ detail: "Credenciais invalidas" }, { status: 401 });
    }
    state.credits = 10;
    return HttpResponse.json({ access_token: "test-token" });
  }),
  http.get("*/v1/credits", () => HttpResponse.json({ credits: state.credits })),

  http.post("*/v1/projects", async ({ request }) => {
    const body = (await request.json()) as { style: string };
    const p: Project = {
      id: id(),
      status: "CREATED",
      style: body.style,
      story_text: null,
      ebook_url: null,
      video_url: null,
      created_at: new Date().toISOString(),
    };
    state.projects.set(p.id, p);
    state.jobs.set(p.id, []);
    return HttpResponse.json(p, { status: 201 });
  }),
  http.get("*/v1/projects/:pid", ({ params }) => {
    const p = state.projects.get(params.pid as string);
    return p ? HttpResponse.json(p) : new HttpResponse(null, { status: 404 });
  }),
  http.get("*/v1/projects/:pid/assets", () =>
    HttpResponse.json({
      character_url: null,
      realistic_url: null,
      page_images: [],
      ebook_url: null,
      video_url: null,
    }),
  ),
  http.get("*/v1/projects/:pid/jobs", ({ params }) => {
    const pid = params.pid as string;
    const project = state.projects.get(pid);
    const jobs = state.jobs.get(pid) ?? [];
    if (project) jobs.forEach((j) => j.status !== "DONE" && advance(j, project));
    return HttpResponse.json(jobs.map(({ _polls, ...j }) => ({ ...j, _polls })));
  }),
  http.post("*/v1/projects/:pid/photos", async ({ params }) => {
    const pid = params.pid as string;
    return HttpResponse.json(
      {
        asset_id: id(),
        storage_key: `projects/${pid}/photo/x.jpg`,
        upload_url: "https://storage.local/bucket/x.jpg?op=put",
        expires_in: 600,
      },
      { status: 201 },
    );
  }),
  http.put("https://storage.local/*", () => new HttpResponse(null, { status: 200 })),

  // Upload da foto via API (servidor grava no storage).
  http.post("*/v1/projects/:pid/photo", ({ params }) => {
    const pid = params.pid as string;
    return HttpResponse.json(
      { asset_id: id(), storage_key: `projects/${pid}/photo/x.jpg`, upload_url: "", expires_in: 0 },
      { status: 201 },
    );
  }),

  ...["avatar", "realistic", "story", "ebook", "video"].map((step) =>
    http.post(`*/v1/projects/:pid/${step}`, ({ params }) => {
      const pid = params.pid as string;
      const type = step.toUpperCase();
      const cost = COST[type];
      if (state.credits < cost) {
        return HttpResponse.json({ detail: "Creditos insuficientes" }, { status: 402 });
      }
      state.credits -= cost;
      const job: Job = {
        id: id(),
        project_id: pid,
        type,
        status: "PENDING",
        provider: null,
        cost_credits: cost,
        attempts: 1,
        error: null,
        created_at: new Date().toISOString(),
        _polls: 0,
      };
      state.jobs.get(pid)?.push(job);
      return HttpResponse.json(
        { job_id: job.id, status: "PENDING", type, estimated_cost_credits: cost },
        { status: 202 },
      );
    }),
  ),
];

export const server = setupServer(...handlers);
