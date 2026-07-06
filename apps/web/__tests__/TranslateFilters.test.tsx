import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import React from "react"

import { TranslateFilters } from "@/app/translate/TranslateFilters"

const mockFilters = {
  tab: "translate",
  bookId: null,
  language: null,
  page: null,
  status: null,
}

describe("TranslateFilters", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("renders filter controls", () => {
    render(
      React.createElement(TranslateFilters, {
        filters: mockFilters,
        onFilterChange: vi.fn(),
        onClearFilters: vi.fn(),
        translateLanguages: ["si", "ta"],
      })
    )

    expect(screen.getByLabelText("Language")).toBeInTheDocument()
    expect(screen.getByLabelText("Page")).toBeInTheDocument()
    expect(screen.getByLabelText("Status")).toBeInTheDocument()
  })

  it("hides language filter for single language", () => {
    render(
      React.createElement(TranslateFilters, {
        filters: mockFilters,
        onFilterChange: vi.fn(),
        onClearFilters: vi.fn(),
        translateLanguages: ["si"],
      })
    )

    expect(screen.queryByLabelText("Language")).not.toBeInTheDocument()
  })

  it("shows clear button when filters are active", () => {
    render(
      React.createElement(TranslateFilters, {
        filters: { ...mockFilters, language: "si" },
        onFilterChange: vi.fn(),
        onClearFilters: vi.fn(),
        translateLanguages: ["si", "ta"],
      })
    )

    expect(screen.getByText("Clear")).toBeInTheDocument()
  })

  it("hides clear button when no filters active", () => {
    render(
      React.createElement(TranslateFilters, {
        filters: mockFilters,
        onFilterChange: vi.fn(),
        onClearFilters: vi.fn(),
        translateLanguages: ["si", "ta"],
      })
    )

    expect(screen.queryByText("Clear")).not.toBeInTheDocument()
  })

  it("calls onFilterChange when language changes", () => {
    const onChange = vi.fn()
    render(
      React.createElement(TranslateFilters, {
        filters: mockFilters,
        onFilterChange: onChange,
        onClearFilters: vi.fn(),
        translateLanguages: ["si", "ta"],
      })
    )

    fireEvent.change(screen.getByLabelText("Language"), { target: { value: "si" } })
    expect(onChange).toHaveBeenCalledWith({ language: "si" })
  })

  it("calls onClearFilters when clear button clicked", () => {
    const onClear = vi.fn()
    render(
      React.createElement(TranslateFilters, {
        filters: { ...mockFilters, language: "si" },
        onFilterChange: vi.fn(),
        onClearFilters: onClear,
        translateLanguages: ["si", "ta"],
      })
    )

    fireEvent.click(screen.getByText("Clear"))
    expect(onClear).toHaveBeenCalled()
  })
})
