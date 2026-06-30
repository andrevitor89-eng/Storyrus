import { expect, test, type Page } from "@playwright/test";

// Estado em memória que imita o backend; injetado via page.route (sem rede real).
type Job = { id: string; project_id: string; type: string; status: string; cost_credits: number; attempts: number; error: string | null; polls: number };

function makeState() {
  return { credits: 0, project: null as any, jobs: [] as Job[], seq: 0 };
}

async function mockApi(page: Page, state: ReturnType<typeof makeState>) {
  const json = (route: any, body: unknown, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  const id = () => `id-${++state.seq}`;

  await page.route("**/v1/auth/signup", (r) => {
    state.credits = 10;
    return json(r, { access_token: "tkn" }, 201);
  });
  await page.route("**/v1/credits", (r) => json(r, { credits: state.credits }));

  await page.route("**/v1/projects", (r) => {
    if (r.request().method() !== "POST") return r.continue();
    state.project = {
      id: id(), status: "CREATED", style: "cartoon",
      story_text: null, ebook_url: null, video_url: null, created_at: "now",
    };
    state.jobs = [];
    return json(r, state.project, 201);
  });

  // jobs (advance) — registrar ANTES da rota de projeto por id
  await page.route(/\/v1\/projects\/[^/]+\/jobs$/, (r) => {
    for (const j of state.jobs) {
      if (j.status === "DONE") continue;
      j.polls += 1;
      if (j.polls === 1) j.status = "RUNNING";
      else if (j.polls >= 2) {
        j.status = "DONE";
        if (j.type === "STORY") {
          state.project.story_text = "Pagina 1: ola.\nPagina 2: fim.";
          state.project.status = "STORY_READY";
        }
      }
    }
    return json(r, state.jobs);
  });

  await page.route(/\/v1\/projects\/[^/]+\/photos$/, (r) =>
    json(r, { asset_id: id(), storage_key: "k", upload_url: "https://storage.local/x?op=put", expires_in: 600 }, 201),
  );
  await page.route("https://storage.local/**", (r) => r.fulfill({ status: 200, body: "" }));

  await page.route(/\/v1\/projects\/[^/]+\/(avatar|story|ebook|video)$/, (r) => {
    const type = r.request().url().split("/").pop()!.toUpperCase();
    const cost = type === "VIDEO" ? 5 : 1;
    if (state.credits < cost) return json(r, { detail: "Creditos insuficientes" }, 402);
    state.credits -= cost;
    const job: Job = { id: id(), project_id: state.project.id, type, status: "PENDING", cost_credits: cost, attempts: 1, error: null, polls: 0 };
    state.jobs.push(job);
    return json(r, { job_id: job.id, status: "PENDING", type, estimated_cost_credits: cost }, 202);
  });

  // project por id (rota mais genérica por último)
  await page.route(/\/v1\/projects\/[^/]+$/, (r) => {
    if (r.request().method() === "POST") return r.continue();
    return json(r, state.project);
  });
}

test("signup → projeto → upload → história com progresso ao vivo", async ({ page }) => {
  const state = makeState();
  await mockApi(page, state);
  await page.goto("/");

  // signup
  await page.getByLabel(/e-mail/i).fill("a@b.com");
  await page.getByLabel(/senha/i).fill("password123");
  await page.getByRole("button", { name: /criar conta/i }).click();

  await expect(page.getByText(/créditos: 10/i)).toBeVisible();

  // cria projeto
  await page.getByRole("button", { name: /desenho/i }).click();
  await page.getByRole("button", { name: /criar projeto/i }).click();
  await expect(page.getByRole("heading", { name: /^projeto$/i })).toBeVisible();

  // upload de foto
  await page.setInputFiles('input[type="file"]', {
    name: "foto.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from("x"),
  });
  await page.getByRole("button", { name: /enviar foto/i }).click();
  await expect(page.getByText(/foto enviada/i)).toBeVisible();

  // dispara história e acompanha progresso até DONE
  await page.getByRole("button", { name: /escrever história/i }).click();
  await expect(page.getByText("STORY")).toBeVisible();
  await expect(page.getByText("DONE")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText(/história gerada/i)).toBeVisible();
  await expect(page.getByText(/créditos: 9/i)).toBeVisible();
});

test("bloqueia 'gerar personagem' sem foto e faz logout", async ({ page }) => {
  const state = makeState();
  await mockApi(page, state);
  await page.goto("/");

  await page.getByLabel(/e-mail/i).fill("a@b.com");
  await page.getByLabel(/senha/i).fill("password123");
  await page.getByRole("button", { name: /criar conta/i }).click();
  await page.getByRole("button", { name: /criar projeto/i }).click();

  await expect(page.getByRole("button", { name: /gerar personagem/i })).toBeDisabled();

  await page.getByRole("button", { name: /sair/i }).click();
  await expect(page.getByRole("button", { name: /criar conta/i })).toBeVisible();
});
