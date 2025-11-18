import { defineConfig, devices } from '@playwright/test';

const PORT = process.env.PORT || '3000';
const BASE_URL =
  process.env.E2E_BASE_URL ||
  `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 90_000,
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ['list'],
    process.env.CI ? ['html', { open: 'never' }] : ['html', { open: 'on-failure' }],
  ],
  use: {
    baseURL: BASE_URL,
    trace: process.env.CI ? 'on-first-retry' : 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1440, height: 900 },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: process.env.CI
    ? [
        {
          command: 'npm run start',
          cwd: __dirname,
          env: {
            ...process.env,
            BROWSER: 'none',
          },
          port: Number(PORT),
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
      ]
    : undefined,
});





