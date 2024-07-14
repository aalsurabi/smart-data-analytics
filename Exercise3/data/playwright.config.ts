import { defineConfig } from '@playwright/test';

export default defineConfig({
  workers: 1,
  timeout: 20000,
  reporter: [
    ['list'],
    ['json', {  outputFile: 'test_results.json' }]
  ],
});