import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import React from "react"

const mockBooks = [
  {
    id: "book-1",
    title: "The Gita",
    author: "Vyasa",
    sourceLanguage: "sa",
    translateLanguages: ["si"],
    status: "READY",
    thumbnailKey: null,
    pageCount: 42,
    stats: {
      totalSections: 10,
      translatedSections: 5,
      inProgressSections: 0,
      pendingSections: 5,
      translationPercent: 50,
    },
  },
]

vi.mock("@/lib/api/books", () => ({
  getAvailableBooks: vi.fn(() => Promise.resolve(mockBooks)),
}))

import TranslatePage from "@/app/translate/page"

describe("TranslatePage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("renders the page title", async () => {
    render(React.createElement(TranslatePage))
    expect(screen.getByRole("heading", { name: "Translate" })).toBeInTheDocument()

    // Let the books-fetch effect settle so its setState isn't left dangling
    // outside act() once the test exits.
    await waitFor(() => {
      expect(screen.getByText("The Gita")).toBeInTheDocument()
    })
  })

  it("renders a book card for each available book", async () => {
    render(React.createElement(TranslatePage))
    await waitFor(() => {
      expect(screen.getByText("The Gita")).toBeInTheDocument()
    })
    expect(screen.getByText("Vyasa")).toBeInTheDocument()
  })

  it("links each book card to its workspace route", async () => {
    render(React.createElement(TranslatePage))
    await waitFor(() => {
      expect(screen.getByText("The Gita")).toBeInTheDocument()
    })
    const link = screen.getByText("The Gita").closest("a")
    expect(link).toHaveAttribute("href", "/translate/book-1")
  })
})
