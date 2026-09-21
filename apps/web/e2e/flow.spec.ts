import { expect, test, type Page } from "@playwright/test";

// Estado em memória que imita o backend; injetado via page.route (sem rede real).
type Job = {
  id: string;
  project_id: string;
  type: string;
  status: string;
  cost_credits: number;
  attempts: number;
  error: string | null;
  polls: number;
};

function makeState() {
  return { credits: 10, project: null as any, jobs: [] as Job[], seq: 0 };
}

async function mockApi(page: Page, state: ReturnType<typeof makeState>) {
  const json = (route: any, body: unknown, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  const id = () => `id-${++state.seq}`;

  await page.route("**/v1/auth/guest", (r) => json(r, { access_token: "e2e-token" }, 201));
  await page.route("**/v1/auth/refresh", (r) => json(r, { access_token: "e2e-token-refreshed" }));
  await page.route("**/v1/auth/resume", (r) => json(r, { access_token: "e2e-token-resumed" }));
  await page.route("**/v1/auth/me", (r) =>
    json(r, {
      id: "e2e-user",
      email: "guest-e2e@storyrus.app",
      credits: state.credits,
      created_at: "now",
      is_guest: true,
    }),
  );
  await page.route("**/v1/credits", (r) => json(r, { credits: state.credits }));
  await page.route("**/v1/voices", (r) => json(r, { items: [], custom_voice_available: false }));

  await page.route("**/v1/projects", (r) => {
    if (r.request().method() !== "POST") return r.continue();
    state.project = {
      id: id(),
      status: "CREATED",
      style: "cgi_3d",
      story_text: null,
      ebook_url: null,
      video_url: null,
      character_approved_at: null,
      created_at: "now",
    };
    state.jobs = [];
    return json(r, state.project, 201);
  });

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
        if (j.type === "AVATAR") {
          state.project.status = "AVATAR_READY";
        }
      }
    }
    return json(r, state.jobs);
  });

  await page.route(/\/v1\/projects\/[^/]+\/photo$/, (r) =>
    json(r, { asset_id: id(), storage_key: "k", upload_url: "", expires_in: 0 }, 201),
  );

  await page.route(/\/v1\/projects\/[^/]+\/assets$/, (r) => {
    const avatarDone = state.jobs.some((j) => j.type === "AVATAR" && j.status === "DONE");
    return json(r, {
      character_url: avatarDone ? "https://cdn.test/character.png" : null,
      realistic_url: null,
      extra_characters: [],
      page_images: [],
      ebook_url: state.project?.ebook_url ?? null,
      video_url: null,
      narrated_video_url: null,
    });
  });

  await page.route(/\/v1\/projects\/[^/]+\/(avatar|story|ebook|video|narrated-video)$/, (r) => {
    const last = r.request().url().split("/").pop()!.split("?")[0];
    const type = last === "narrated-video" ? "NARRATED_VIDEO" : last.toUpperCase();
    const cost = type === "VIDEO" ? 5 : type === "NARRATED_VIDEO" ? 8 : 1;
    if (state.credits < cost) return json(r, { detail: "Creditos insuficientes" }, 402);
    state.credits -= cost;
    const job: Job = {
      id: id(),
      project_id: state.project.id,
      type,
      status: "PENDING",
      cost_credits: cost,
      attempts: 1,
      error: null,
      polls: 0,
    };
    state.jobs.push(job);
    return json(r, { job_id: job.id, status: "PENDING", type, estimated_cost_credits: cost }, 202);
  });

  await page.route(/\/v1\/projects\/[^/]+$/, (r) => {
    if (r.request().method() === "POST") return r.continue();
    return json(r, state.project);
  });
}

test("landing leva ao estúdio", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  // Stable selector: not tied to hero CTA copy (pt/en/es).
  const heroCta = page.getByTestId("landing-hero-cta");
  await expect(heroCta).toBeVisible();
  await heroCta.click();
  await expect(page).toHaveURL(/\/app/);
  await expect(page.getByTestId("studio-create-project")).toBeVisible();
});

test("estúdio → projeto → foto gera personagem → história", async ({ page }) => {
  const state = makeState();
  await mockApi(page, state);
  await page.goto("/app");

  await expect(page.getByTestId("studio-credits")).toContainText(/créditos:\s*10/i);

  await page.getByLabel("Nome da criança").fill("Lila");
  await page.getByLabel("Idade").fill("5");
  await page.getByLabel("Título do livro").fill("Lila e as estrelas");
  await page.getByLabel("Insira o tema desejado").fill("Aventura no espaço");
  await page.getByTestId("studio-photo-input").setInputFiles({
    name: "foto.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from("x"),
  });
  await page.getByTestId("studio-media-consent").check();
  await page.getByTestId("studio-create-project").click();
  await expect(page.getByTestId("studio-project")).toBeVisible();
  await expect(page.getByTestId("studio-project").getByRole("heading", { level: 2 })).toBeVisible();
  // Job rows use stable test ids (avoids colliding with AVATAR_READY / STORY_READY status text).
  await expect(page.getByTestId("studio-job-type-AVATAR")).toBeVisible();
  await expect(page.getByTestId("studio-job-AVATAR")).toHaveAttribute("data-job-status", "DONE", {
    timeout: 15_000,
  });

  await page.getByTestId("studio-generate-story").click();
  await expect(page.getByTestId("studio-job-type-STORY")).toBeVisible();
  await expect(page.getByTestId("studio-story-text")).toContainText(/pagina 1: ola/i, {
    timeout: 15_000,
  });
});

test("ebook fica desabilitado até aprovar o personagem", async ({ page }) => {
  const state = makeState();
  await mockApi(page, state);
  await page.goto("/app");

  await page.getByLabel("Nome da criança").fill("Lila");
  await page.getByLabel("Idade").fill("5");
  await page.getByLabel("Título do livro").fill("Lila e as estrelas");
  await page.getByLabel("Insira o tema desejado").fill("Aventura no espaço");
  await page.getByTestId("studio-photo-input").setInputFiles({
    name: "foto.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from("x"),
  });
  await page.getByTestId("studio-media-consent").check();
  await page.getByTestId("studio-create-project").click();
  await expect(page.getByTestId("studio-mount-ebook")).toBeDisabled();
});

test("path inexistente mostra 404", async ({ page }) => {
  await page.goto("/pagina-que-nao-existe");
  await expect(page.getByTestId("not-found-title")).toBeVisible();
  await expect(page.getByTestId("not-found-home")).toBeVisible();
});

test("landing sem preço e EN atualiza lang", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("landing-personalize").first()).toBeVisible();
  await expect(page.locator("body")).not.toContainText("US$ 39,99");
  await expect(page.locator("body")).not.toContainText("$39.99");
  await expect(page.locator("body")).not.toContainText("ECONOMIZE 33%");
  await page.getByTestId("landing-lang-en").click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.getByTestId("landing-lang-es").click();
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
});

test("menu mobile abre abaixo da logo", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const menuBtn = page.getByTestId("landing-menu");
  await menuBtn.click();
  await expect(menuBtn).toHaveAttribute("aria-expanded", "true");
  const logo = page.getByTestId("landing-brand").locator("img");
  const panel = page.getByTestId("landing-site-menu");
  await expect(panel).toBeVisible();
  const logoBox = await logo.boundingBox();
  const panelBox = await panel.boundingBox();
  expect(logoBox).toBeTruthy();
  expect(panelBox).toBeTruthy();
  expect(panelBox!.y).toBeGreaterThanOrEqual((logoBox!.y + logoBox!.height) - 8);
});
