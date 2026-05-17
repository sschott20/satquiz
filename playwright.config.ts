import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  webServer: {
    command: 'npm run dev -- --port=5180',
    port: 5180,
    reuseExistingServer: !process.env.CI,
  },
  use: {
    baseURL: 'http://localhost:5180',
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
});
