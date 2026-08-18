import { expect, test, type Page } from "@playwright/test";
import { mockApi } from "./mock-api";

async function openStudio(page: Page) {
  await page.goto("/app");
  await expect(page.getByText(/créditos:\s*10/i)).toBeVisible();
}

async function createProject(page: Page) {
  await page.getByRole("button", { name: /criar projeto/i }).click();
  await expect(page.getByRole("heading", { name: /^projeto$/i })).toBeVisible();
}

async function uploadChildPhoto(page: Page) {
  await page
    .locator('input[type="file"]')
    .first()
    .setInputFiles({
      name: "foto.jpg",
      mimeType: "image/jpeg",
      buffer: Buffer.from("fake-image"),
    });
  await page.getByRole("button", { name: /enviar foto/i }).click();
}

test.describe("Padrão visual da foto (e2e)", () => {
  test("mostra dicas e gera personagem quando a foto passa no padrão", async ({ page }) => {
    await mockApi(page);
    await openStudio(page);
    await createProject(page);

    await expect(page.getByRole("heading", { name: /padrão visual da foto/i })).toBeVisible();
    await expect(page.getByText(/nítida, bem iluminada e centralizada/i)).toBeVisible();
    await expect(page.getByText(/mais de uma pessoa na foto/i)).toBeVisible();
    await expect(page.getByText(/rosto de lado/i)).toBeVisible();

    await uploadChildPhoto(page);

    await expect(page.locator(".jobs .jtype")).toHaveText("AVATAR");
    await expect(page.getByTestId("photo-standard-reasons")).toHaveCount(0);
  });

  test("bloqueia o avatar e lista o motivo quando a foto falha no padrão", async ({ page }) => {
    await mockApi(page, { rejectPhoto: true });
    await openStudio(page);
    await createProject(page);

    await uploadChildPhoto(page);

    await expect(page.getByTestId("photo-standard-reasons")).toHaveText(
      /mais de uma pessoa/i,
    );
    await expect(page.getByRole("alert")).toHaveText(/padrão visual para criar o avatar/i);
    await expect(page.locator(".jobs")).toHaveCount(0);
  });
});
