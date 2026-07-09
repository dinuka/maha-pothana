import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import React from "react"

vi.mock("@/lib/apiClientBrowser", () => ({
  apiFetchBrowser: vi.fn(),
}))

import { BookProgressHeader } from "@/app/translate/components/BookProgressHeader"
import { apiFetchBrowser } from "@/lib/apiClientBrowser"

describe("BookProgressHeader", () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("renders nothing before stats load", () => {
    ;(apiFetchBrowser as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))

    const { container } = render(React.createElement(BookProgressHeader, { bookId: "book-1" }))

    expect(container).toBeEmptyDOMElement()
  })

  it("renders the compact progress strip when stats load", async () => {
    ;(apiFetchBrowser as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            totalSections: 100,
            translatedSections: 37,
            pendingSections: 10,
            inProgressSections: 5,
            translationPercent: 37.0,
            byLanguage: { si: { total: 100, translated: 37, percent: 37.0 } },
            byPage: [{ pageNumber: 1, total: 10, translated: 5, percent: 50.0 }],
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      })

    render(React.createElement(BookProgressHeader, { bookId: "book-1" }))

    await waitFor(() => {
      expect(screen.getByText("37%")).toBeInTheDocument()
    })
    expect(screen.getByText("✅ 37")).toBeInTheDocument()
    expect(screen.getByText("⏳ 10")).toBeInTheDocument()
    expect(screen.queryByText("Per-Language Breakdown")).not.toBeInTheDocument()
  })

  it("expands to show the detailed breakdown on toggle", async () => {
    ;(apiFetchBrowser as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            totalSections: 100,
            translatedSections: 37,
            pendingSections: 10,
            inProgressSections: 5,
            translationPercent: 37.0,
            byLanguage: { si: { total: 100, translated: 37, percent: 37.0 } },
            byPage: [{ pageNumber: 1, total: 10, translated: 5, percent: 50.0 }],
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      })

    render(React.createElement(BookProgressHeader, { bookId: "book-1" }))

    await waitFor(() => {
      expect(screen.getByText("37%")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText("View details ▾"))

    expect(screen.getByText("Per-Language Breakdown")).toBeInTheDocument()
    expect(screen.getByText("Per-Page Breakdown")).toBeInTheDocument()
  })

  it("renders an error message on failure", async () => {
    ;(apiFetchBrowser as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 500,
    })

    render(React.createElement(BookProgressHeader, { bookId: "book-1" }))

    await waitFor(() => {
      expect(screen.getByText("Failed to load progress")).toBeInTheDocument()
    })
  })
})
