import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import React from "react"

vi.mock("@/lib/apiClientBrowser", () => ({
  apiFetchBrowser: vi.fn(),
}))

import { StatsTab } from "@/app/translate/StatsTab"
import { apiFetchBrowser } from "@/lib/apiClientBrowser"

describe("StatsTab", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("shows loading state", () => {
    ;(apiFetchBrowser as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))

    render(React.createElement(StatsTab, { bookId: "book-1" }))

    expect(screen.getByText("Loading statistics...")).toBeInTheDocument()
  })

  it("renders stats when data loads", async () => {
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

    render(React.createElement(StatsTab, { bookId: "book-1" }))

    await waitFor(() => {
      expect(screen.getByText("Translation Progress")).toBeInTheDocument()
      expect(screen.getByText("37%")).toBeInTheDocument()
      expect(screen.getByText("Approved: 37")).toBeInTheDocument()
      expect(screen.getByText("Pending: 10")).toBeInTheDocument()
      expect(screen.getByText("Total: 100")).toBeInTheDocument()
    })
  })

  it("renders error state on failure", async () => {
    ;(apiFetchBrowser as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 500,
    })

    render(React.createElement(StatsTab, { bookId: "book-1" }))

    await waitFor(() => {
      expect(screen.getByText("Failed to load statistics")).toBeInTheDocument()
    })
  })
})
