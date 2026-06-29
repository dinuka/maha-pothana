import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import React from "react"

vi.mock("react-konva", () => ({
  Stage: ({ children }: { children: React.ReactNode }) => React.createElement("div", { "data-testid": "stage" }, children),
  Layer: ({ children }: { children: React.ReactNode }) => React.createElement("div", { "data-testid": "layer" }, children),
  Rect: ({ id, onClick }: { id: string; onClick?: () => void }) =>
    React.createElement("div", { "data-testid": "rect", "data-id": id, onClick }),
  Text: ({ text }: { text: string }) => React.createElement("span", { "data-testid": "label" }, text),
  Transformer: () => React.createElement("div", { "data-testid": "transformer" }),
}))

import PageEditor from "@/components/PageEditor"

describe("PageEditor", () => {
  const mockSections = [
    { id: "s1", type: "HEADER" as const, x: 0, y: 0, width: 100, height: 50 },
    { id: "s2", type: "PARAGRAPH" as const, x: 0, y: 60, width: 200, height: 150 },
  ]

  it("renders no image message when no url provided", () => {
    render(React.createElement(PageEditor))
    expect(screen.getByText("No page image available")).toBeInTheDocument()
  })

  it("renders Add Section button", () => {
    render(React.createElement(PageEditor))
    expect(screen.getByText("Add Section")).toBeInTheDocument()
  })

  it("toggles drawing mode on Add Section click", () => {
    render(React.createElement(PageEditor))
    const btn = screen.getByText("Add Section")
    fireEvent.click(btn)
    expect(screen.getByText("Cancel Draw")).toBeInTheDocument()
    fireEvent.click(btn)
    expect(screen.getByText("Add Section")).toBeInTheDocument()
  })

  it("renders initial sections", () => {
    render(React.createElement(PageEditor, { pageImageUrl: "/test.png", initialSections: mockSections }))
    const rects = screen.getAllByTestId("rect")
    // 1 background rect + 2 section rects
    expect(rects).toHaveLength(3)
  })

  it("deletes selected section", () => {
    render(React.createElement(PageEditor, { pageImageUrl: "/test.png", initialSections: mockSections }))
    const deleteBtn = screen.getByText("Delete")
    expect(deleteBtn).toBeDisabled()
    const allRects = screen.getAllByTestId("rect")
    // index 0 is background rect (no onClick), index 1 is first section
    fireEvent.click(allRects[1])
    expect(deleteBtn).not.toBeDisabled()
    fireEvent.click(deleteBtn)
    const rects = screen.getAllByTestId("rect")
    // 1 background rect + 1 remaining section rect
    expect(rects).toHaveLength(2)
  })

  it("calls onSave when confirm button clicked", () => {
    const onSave = vi.fn()
    render(React.createElement(PageEditor, { initialSections: mockSections, onSave }))
    fireEvent.click(screen.getByText("Confirm Sections"))
    expect(onSave).toHaveBeenCalledWith(mockSections)
  })

  it("renders zoom controls", () => {
    render(React.createElement(PageEditor))
    expect(screen.getByText("100%")).toBeInTheDocument()
  })
})
