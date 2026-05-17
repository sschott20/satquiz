import { test, expect } from '@playwright/test';

test('runs a tiny session and shows explanations on review', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'SAT Practice' })).toBeVisible();

  await page.getByLabel('Math').check();
  await page.getByLabel('Number of questions').fill('3');
  await page.getByLabel('Time limit (minutes)').fill('15');
  await page.getByLabel('Exclude active (practice-test) questions').uncheck();

  await page.getByRole('button', { name: 'Start' }).click();

  await expect(page.getByText(/Question 1 of 3/)).toBeVisible();

  for (let i = 0; i < 3; i++) {
    const sprVisible = await page.locator('input.spr').first().isVisible().catch(() => false);
    if (sprVisible) {
      await page.locator('input.spr').fill('3');
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

  // Expand the first row; all fixture math questions have explanations.
  await page.locator('tbody tr').first().click();
  await expect(page.getByTestId('explanation')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Explanation' })).toBeVisible();

  // Collapsing hides it again.
  await page.locator('tbody tr').first().click();
  await expect(page.getByTestId('explanation')).not.toBeVisible();
});
