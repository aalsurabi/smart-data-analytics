import { test, expect } from '@playwright/test';
import { writeFileSync } from 'fs';

test('test', async ({ page }) => {
  await page.goto('http://localhost:8080/cadenza/');
  await page.getByRole('link', { name: 'Anmelden' }).click();
  await page.getByLabel('Benutzername *').click();
  await page.getByLabel('Benutzername *').fill('Admin');
  await page.getByLabel('Benutzername *').press('Tab');
  await page.getByPlaceholder(' ').fill('Admin');
  await page.getByRole('button', { name: 'Anmelden' }).click();
  await page.getByRole('link', { name: 'Testmappe_Ladesaeulen', exact: true }).click();
  await page.getByTestId('workbook-header').getByRole('button', { name: 'Mehr' }).click();
  await page.getByText('disy Cadenza').click();
  await page.screenshot({ path: 'generated_screenshots/few_shot/25_1.png' });
  const htmlContent = await page.content();
  writeFileSync('generated_html/few_shot/25_1.html', htmlContent);
  await page.goto('http://localhost:8080/cadenza/logout');
});