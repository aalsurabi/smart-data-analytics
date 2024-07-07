import { defineConfig } from '@playwright/test';

export default defineConfig({
  workers: 1,
  timeout: 15000,
  reporter: [
    ['list'],
    ['json', {  outputFile: 'test_results.json' }]
  ],
});