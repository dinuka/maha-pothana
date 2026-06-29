import { test, expect } from "@playwright/test"

test.describe("Book Upload", () => {
  test("UPLOAD-01: Upload valid PDF and redirect to book console", async ({ page }) => {
    await page.goto("/books/new")
    await page.fill("input[placeholder='Enter book title']", "Test Book")
    await page.fill("input[placeholder='Enter author name']", "Test Author")
    await page.selectOption("select", { label: "Sinhala" })
    await page.click("text=English")
    await page.setInputFiles("input[type='file']", {
      name: "test.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("fake PDF content"),
    })
    await page.route("**/api/books", (route) => {
      route.fulfill({ status: 200, body: JSON.stringify({ id: "book-123" }) })
    })
    await page.click("text=Upload Book")
    await page.waitForURL("/books/book-123")
  })

  test("UPLOAD-02: Duplicate book shows error", async ({ page }) => {
    await page.route("**/api/books", (route) => {
      route.fulfill({ status: 409, body: JSON.stringify({ message: "This book has already been uploaded" }) })
    })
    await page.goto("/books/new")
    await page.fill("input[placeholder='Enter book title']", "Duplicate")
    await page.fill("input[placeholder='Enter author name']", "Author")
    await page.selectOption("select", { label: "Sinhala" })
    await page.click("text=English")
    await page.setInputFiles("input[type='file']", {
      name: "dup.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("dup"),
    })
    await page.click("text=Upload Book")
    await expect(page.locator("text=This book has already been uploaded")).toBeVisible()
  })

  test("UPLOAD-03: Non-PDF file rejected", async ({ page }) => {
    await page.goto("/books/new")
    await page.setInputFiles("input[type='file']", {
      name: "image.png",
      mimeType: "image/png",
      buffer: Buffer.from("PNG"),
    })
    await expect(page.locator("text=Please upload a PDF file")).toBeVisible()
  })

  test("UPLOAD-04: Missing required fields shows validation", async ({ page }) => {
    await page.goto("/books/new")
    await page.click("text=Upload Book")
    await expect(page.locator("text=Please fill all required fields")).toBeVisible()
  })

  test("UPLOAD-07: Translator cannot access upload page", async ({ page }) => {
    await page.goto("/books/new")
    // Should be redirected since translator doesn't have EDITOR role
    await page.waitForURL((url) => !url.pathname.includes("/books/new"))
  })

  test("UPLOAD-08: Multiple target languages selected", async ({ page }) => {
    await page.goto("/books/new")
    await page.selectOption("select", { label: "Sinhala" })
    await page.click("text=English")
    await page.click("text=Tamil")
    await page.click("text=Sanskrit")
    const selectedChips = page.locator("button", { has: page.locator('[style*="background: var(--primary)"]') })
    await expect(selectedChips).toHaveCount(3)
  })
})
