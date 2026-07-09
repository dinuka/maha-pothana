import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { act, render, screen, waitFor, fireEvent } from "@testing-library/react"
import React from "react"

import BookConsolePage from "@/app/books/[bookId]/page"

const bookResponse = {
  id: "book-1",
  title: "Test Book",
  author: "Test Author",
  sourceLanguage: "si",
  translateLanguages: ["en"],
  status: "READY",
}

const makePage = (pageNumber: number) => ({
  id: `page-${pageNumber}`,
  pageNumber,
  originalPageNumber: String(pageNumber),
  status: "PENDING",
  thumbnailUrl: null,
})

const pagesResponse = (skip: number, limit: number, total: number) => {
  const items = Array.from({ length: Math.min(limit, Math.max(total - skip, 0)) }, (_, i) =>
    makePage(skip + i + 1),
  )
  return { items, total, skip, limit }
}

const jsonResponse = (body: unknown) => ({
  ok: true,
  status: 200,
  json: () => Promise.resolve(body),
})

const renderPage = () =>
  render(React.createElement(BookConsolePage, { params: Promise.resolve({ bookId: "book-1" }) }))

type IntersectionCallback = (entries: { isIntersecting: boolean }[]) => void

describe("BookConsolePage", () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn((url: string) => {
      if (url.includes("/api/auth/token")) {
        return Promise.resolve(jsonResponse({ token: "tok" }))
      }
      if (url.includes(`${"http://localhost:8000"}/api/books/book-1`) && !url.includes("/pages")) {
        return Promise.resolve(jsonResponse(bookResponse))
      }
      return Promise.resolve(jsonResponse(pagesResponse(0, 35, 40)))
    })
    globalThis.fetch = fetchMock
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("fetches the first batch with limit=35&skip=0 and renders returned pages", async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText("Test Book")).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument()
      expect(screen.getByText("35")).toBeInTheDocument()
    })

    const pagesCall = fetchMock.mock.calls.find(([url]: [string]) => url.includes("/pages?"))
    expect(pagesCall?.[0]).toContain("skip=0")
    expect(pagesCall?.[0]).toContain("limit=35")
  })

  it("resets and re-fetches with skip=0&limit=35 when the status filter changes", async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText("Test Book")).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument()
    })

    fetchMock.mockClear()

    const filterSelect = screen.getAllByRole("combobox")[0]
    fireEvent.change(filterSelect!, { target: { value: "completed" } })

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(([url]: [string]) => url.includes("/pages?"))
      expect(call?.[0]).toContain("status=completed")
      expect(call?.[0]).toContain("skip=0")
      expect(call?.[0]).toContain("limit=35")
    })
  })

  it("re-fetches with the new sort param when the sort select changes", async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText("Test Book")).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument()
    })

    fetchMock.mockClear()

    const sortSelect = screen.getAllByRole("combobox")[1]
    fireEvent.change(sortSelect!, { target: { value: "PROGRESS" } })

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(([url]: [string]) => url.includes("/pages?"))
      expect(call?.[0]).toContain("sort=PROGRESS")
    })
  })

  it("appends the next batch with skip=35&limit=7 when the sentinel intersects", async () => {
    let capturedCallback: IntersectionCallback | undefined
    vi.stubGlobal(
      "IntersectionObserver",
      class {
        constructor(cb: IntersectionCallback) {
          capturedCallback = cb
        }
        observe() {}
        unobserve() {}
        disconnect() {}
      },
    )

    renderPage()

    await waitFor(() => {
      expect(screen.getByText("35")).toBeInTheDocument()
    })

    fetchMock.mockClear()
    fetchMock.mockImplementation((url: string) => {
      if (url.includes("/pages?")) return Promise.resolve(jsonResponse(pagesResponse(35, 7, 40)))
      return Promise.resolve(jsonResponse(bookResponse))
    })

    act(() => {
      capturedCallback?.([{ isIntersecting: true }])
    })

    await waitFor(() => {
      expect(screen.getByText("40")).toBeInTheDocument()
    })

    // original 35 cards must still be present — this batch appends, not replaces
    expect(screen.getByText("1")).toBeInTheDocument()
    expect(screen.getByText("35")).toBeInTheDocument()

    const call = fetchMock.mock.calls.find(([url]: [string]) => url.includes("/pages?"))
    expect(call?.[0]).toContain("skip=35")
    expect(call?.[0]).toContain("limit=7")
  })

  it("only triggers one additional fetch when the sentinel intersects twice in quick succession", async () => {
    let capturedCallback: IntersectionCallback | undefined
    vi.stubGlobal(
      "IntersectionObserver",
      class {
        constructor(cb: IntersectionCallback) {
          capturedCallback = cb
        }
        observe() {}
        unobserve() {}
        disconnect() {}
      },
    )

    renderPage()

    await waitFor(() => {
      expect(screen.getByText("35")).toBeInTheDocument()
    })

    let resolveFetch: (() => void) | undefined
    fetchMock.mockClear()
    fetchMock.mockImplementation((url: string) => {
      if (url.includes("/pages?")) {
        return new Promise((resolve) => {
          resolveFetch = () => resolve(jsonResponse(pagesResponse(35, 7, 40)))
        })
      }
      return Promise.resolve(jsonResponse(bookResponse))
    })

    // fire twice synchronously, before the first fetch resolves
    act(() => {
      capturedCallback?.([{ isIntersecting: true }])
      capturedCallback?.([{ isIntersecting: true }])
    })

    await act(async () => {
      resolveFetch?.()
    })

    await waitFor(() => {
      expect(screen.getByText("40")).toBeInTheDocument()
    })

    const pageFetchCalls = fetchMock.mock.calls.filter(([url]: [string]) => url.includes("/pages?"))
    expect(pageFetchCalls).toHaveLength(1)
  })

  // NOTE: this does not (and cannot) reproduce the real initial-load race, where a
  // real IntersectionObserver could fire in the browser-only paint gap between
  // `setBook` committing and `setPages` committing (pages still [] at that point).
  // Under Testing Library both updates settle inside one act() flush, so that
  // intermediate render never paints and the sentinel-mount gate can't be exercised
  // here. This only asserts the steady-state sequence once an observer is attached
  // post-first-batch: it fires a legitimate skip=35 batch, not a spurious skip=0 one.
  it("fires a legitimate skip=35 batch once observed, after the first batch has loaded", async () => {
    vi.stubGlobal(
      "IntersectionObserver",
      class {
        callback: IntersectionCallback
        constructor(cb: IntersectionCallback) {
          this.callback = cb
        }
        observe() {
          this.callback([{ isIntersecting: true }])
        }
        unobserve() {}
        disconnect() {}
      },
    )

    renderPage()

    await waitFor(() => {
      expect(screen.getByText("35")).toBeInTheDocument()
    })

    const pageFetchCalls = fetchMock.mock.calls.filter(([url]: [string]) => url.includes("/pages?"))
    expect(
      pageFetchCalls.some(([url]: [string]) => url.includes("skip=0") && url.includes("limit=7")),
    ).toBe(false)
    expect(pageFetchCalls[0]?.[0]).toContain("skip=0")
    expect(pageFetchCalls[0]?.[0]).toContain("limit=35")
  })
})
