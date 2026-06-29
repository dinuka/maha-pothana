import { test, expect } from "@playwright/test"

test.describe("Book Organization & Publishing", () => {
  test("ORG-03: Filter pages by completion status", async ({ page }) => {
    await page.goto("/books/book-1")
    await page.click("text=Completed")
    // Only completed pages should show
    const pageItems = page.locator("[data-testid='page-item']")
    const count = await pageItems.count()
    for (let i = 0; i < count; i++) {
      await expect(pageItems.nth(i)).toContainText("100%")
    }
  })

  test("ORG-05: Review translations shows all submitted", async ({ page }) => {
    await page.goto("/books/book-1")
    await page.click("text=Review")
    await expect(page.locator("text=Translation 1")).toBeVisible()
  })

  test("ORG-06: Approve translation marks it approved", async ({ page }) => {
    await page.route("**/api/translations/*/approve", (route) => {
      route.fulfill({ status: 200 })
    })
    await page.goto("/books/book-1")
    await page.click("text=Review")
    await page.click("text=Approve")
    await expect(page.locator("[data-testid='approved-badge']")).toBeVisible()
  })

  test("ORG-11: Build button triggers book build", async ({ page }) => {
    let buildCalled = false
    await page.route("**/api/books/*/build", (route) => {
      buildCalled = true
      route.fulfill({ status: 200, body: JSON.stringify({ status: "BUILDING" }) })
    })
    await page.goto("/books/book-1")
    await page.click("text=Build")
    await expect(buildCalled).toBe(true)
  })
})
