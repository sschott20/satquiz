import { test, expect } from '@playwright/test';

test('user gate, session with drill, and history flow', async ({ page }) => {
  await page.goto('/');

  // User gate.
  await expect(page.getByRole('heading', { name: 'SAT Practice' })).toBeVisible();
  await page.getByLabel('username').fill('Tester');
  await page.getByRole('button', { name: 'Start' }).click();

  // Setup screen.
  await expect(page.getByRole('button', { name: /Switch user \(Tester\)/ })).toBeVisible();
  await page.getByLabel('Math').check();
  await page.getByLabel('Number of questions').fill('3');
  // Time field stays blank → no timer.
  await page.getByLabel('Exclude active (practice-test) questions').uncheck();
  await page.getByRole('button', { name: 'Start' }).click();

  // Session screen — no timer visible.
  await expect(page.getByText(/Question 1 of 3/)).toBeVisible();
  await expect(page.getByText('No time limit')).toBeVisible();

  // Answer all questions with a likely-wrong value (A for MCQ, "999999" for SPR).
  for (let i = 0; i < 3; i++) {
    const sprVisible = await page.locator('input.spr').first().isVisible().catch(() => false);
    if (sprVisible) {
      await page.locator('input.spr').fill('999999');
    } else {
      await page.locator('button[aria-pressed]').first().click();
    }
    if (i < 2) {
      await page.getByRole('button', { name: 'Next' }).click();
    } else {
      page.once('dialog', (d) => d.accept());
      await page.getByRole('button', { name: 'Submit' }).click();
    }
  }

  // Review screen.
  await expect(page.getByRole('heading', { name: /Score: \d \/ 3/ })).toBeVisible();

  // Expand the first row.
  await page.locator('[data-testid="result-row"]').first().click();

  // Navigate to History.
  await page.getByRole('button', { name: 'History' }).click();
  await expect(page.getByRole('heading', { name: /History — Tester/ })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Sessions' })).toBeVisible();
  await expect(page.getByRole('tab', { name: 'All questions' })).toBeVisible();

  // The session just completed shows up.
  await expect(page.locator('table.sessions tbody tr').first()).toBeVisible();
});
