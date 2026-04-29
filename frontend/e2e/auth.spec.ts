// NOTE: Run `npx playwright install` before executing E2E tests.
import { test, expect } from "@playwright/test";

test.describe("Fluxo de autenticação", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
  });

  test("exibe o formulário de login com campos de e-mail e senha", async ({
    page,
  }) => {
    await expect(page.getByLabel(/e-mail/i)).toBeVisible();
    await expect(page.getByLabel(/senha/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /entrar/i })).toBeVisible();
  });

  test("exibe erro ao enviar credenciais inválidas", async ({ page }) => {
    // Intercepta a chamada de autenticação e simula falha
    await page.route("**/api/auth/callback/credentials**", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ error: "CredentialsSignin" }),
      });
    });

    await page.getByLabel(/e-mail/i).fill("usuario@invalido.com");
    await page.getByLabel(/senha/i).fill("senhaerrada");
    await page.getByRole("button", { name: /entrar/i }).click();

    await expect(
      page.getByText(/e-mail ou senha inválidos/i)
    ).toBeVisible({ timeout: 5000 });
  });

  test("redireciona para o dashboard após login bem-sucedido", async ({
    page,
  }) => {
    // Intercepta a resposta da sessão para simular login bem-sucedido
    await page.route("**/api/auth/callback/credentials**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ url: "http://localhost:3000/" }),
      });
    });

    await page.route("**/api/auth/session**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: {
            id: 1,
            name: "Gabriel",
            email: "gabriel@caloria.com",
          },
          expires: "2099-01-01T00:00:00.000Z",
        }),
      });
    });

    await page.getByLabel(/e-mail/i).fill("gabriel@caloria.com");
    await page.getByLabel(/senha/i).fill("senha123");
    await page.getByRole("button", { name: /entrar/i }).click();

    // Aguarda o redirecionamento para a raiz ou dashboard
    await expect(page).toHaveURL(/\/(dashboard)?$/, { timeout: 10000 });
  });
});
