import { test, expect } from '@playwright/test';

test.describe('Inkdown Landing', () => {
  test('has correct title and hero', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Inkdown/);
    await expect(page.locator('h1')).toContainText('Beautiful PDFs from Markdown');
  });

  test('landing links to editor', async ({ page }) => {
    await page.goto('/');
    const editorLink = page.locator('a:has-text("Start Writing")');
    await expect(editorLink).toBeVisible();
    await expect(editorLink).toHaveAttribute('href', '/editor');
  });

  test('landing links to IntelliForge AI', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=IntelliForge AI').first()).toBeVisible();
  });
});

test.describe('Inkdown Editor', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/editor');
  });

  test('renders editor with textarea and tabs', async ({ page }) => {
    await expect(page.locator('textarea')).toBeVisible();
    await expect(page.getByText('Markdown', { exact: true }).first()).toBeVisible();
  });

  test('live preview updates as user types', async ({ page }) => {
    const textarea = page.locator('textarea');
    await textarea.clear();
    await textarea.fill('# Hello World\n\nThis is **bold** text.');

    const preview = page.locator('.prose');
    await expect(preview.locator('h1')).toContainText('Hello World');
    await expect(preview.locator('strong')).toContainText('bold');
  });

  test('template dropdown loads templates', async ({ page }) => {
    await page.click('button:has-text("Templates")');
    await expect(page.getByText('Resume', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Project README', { exact: true })).toBeVisible();

    await page.getByText('Resume', { exact: true }).first().click();
    const textarea = page.locator('textarea');
    await expect(textarea).toContainText('Jane Smith');
  });

  test('new document clears editor', async ({ page }) => {
    await page.click('button:has-text("New")');
    const textarea = page.locator('textarea');
    await expect(textarea).toHaveValue('');
  });

  test('export dialog opens and has settings', async ({ page }) => {
    await page.click('button:has-text("Export PDF")');
    await expect(page.locator('text=Configure your PDF export')).toBeVisible();
    await expect(page.locator('#filename')).toBeVisible();
    await expect(page.locator('#page-size')).toBeVisible();
    await expect(page.locator('#margin')).toBeVisible();
  });

  test('export dialog validates empty content', async ({ page }) => {
    const textarea = page.locator('textarea');
    await textarea.clear();

    await page.click('button:has-text("Export PDF")');
    const downloadBtn = page.locator('button:has-text("Download PDF")');
    await expect(downloadBtn).toBeDisabled();
  });

  test('keyboard shortcut opens export dialog', async ({ page }) => {
    await page.keyboard.press('Control+Shift+e');
    await expect(page.locator('text=Configure your PDF export')).toBeVisible();
  });
});
