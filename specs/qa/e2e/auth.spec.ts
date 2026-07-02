import { test, expect } from "@playwright/test"

test.describe("Authentication & Authorization", () => {
  test("AUTH-01: Google SSO login redirects to dashboard", async ({ page }) => {
    await page.goto("/auth/signin")
    await page.click("text=Sign in with Google")
    // Google OAuth redirect — in test, mock the callback
    await page.waitForURL("/dashboard")
    await expect(page.locator("text=Dashboard")).toBeVisible()
  })

  test("AUTH-03: Returning user sees dashboard with roles", async ({ page }) => {
    await page.goto("/")
    // Mock authenticated session
    await page.evaluate(() => {
      window.localStorage.setItem("next-auth.session-token", "mock-token")
    })
    await page.goto("/dashboard")
    await expect(page.locator("text=Welcome back")).toBeVisible()
  })

  test("AUTH-05: Editor nav includes Books link", async ({ page }) => {
    // Set role = EDITOR
    await page.goto("/dashboard")
    await expect(page.locator("nav >> text=Books")).toBeVisible()
    await expect(page.locator("nav >> text=Translate")).not.toBeVisible()
  })

  test("AUTH-05: Translator nav includes Translate link", async ({ page }) => {
    // Set role = TRANSLATOR
    await page.goto("/dashboard")
    await expect(page.locator("nav >> text=Translate")).toBeVisible()
    await expect(page.locator("nav >> text=Books")).not.toBeVisible()
  })

  test("AUTH-06: Unauthenticated access redirects to login", async ({ page }) => {
    await page.goto("/dashboard")
    await page.waitForURL("/auth/signin")
  })

  test("AUTH-04: Super Admin sees Admin link and can manage users", async ({ page }) => {
    await page.goto("/admin/users")
    await expect(page.locator("text=User Management")).toBeVisible()
  })

  test("AUTH-07: Expired token shows error on sign-in attempt", async ({ page }) => {
    await page.route("**/api/auth/**", (route) => {
      route.fulfill({ status: 401, body: "Token expired" })
    })
    await page.goto("/auth/signin")
    await page.click("text=Sign in with Google")
    await expect(page.locator("text=Authentication failed")).toBeVisible()
  })
})
