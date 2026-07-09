import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import React from "react"

vi.mock("@/lib/apiClientBrowser", () => ({
  apiFetchBrowser: vi.fn(),
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}))

import { HistoryTab } from "@/app/translate/HistoryTab"
import { apiFetchBrowser } from "@/lib/apiClientBrowser"

const mockFilters = {
  tab: "history",
  bookId: "book-1",
  language: null,
  page: null,
  status: null,
}

describe("HistoryTab", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("shows loading state initially", () => {
    ;(apiFetchBrowser as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))

    render(
      React.createElement(HistoryTab, {
        filters: mockFilters,
        onSectionClick: vi.fn(),
      }),
    )

    expect(screen.getByText("Loading history...")).toBeInTheDocument()
  })

  it("renders history items", async () => {
    ;(apiFetchBrowser as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          items: [
            {
              id: "h1",
              translationId: "t1",
              sectionId: "s1",
              pageNumber: 1,
              sectionOrder: 0,
              translatorId: "u1",
              translatorName: "Kamal",
              translatedText: "Translation text here",
              action: "APPROVED",
              performedBy: null,
              performedByName: "Nimal",
              createdAt: "2026-07-05T14:30:00Z",
            },
          ],
          nextCursor: null,
          hasMore: false,
        }),
    })

    render(
      React.createElement(HistoryTab, {
        filters: mockFilters,
        onSectionClick: vi.fn(),
      }),
    )

    await waitFor(() => {
      expect(screen.getByText(/Page 1, Section 1/)).toBeInTheDocument()
      expect(screen.getByText(/Translation text here/)).toBeInTheDocument()
      expect(screen.getByText(/APPROVED/)).toBeInTheDocument()
    })
  })

  it("shows empty state when no items", async () => {
    ;(apiFetchBrowser as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          items: [],
          nextCursor: null,
          hasMore: false,
        }),
    })

    render(
      React.createElement(HistoryTab, {
        filters: mockFilters,
        onSectionClick: vi.fn(),
      }),
    )

    await waitFor(() => {
      expect(screen.getByText("No translations yet")).toBeInTheDocument()
    })
  })
})
