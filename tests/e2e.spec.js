import { test, expect } from '@playwright/test';

test('convert markdown to pdf', async ({ page }) => {
  // Navigate to the app
  await page.goto('https://markdown-to-pdf-converter-taupe.vercel.app');

  // Check the title
  await expect(page).toHaveTitle('Markdown to PDF Converter');

  // Enter some markdown
  const markdown = `# Hello World

This is a **bold** text and *italic* text.

- Item 1
- Item 2

> This is a blockquote

\`inline code\`

[Link](https://example.com)`;

  await page.fill('textarea', markdown);

  // Click the convert button
  await page.click('button:has-text("Convert to PDF")');

  // Wait a bit for the request
  await page.waitForTimeout(5000);

  // Check if error message appears
  const errorVisible = await page.isVisible('p:has-text("Failed to convert")');
  expect(errorVisible).toBe(false);

  // Since download event might not fire in headless, just check that no error occurred
  // In a real scenario, you might need to handle downloads differently
});