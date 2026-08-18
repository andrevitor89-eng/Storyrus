import type { Page } from "@playwright/test";

type Job = {
  id: string;
  project_id: string;
  type: string;
  status: string;
  provider: null;
  cost_credits: number;
  attempts: number;
  error: string | null;
  created_at: string;
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

export type MockApiOptions = {
  rejectPhoto?: boolean;
};

/**
 * Intercepta /v1 no navegador (antes do proxy do Vite). Sem isso o GET /v1/credits
 * fica pendente e o estúdio mostra "Créditos: …" para sempre.
 */
export async function mockApi(page: Page, opts: MockApiOptions = {}): Promise<void> {
  let credits = 10;
  let project: Project | null = null;
  const jobs: Job[] = [];
  let seq = 0;
  const nextId = () => `id-${++seq}`;

  await page.route(/\/v1\//, async (route) => {
    const req = route.request();
    const method = req.method();
    const path = new URL(req.url()).pathname.replace(/\/$/, "") || "/";

    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(body),
      });

    if (method === "GET" && path === "/v1/credits") {
      return json(200, { credits });
    }

    if (method === "POST" && path === "/v1/projects") {
      project = {
        id: nextId(),
        status: "CREATED",
        style: "realistic",
        story_text: null,
        ebook_url: null,
        video_url: null,
        created_at: new Date().toISOString(),
      };
      return json(201, project);
    }

    if (method === "GET" && project && path === `/v1/projects/${project.id}`) {
      return json(200, project);
    }

    if (method === "GET" && path.endsWith("/assets")) {
      return json(200, {
        character_url: null,
        realistic_url: null,
        extra_characters: [],
        page_images: [],
        ebook_url: null,
        video_url: null,
      });
    }

    if (method === "GET" && path.endsWith("/jobs")) {
      return json(200, jobs);
    }

    if (method === "POST" && path.endsWith("/photo")) {
      if (opts.rejectPhoto) {
        return json(422, {
          detail: {
            code: "PHOTO_STANDARD",
            message: "O rosto da criança precisa estar no padrão visual para criar o avatar.",
            reasons: ["Há mais de uma pessoa na foto. Envie só a criança."],
          },
        });
      }
      return json(201, {
        asset_id: nextId(),
        storage_key: "photo.jpg",
        upload_url: "",
        expires_in: 0,
      });
    }

    if (method === "POST" && (path.endsWith("/avatar") || path.endsWith("/realistic"))) {
      const type = path.endsWith("/avatar") ? "AVATAR" : "REALISTIC";
      credits -= 1;
      const job: Job = {
        id: nextId(),
        project_id: project?.id ?? nextId(),
        type,
        status: "DONE",
        provider: null,
        cost_credits: 1,
        attempts: 1,
        error: null,
        created_at: new Date().toISOString(),
      };
      jobs.push(job);
      if (project && type === "AVATAR") project.status = "AVATAR_READY";
      return json(202, {
        job_id: job.id,
        status: "PENDING",
        type,
        estimated_cost_credits: 1,
      });
    }

    return json(404, { detail: `not mocked: ${method} ${path}` });
  });
}
