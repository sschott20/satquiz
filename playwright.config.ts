import { defineConfig, devices } from '@playwright/test';

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
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    {
      name: 'mobile',
      // Mobile viewport on Chromium (avoids needing the WebKit binary in CI).
      use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
    },
  ],
});
