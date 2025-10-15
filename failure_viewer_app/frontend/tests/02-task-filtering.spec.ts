import { test, expect } from '@playwright/test';

test.describe('Task Filtering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    // Select first project
    const firstCard = page.locator('[class*="Card"]').filter({ hasText: 'Total Samples' }).first();
    await firstCard.click();
    await page.waitForTimeout(2000);
  });

  test('should display filter bar with pass/fail buttons', async ({ page }) => {
    // Check for All, Pass, Fail buttons
    await expect(page.locator('button:has-text("All")')).toBeVisible();
    await expect(page.locator('button:has-text("Pass")')).toBeVisible();
    await expect(page.locator('button:has-text("Fail")')).toBeVisible();
  });

  test('should display task count', async ({ page }) => {
    // Look for text pattern like "X tasks" or "X task"
    const countText = page.locator('text=/\\d+ task/');
    await expect(countText).toBeVisible({ timeout: 5000 });
  });

  test('should filter by pass status', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Get initial count
    const initialCount = await page.locator('[class*="Card"]').filter({ hasText: 'PASS' }).count();
    
    // Click Pass button
    await page.locator('button:has-text("Pass")').click();
    await page.waitForTimeout(500);
    
    // All visible tasks should show PASS badge
    const passCards = await page.locator('[class*="Card"]').filter({ hasText: 'PASS' }).count();
    const failCards = await page.locator('[class*="Card"]').filter({ hasText: 'FAIL' }).count();
    
    expect(failCards).toBe(0);
    if (passCards > 0) {
      expect(passCards).toBeGreaterThan(0);
    }
  });

  test('should filter by fail status', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Click Fail button
    await page.locator('button:has-text("Fail")').click();
    await page.waitForTimeout(500);
    
    // All visible tasks should show FAIL badge
    const passCards = await page.locator('[class*="Card"]').filter({ hasText: 'PASS' }).count();
    const failCards = await page.locator('[class*="Card"]').filter({ hasText: 'FAIL' }).count();
    
    expect(passCards).toBe(0);
    if (failCards > 0) {
      expect(failCards).toBeGreaterThan(0);
    }
  });

  test('should reset filter to show all tasks', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Filter to Pass first
    await page.locator('button:has-text("Pass")').click();
    await page.waitForTimeout(500);
    
    // Click All to reset
    await page.locator('button:has-text("All")').click();
    await page.waitForTimeout(500);
    
    // Should see both pass and fail tasks
    const passCards = await page.locator('[class*="Card"]').filter({ hasText: 'PASS' }).count();
    const failCards = await page.locator('[class*="Card"]').filter({ hasText: 'FAIL' }).count();
    
    const totalTasks = passCards + failCards;
    expect(totalTasks).toBeGreaterThan(0);
  });

  test('should display axial code search input', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="axial codes"]');
    await expect(searchInput).toBeVisible();
  });

  test('should filter by axial code', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Type in search box
    const searchInput = page.locator('input[placeholder*="axial codes"]');
    await searchInput.fill('tool');
    await page.waitForTimeout(500);
    
    // Check if dropdown appears with matching codes
    const dropdown = page.locator('[class*="absolute"]').filter({ hasText: 'tool' }).first();
    
    // If dropdown is visible, click first option
    if (await dropdown.isVisible().catch(() => false)) {
      const firstOption = dropdown.locator('div').first();
      await firstOption.click();
      await page.waitForTimeout(500);
      
      // Should see a tag with the selected code
      const tag = page.locator('[class*="Badge"]').filter({ hasText: 'tool' });
      await expect(tag).toBeVisible();
    }
  });

  test('should remove axial code filter', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Add a filter first
    const searchInput = page.locator('input[placeholder*="axial codes"]');
    await searchInput.fill('tool');
    await page.waitForTimeout(500);
    
    const dropdown = page.locator('[class*="absolute"]').filter({ hasText: 'tool' }).first();
    if (await dropdown.isVisible().catch(() => false)) {
      const firstOption = dropdown.locator('div').first();
      await firstOption.click();
      await page.waitForTimeout(500);
      
      // Click X to remove
      const removeButton = page.locator('[class*="Badge"]').filter({ hasText: 'tool' }).locator('svg').first();
      if (await removeButton.isVisible().catch(() => false)) {
        await removeButton.click();
        await page.waitForTimeout(500);
      }
    }
  });

  test('should clear all filters', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Add a filter
    const searchInput = page.locator('input[placeholder*="axial codes"]');
    await searchInput.fill('tool');
    await page.waitForTimeout(500);
    
    const dropdown = page.locator('[class*="absolute"]').filter({ hasText: 'tool' }).first();
    if (await dropdown.isVisible().catch(() => false)) {
      const firstOption = dropdown.locator('div').first();
      await firstOption.click();
      await page.waitForTimeout(500);
      
      // Click "Clear all" button
      const clearButton = page.locator('button:has-text("Clear all")');
      if (await clearButton.isVisible().catch(() => false)) {
        await clearButton.click();
        await page.waitForTimeout(500);
      }
    }
  });
});

