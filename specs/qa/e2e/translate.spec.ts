import { test, expect } from "@playwright/test"

const mockSection = {
  id: "sec-1",
  type: "PARAGRAPH",
  originalText: "Original content here",
  autoTranslatedText: "Machine translated content",
  pageNumber: 5,
  bookTitle: "Dhammapada",
  bookId: "book-1",
}

test.describe("Translation Flow", () => {
  test.beforeEach(async ({ page }) => {
    // Mock section fetch
    await page.route("**/api/sections/next", (route) => {
      route.fulfill({ status: 200, body: JSON.stringify(mockSection) })
    })
  })

  test("TRANS-01: Get next section displays in editor", async ({ page }) => {
    await page.route("**/api/sections/*/my-translation", (route) => {
      route.fulfill({ status: 404 })
    })
    await page.goto("/translate")
    await page.click("text=Next Section")
    await expect(page.locator("text=Dhammapada")).toBeVisible()
    await expect(page.locator("text=— Page 5")).toBeVisible()
    await expect(page.locator("text=Machine translated content")).toBeVisible()
  })

  test("TRANS-02: Submit translation shows success message", async ({ page }) => {
    await page.route("**/api/sections/*/my-translation", (route) => {
      route.fulfill({ status: 404 })
    })
    await page.route("**/api/sections/*/translate", (route) => {
      route.fulfill({ status: 200, body: JSON.stringify({}) })
    })
    await page.goto("/translate")
    await page.click("text=Next Section")
    await page.fill("textarea", "My translation text")
    await page.click("text=Save Translation")
    await expect(page.locator("text=Translation saved!")).toBeVisible()
  })

  test("TRANS-03: Submit with exact letter transliteration", async ({ page }) => {
    await page.route("**/api/sections/*/my-translation", (route) => {
      route.fulfill({ status: 404 })
    })
    await page.route("**/api/sections/*/translate", (route) => {
      route.fulfill({ status: 200, body: JSON.stringify({}) })
    })
    await page.goto("/translate")
    await page.click("text=Next Section")
    await page.fill("textarea", "Translation")
    await page.fill("input[placeholder*='letter-for-letter']", "माता → මාතා")
    await page.click("text=Save Translation")
    await expect(page.locator("text=Translation saved!")).toBeVisible()
  })

  test("TRANS-04: Empty queue shows all translated message", async ({ page }) => {
    await page.route("**/api/sections/next", (route) => {
      route.fulfill({ status: 404 })
    })
    await page.goto("/translate")
    await page.click("text=Next Section")
    await expect(page.locator("text=All sections translated!")).toBeVisible()
  })

  test("TRANS-08: Skip loads next section", async ({ page }) => {
    await page.route("**/api/sections/*/my-translation", (route) => {
      route.fulfill({ status: 404 })
    })
    await page.goto("/translate")
    await page.click("text=Next Section")
    await page.click("text=Skip")
    // Should load the next section again
    await expect(page.locator("text=Dhammapada")).toBeVisible()
  })

  test("TRANS-12: Previous submission panel shown when pending translation exists", async ({
    page,
  }) => {
    await page.route("**/api/sections/*/my-translation", (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          translatedText: "My earlier translation",
          exactLetterTranslation: "exact text",
          isApproved: false,
        }),
      })
    })
    await page.goto("/translate")
    await page.click("text=Next Section")
    await expect(page.locator("text=My previous submission (pending review)")).toBeVisible()
    await expect(page.locator("text=My earlier translation")).toBeVisible()
    await expect(page.locator("text=Exact: exact text")).toBeVisible()
  })
})
