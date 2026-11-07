import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  workers: 1,
  retries: 0,
  timeout: 120000,
  reporter: [['line']],
  outputDir: '/tmp/cu09-artifacts/results',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173',
    browserName: 'chromium',
    headless: true,
    trace: 'off',
    screenshot: 'off',
  },
});
