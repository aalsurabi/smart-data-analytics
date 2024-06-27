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
  await page.getByRole('link', { name: 'Dashboard Häufigkeit der' }).click();
  await page.getByLabel('Datenmanager (ALT+⇧+3)').click();
  await page.getByTestId('data-browser-panel').getByLabel('Schließen (⇧+ESC)').click();
  await page.getByLabel('Datenmanager (ALT+⇧+3)').click();
});