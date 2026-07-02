import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import React from "react"

import TranslatePage from "@/app/translate/page"

describe("TranslatePage", () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn()
    globalThis.fetch = fetchMock
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("renders initial empty state with Next Section button", () => {
    render(React.createElement(TranslatePage))
    expect(screen.getByText("Translate")).toBeInTheDocument()
    expect(screen.getByText("Next Section")).toBeInTheDocument()
    expect(screen.getByText(/Click below to get started/)).toBeInTheDocument()
  })

  it("fetches next section on button click", async () => {
    fetchMock
      .mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: () =>
          Promise.resolve({
            id: "sec-1",
            type: "PARAGRAPH",
            originalText: "Original text",
            autoTranslatedText: "Auto translated",
            pageNumber: 5,
            bookTitle: "Test Book",
            book: { id: "book-1" },
          }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
      })

    render(React.createElement(TranslatePage))
    fireEvent.click(screen.getByText("Next Section"))

    await waitFor(() => {
      expect(screen.getByText("Test Book")).toBeInTheDocument()
      expect(screen.getByText("— Page 5")).toBeInTheDocument()
    })
  })

  it("shows all sections translated when 404 returned", async () => {
    fetchMock.mockResolvedValueOnce({
      status: 404,
      ok: false,
    })

    render(React.createElement(TranslatePage))
    fireEvent.click(screen.getByText("Next Section"))

    await waitFor(() => {
      expect(screen.getByText("All sections translated!")).toBeInTheDocument()
    })
  })

  it("loads section into editor", async () => {
    fetchMock
      .mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: () =>
          Promise.resolve({
            id: "sec-2",
            type: "PARAGRAPH",
            originalText: "Orig",
            autoTranslatedText: "Machine translation",
            pageNumber: 1,
            bookTitle: "Bhagavad Gita",
            book: { id: "book-2" },
          }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
      })

    render(React.createElement(TranslatePage))
    fireEvent.click(screen.getByText("Next Section"))

    await waitFor(() => {
      expect(screen.getByDisplayValue("Machine translation")).toBeInTheDocument()
      expect(screen.getByPlaceholderText("Enter your translation here...")).toBeInTheDocument()
    })
  })

  it("renders exact letter input field", async () => {
    fetchMock
      .mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: () =>
          Promise.resolve({
            id: "sec-3",
            type: "PARAGRAPH",
            originalText: "Orig",
            autoTranslatedText: "Auto",
            pageNumber: 1,
            bookTitle: "Book",
            book: { id: "b1" },
          }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
      })

    render(React.createElement(TranslatePage))
    fireEvent.click(screen.getByText("Next Section"))

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/letter-for-letter/)).toBeInTheDocument()
      expect(screen.getByText("Exact letter transliteration")).toBeInTheDocument()
    })
  })

  it("calls API on save and shows success message", async () => {
    fetchMock
      .mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: () =>
          Promise.resolve({
            id: "sec-4",
            type: "PARAGRAPH",
            originalText: "Orig",
            autoTranslatedText: "Auto",
            pageNumber: 1,
            bookTitle: "Book",
            book: { id: "b1" },
          }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      })

    render(React.createElement(TranslatePage))
    fireEvent.click(screen.getByText("Next Section"))

    await waitFor(() => {
      expect(screen.getByText("Save Translation")).toBeInTheDocument()
    })

    const textarea = screen.getByPlaceholderText("Enter your translation here...")
    fireEvent.change(textarea, { target: { value: "My translation" } })

    fireEvent.click(screen.getByText("Save Translation"))

    await waitFor(() => {
      expect(screen.getByText("Translation saved!")).toBeInTheDocument()
    })

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/sections/sec-4/translate"),
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("My translation"),
      }),
    )
  })

  it("shows previous submission panel when user has pending translation", async () => {
    fetchMock
      .mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: () =>
          Promise.resolve({
            id: "sec-5",
            type: "PARAGRAPH",
            originalText: "Orig",
            autoTranslatedText: "Auto",
            pageNumber: 1,
            bookTitle: "Book",
            book: { id: "b1" },
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            translatedText: "Previous translation",
            exactLetterTranslation: "Exact letter",
            isApproved: false,
          }),
      })

    render(React.createElement(TranslatePage))
    fireEvent.click(screen.getByText("Next Section"))

    await waitFor(() => {
      expect(screen.getByText("My previous submission (pending review)")).toBeInTheDocument()
      expect(screen.getByText(/Exact: Exact letter/)).toBeInTheDocument()
    })
  })
})
