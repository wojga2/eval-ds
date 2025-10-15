import { test, expect } from '@playwright/test';

test.describe('Project Selection', () => {
  test('should display app title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Failure Viewer App/);
  });

  test('should show project selection header', async ({ page }) => {
    await page.goto('/');
    const header = page.locator('h1:has-text("Failure Viewer App")');
    await expect(header).toBeVisible();
  });

  test('should display "Select a Project" heading', async ({ page }) => {
    await page.goto('/');
    const heading = page.locator('h2:has-text("Select a Project")');
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('should load and display project cards', async ({ page }) => {
    await page.goto('/');
    
    // Wait for projects to load
    await page.waitForTimeout(2000);
    
    // Check if any project cards exist
    const projectCards = page.locator('[class*="Card"]').filter({ hasText: 'Total Samples' });
    const count = await projectCards.count();
    
    // Should have at least one project
    expect(count).toBeGreaterThan(0);
  });

  test('should display project statistics', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    // Find first project card
    const firstCard = page.locator('[class*="Card"]').filter({ hasText: 'Total Samples' }).first();
    await expect(firstCard).toBeVisible();
    
    // Check for statistics
    await expect(firstCard.locator('text=Total Samples')).toBeVisible();
    await expect(firstCard.locator('text=Success')).toBeVisible();
    await expect(firstCard.locator('text=Failed')).toBeVisible();
  });

  test('should allow selecting a project', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    // Click first project card
    const firstCard = page.locator('[class*="Card"]').filter({ hasText: 'Total Samples' }).first();
    await firstCard.click();
    
    // Wait for project to load
    await page.waitForTimeout(2000);
    
    // Check if "Back to Projects" button appears
    const backButton = page.locator('button:has-text("Back to Projects")');
    await expect(backButton).toBeVisible({ timeout: 10000 });
  });

  test('should navigate back to project list', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    // Select a project
    const firstCard = page.locator('[class*="Card"]').filter({ hasText: 'Total Samples' }).first();
    await firstCard.click();
    await page.waitForTimeout(2000);
    
    // Click back button
    const backButton = page.locator('button:has-text("Back to Projects")');
    await backButton.click();
    await page.waitForTimeout(1000);
    
    // Should see project selection again
    const heading = page.locator('h2:has-text("Select a Project")');
    await expect(heading).toBeVisible();
  });
});

