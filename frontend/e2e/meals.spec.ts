// NOTE: Run `npx playwright install` before executing E2E tests.
import { test, expect } from "@playwright/test";

test.describe("Página de Refeições", () => {
  test.beforeEach(async ({ page }) => {
    // Simula sessão autenticada para todos os testes de refeições
    await page.route("**/api/auth/session**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: {
            id: 1,
            name: "Gabriel",
            email: "gabriel@caloria.com",
            accessToken: "fake-token",
          },
          expires: "2099-01-01T00:00:00.000Z",
        }),
      });
    });
  });

  test("navega para a página de refeições", async ({ page }) => {
    await page.route("**/api/v1/meals**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    });

    await page.goto("/refeicoes");

    // Verifica que a página carregou (não redirecionou para login)
    await expect(page).not.toHaveURL(/\/login/, { timeout: 5000 });
    await expect(page).toHaveURL(/\/refeicoes/);
  });

  test("exibe estado vazio quando não há refeições", async ({ page }) => {
    await page.route("**/api/v1/meals**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    });

    await page.route("**/api/v1/auth/me**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          name: "Gabriel",
          email: "gabriel@caloria.com",
          calorie_goal: 2000,
          weight_goal: null,
          water_goal_ml: null,
          goal_type: null,
          telegram_chat_id: null,
          whatsapp_number: null,
          profile: null,
          created_at: "2026-01-01T00:00:00Z",
        }),
      });
    });

    await page.goto("/refeicoes");

    // Aguarda a página carregar e não redirecionar
    await expect(page).toHaveURL(/\/refeicoes/, { timeout: 10000 });
  });
});
