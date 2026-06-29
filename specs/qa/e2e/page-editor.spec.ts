import { test, expect } from "@playwright/test"

test.describe("Section Detection & Editing", () => {
  test("SECT-01: Sections appear after detection", async ({ page }) => {
    await page.goto("/books/book-1/pages/1")
    await expect(page.locator("text=Add Section")).toBeVisible()
  })

  test("SECT-04: Delete section removes it", async ({ page }) => {
    await page.goto("/books/book-1/pages/1")
    // Click a section rectangle
    const rect = page.locator("[data-testid='rect']").first()
    await rect.click()
    await page.click("text=Delete")
    await expect(page.locator("[data-testid='rect']")).toHaveCount(0)
  })

  test("SECT-05: Add new section starts drawing mode", async ({ page }) => {
    await page.goto("/books/book-1/pages/1")
    await page.click("text=Add Section")
    await expect(page.locator("text=Cancel Draw")).toBeVisible()
  })

  test("SECT-07: Confirm sections button triggers save", async ({ page }) => {
    let savedSections: unknown = null
    await page.route("**/api/books/*/pages/*/sections", (route) => {
      savedSections = route.request().postDataJSON()
      route.fulfill({ status: 200 })
    })
    await page.goto("/books/book-1/pages/1")
    await page.click("text=Confirm Sections")
    expect(savedSections).not.toBeNull()
  })

  test("SECT-06: Change section type updates color", async ({ page }) => {
    await page.goto("/books/book-1/pages/1")
    const rect = page.locator("[data-testid='rect']").first()
    await rect.click()
    await page.selectOption("select", "FOOTNOTE")
    // Color should update to orange for FOOTNOTE
    await expect(rect).toHaveCSS("stroke", "rgb(249, 115, 22)")
  })
})
