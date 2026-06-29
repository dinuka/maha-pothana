import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import React from "react"

const mockPush = vi.fn()
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}))

import UploadBookPage from "@/app/books/new/page"

describe("UploadBookPage", () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it("renders the upload form", () => {
    render(React.createElement(UploadBookPage))
    expect(screen.getByText("Upload New Book")).toBeInTheDocument()
    expect(screen.getByText("Book Title *")).toBeInTheDocument()
    expect(screen.getByText("Author *")).toBeInTheDocument()
    expect(screen.getByText("Source Language *")).toBeInTheDocument()
    expect(screen.getByText("Target Languages * (select one or more)")).toBeInTheDocument()
  })

  it("shows error when submitting empty form", () => {
    render(React.createElement(UploadBookPage))
    fireEvent.click(screen.getByText("Upload Book"))
    expect(screen.getByText("Please fill all required fields")).toBeInTheDocument()
  })

  it("toggles target language chip selection", () => {
    render(React.createElement(UploadBookPage))
    const select = screen.getByRole("combobox", { name: /source language/i })
    fireEvent.change(select, { target: { value: "si" } })
    const chips = screen.getAllByRole("button").filter((b) => b.textContent === "English")
    expect(chips).toHaveLength(1)
    const chip = chips[0]
    fireEvent.click(chip)
    expect(chip).toHaveStyle({ background: "var(--primary)" })
    fireEvent.click(chip)
    expect(chip).toHaveStyle({ background: "var(--surface)" })
  })

  it("renders file drop zone", () => {
    render(React.createElement(UploadBookPage))
    expect(screen.getByText(/Drag & drop a PDF here/)).toBeInTheDocument()
    expect(screen.getByText("Select PDF")).toBeInTheDocument()
  })
})
