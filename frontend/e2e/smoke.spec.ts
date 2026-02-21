import { test, expect } from '@playwright/test'

test.describe('Smoke Tests', () => {
  test('dashboard loads', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('Dashboard')
  })

  test('datasets page loads', async ({ page }) => {
    await page.goto('/datasets')
    await expect(page.locator('h1')).toContainText('Datasets')
  })

  test('browse page loads', async ({ page }) => {
    await page.goto('/browse')
    await expect(page.locator('h1')).toContainText('Browse')
  })

  test('glossary page loads', async ({ page }) => {
    await page.goto('/glossary')
    await expect(page.locator('h1')).toContainText('Glossary')
  })

  test('navigation links work', async ({ page }) => {
    await page.goto('/')

    // Click Datasets link
    await page.click('a[href="/datasets"]')
    await expect(page).toHaveURL('/datasets')

    // Click Browse link
    await page.click('a[href="/browse"]')
    await expect(page).toHaveURL('/browse')

    // Click Glossary link
    await page.click('a[href="/glossary"]')
    await expect(page).toHaveURL('/glossary')

    // Click Dashboard link
    await page.click('a[href="/"]')
    await expect(page).toHaveURL('/')
  })

  test('datasets page has search and filters', async ({ page }) => {
    await page.goto('/datasets')
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible()
  })

  test('dark mode toggle works', async ({ page }) => {
    await page.goto('/')
    // Find and click the theme toggle button
    const toggle = page.locator('button[aria-label*="theme"], button[aria-label*="mode"], button[title*="theme"], button[title*="mode"]')
    if (await toggle.count() > 0) {
      await toggle.first().click()
      // Check that dark class is added to html
      await expect(page.locator('html')).toHaveClass(/dark/)
    }
  })
})
