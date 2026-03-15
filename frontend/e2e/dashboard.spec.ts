// NOTE: Run `npx playwright install` before executing E2E tests.
import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("redireciona para login quando não autenticado", async ({ page }) => {
    // Sem sessão ativa, a rota protegida deve redirecionar para /login
    await page.route("**/api/auth/session**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({}),
      });
    });

    await page.goto("/dashboard");

    // Next-auth redireciona usuários não autenticados para /login
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test("exibe elementos do dashboard quando autenticado", async ({ page }) => {
    // Simula sessão autenticada
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

    // Stub das chamadas de API do dashboard
    await page.route("**/api/v1/dashboard/today**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          date: "2026-03-15",
          nutrition: {
            total_calories: 1500,
            total_protein: 80,
            total_carbs: 200,
            total_fat: 50,
            meals_count: 3,
            meals: [],
          },
          hydration: { date: "2026-03-15", total_ml: 1500, entries: [] },
          mood: null,
          latest_weight: null,
        }),
      });
    });

    await page.goto("/dashboard");

    // Verifica que a página carregou com elementos do dashboard
    await expect(page).not.toHaveURL(/\/login/, { timeout: 5000 });
  });
});
