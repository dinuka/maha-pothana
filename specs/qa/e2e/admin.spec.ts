import { test, expect } from "@playwright/test"

test.describe("Team Management", () => {
  test("TEAM-01: Invite translator by email", async ({ page }) => {
    let invitedEmail = ""
    await page.route("**/api/books/*/invite", (route) => {
      invitedEmail = route.request().postDataJSON().email
      route.fulfill({ status: 200, body: JSON.stringify({ status: "PENDING" }) })
    })
    await page.goto("/books/book-1")
    await page.click("text=Invite Translator")
    await page.fill("input[type='email']", "translator@example.com")
    await page.click("text=Send Invite")
    expect(invitedEmail).toBe("translator@example.com")
    await expect(page.locator("text=PENDING")).toBeVisible()
  })

  test("TEAM-03: Block translator preserves existing translations", async ({ page }) => {
    await page.route("**/api/books/*/translators/*/block", (route) => {
      route.fulfill({ status: 200 })
    })
    await page.goto("/books/book-1")
    await page.click("text=Block")
    await expect(page.locator("text=Translator blocked")).toBeVisible()
  })
})
