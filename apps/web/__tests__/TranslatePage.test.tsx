import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen } from "@testing-library/react"
import React from "react"
import { Suspense } from "react"

// Mock the hooks module
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}))

// Mock the API module
vi.mock("@/lib/api/translations", () => ({
  getNextSection: vi.fn(),
  getMyTranslation: vi.fn(),
  submitTranslation: vi.fn(),
  getTranslationHistory: vi.fn(),
  getBookStats: vi.fn(),
  getTranslatorStats: vi.fn(),
  getDraft: vi.fn(),
  saveDraft: vi.fn(),
  deleteDraft: vi.fn(),
}))

// Mock the publicEnv
vi.mock("@/lib/env/publicEnv", () => ({
  publicEnv: { apiUrl: "http://localhost:8000" },
}))

// Mock child components
vi.mock("@/app/translate/TranslateTab", () => ({
  TranslateTab: ({ filters }: { filters: unknown }) => (
    <div data-testid="translate-tab">Translate Tab - {JSON.stringify(filters)}</div>
  ),
}))

vi.mock("@/app/translate/HistoryTab", () => ({
  HistoryTab: () => <div data-testid="history-tab">History Tab</div>,
}))

vi.mock("@/app/translate/StatsTab", () => ({
  StatsTab: () => <div data-testid="stats-tab">Stats Tab</div>,
}))

vi.mock("@/app/translate/TranslateFilters", () => ({
  TranslateFilters: ({ onFilterChange }: { onFilterChange: (updates: Record<string, unknown>) => void }) => (
    <div data-testid="translate-filters">
      <button onClick={() => onFilterChange({ language: "si" })}>Set Si</button>
    </div>
  ),
}))

vi.mock("@/hooks/useTranslationFilters", () => ({
  useTranslationFilters: () => ({
    filters: { tab: "translate", bookId: null, language: null, page: null, status: null },
    setFilters: vi.fn(),
    clearFilters: vi.fn(),
  }),
}))

import TranslatePage from "@/app/translate/page"

describe("TranslatePage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("renders the page title", () => {
    render(
      React.createElement(
        Suspense,
        { fallback: <div>Loading...</div> },
        React.createElement(TranslatePage)
      )
    )
    expect(screen.getByRole("heading", { name: "Translate" })).toBeInTheDocument()
  })

  it("renders tab bar with three tabs", () => {
    render(
      React.createElement(
        Suspense,
        { fallback: <div>Loading...</div> },
        React.createElement(TranslatePage)
      )
    )
    expect(screen.getByRole("tab", { name: "Translate" })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: "History" })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: "Stats" })).toBeInTheDocument()
  })

  it("default tab is translate", () => {
    render(
      React.createElement(
        Suspense,
        { fallback: <div>Loading...</div> },
        React.createElement(TranslatePage)
      )
    )
    const translateTab = screen.getByRole("tab", { name: "Translate" })
    expect(translateTab).toHaveAttribute("aria-selected", "true")
  })

  it("renders translate tab content by default", () => {
    render(
      React.createElement(
        Suspense,
        { fallback: <div>Loading...</div> },
        React.createElement(TranslatePage)
      )
    )
    expect(screen.getByTestId("translate-tab")).toBeInTheDocument()
  })
})
