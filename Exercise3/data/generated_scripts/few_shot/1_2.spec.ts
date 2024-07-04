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
  await page.getByText('Verzeichnis Gewässergüte', { exact: true }).click();
  const parentElement = await page.getByText('Arbeitsmappe Übersicht Messstellen').locator('..');
  await parentElement.locator('.d-icon.d-icon-bold.status-icon').click(); 
  await page.getByRole('link', { name: 'Tabelle Messstellenliste' }).click();
  const tableElement = await page.getByRole('table');
  const rows = await tableElement.locator('tr').all();
  for (const row of rows) {
    const cells = await row.locator('td').all();
    for (const cell of cells) {
      const textContent = await cell.textContent();
      console.log(textContent);
    }
  }
});