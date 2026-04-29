import { test, expect } from "@playwright/test";

const BASE_URL = process.env.BASE_URL ?? "https://frontend-nine-mu-59.vercel.app";
const TEST_EMAIL = `playwright_test_${Date.now()}@gmail.com`;
const TEST_PASSWORD = "Playwright@123";
const TEST_NAME = "Teste Playwright";

test.describe("Autenticação", () => {
  test("deve carregar a página de login", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await expect(page.getByRole("heading", { name: /bem-vindo/i })).toBeVisible();
    await expect(page.getByLabel(/e-mail/i)).toBeVisible();
    await expect(page.getByLabel(/senha/i)).toBeVisible();
  });

  test("deve rejeitar credenciais inválidas", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel(/e-mail/i).fill("invalido@test.com");
    await page.getByLabel(/senha/i).fill("senhaerrada");
    await page.getByRole("button", { name: /entrar/i }).click();
    await expect(page.getByText(/e-mail ou senha inválidos/i)).toBeVisible({ timeout: 10000 });
  });

  test("deve cadastrar novo usuário e redirecionar", async ({ page }) => {
    await page.goto(`${BASE_URL}/register`);

    await page.getByLabel(/nome/i).fill(TEST_NAME);
    await page.getByLabel(/e-mail/i).fill(TEST_EMAIL);
    await page.getByLabel(/^senha$/i).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: /criar conta/i }).click();

    await expect(page).toHaveURL(/(onboarding|dashboard|login)/, { timeout: 15000 });
  });

  test("deve fazer login com usuário existente", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel(/e-mail/i).fill("gabrielnegreirossaraiva38@gmail.com");
    await page.getByLabel(/senha/i).fill("082405@Gn");
    await page.getByRole("button", { name: /entrar/i }).click();

    await expect(page).toHaveURL(/(dashboard|onboarding)/, { timeout: 15000 });
  });
});
