import { test, expect } from '@playwright/test';

test('has title and dashboard loaded', async ({ page }) => {
  await page.goto('http://127.0.0.1:3005');
  
  // App should redirect to /dashboard and show "Inventory App" in the sidebar
  await expect(page).toHaveURL(/.*\/dashboard/);
  await expect(page.locator('h1').filter({ hasText: 'Inventory App' })).toBeVisible();

  // Dashboard Summary should be visible
  await expect(page.locator('h1').filter({ hasText: 'Dashboard Summary' })).toBeVisible({ timeout: 15000 });
});

test('can navigate to products', async ({ page }) => {
  await page.goto('http://127.0.0.1:3005');
  
  // Click on Products link
  const productsLink = page.locator('nav a').filter({ hasText: 'Products' });
  await productsLink.click();
  
  // Wait for the URL to change
  await expect(page).toHaveURL(/.*\/products/);
  
  // Ensure we see the Products heading
  await expect(page.locator('h1').filter({ hasText: 'Products' }).first()).toBeVisible();
});
