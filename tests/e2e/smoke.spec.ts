import { test, expect } from '@playwright/test';

test('runs a tiny session end-to-end', async ({ page }) => {
  await page.goto('/');

  // Wait for the bank to load and Setup to render.
  await expect(page.getByRole('heading', { name: 'SAT Practice' })).toBeVisible();

  await page.getByLabel('Math').check();
  await page.getByLabel('Number of questions').fill('3');
  await page.getByLabel('Time limit (minutes)').fill('15');
  // The fixture only has 3 math questions total; one is "active". Disable the
  // exclude-active filter so all three are eligible.
  await page.getByLabel('Exclude active (practice-test) questions').uncheck();

  await page.getByRole('button', { name: 'Start' }).click();

  await expect(page.getByText(/Question 1 of 3/)).toBeVisible();

  for (let i = 0; i < 3; i++) {
    // The first MCQ choice button. Each ChoiceButton renders a letter button + a cross-out button.
    await page.locator('button[aria-pressed]', { hasText: 'A' }).or(
      page.locator('input.spr'),
    ).first().click({ trial: false });

    // If the question is SPR, click won't suffice — fill the input.
    const sprVisible = await page.locator('input.spr').isVisible().catch(() => false);
    if (sprVisible) {
      await page.locator('input.spr').fill('3');
    }

    if (i < 2) {
      await page.getByRole('button', { name: 'Next' }).click();
    } else {
      page.once('dialog', (d) => d.accept());
      await page.getByRole('button', { name: 'Submit' }).click();
    }
  }

  await expect(page.getByRole('heading', { name: /Score: \d \/ 3/ })).toBeVisible();
});
