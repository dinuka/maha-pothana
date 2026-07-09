import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import React from "react"
import { SourceTextPanel } from "@/app/translate/components/SourceTextPanel"

vi.mock("@/lib/apiClientBrowser", () => ({
  apiFetchBrowser: vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) }),
}))

describe("SourceTextPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("renders with OCR text when no AI text", () => {
    render(<SourceTextPanel originalText="Original OCR text" aiExtractedText={null} zoom={100} />)
    expect(screen.getByText("Original OCR text")).toBeInTheDocument()
    expect(screen.getByText("OCR")).toBeInTheDocument()
  })

  it("renders with AI extracted text by default", () => {
    render(
      <SourceTextPanel
        originalText="Original OCR text"
        aiExtractedText="AI extracted text"
        confidence={0.95}
        zoom={100}
      />,
    )
    expect(screen.getByText("AI extracted text")).toBeInTheDocument()
    expect(screen.getByText(/AI Extracted 95%/)).toBeInTheDocument()
  })

  it("shows toggle when both texts available", () => {
    render(
      <SourceTextPanel
        originalText="Original OCR text"
        aiExtractedText="AI extracted text"
        zoom={100}
      />,
    )
    expect(screen.getByText("AI Extracted")).toBeInTheDocument()
    expect(screen.getByText("Show OCR")).toBeInTheDocument()
  })

  it("toggles between AI and OCR text", () => {
    render(
      <SourceTextPanel
        originalText="Original OCR text"
        aiExtractedText="AI extracted text"
        zoom={100}
      />,
    )
    fireEvent.click(screen.getByText("Show OCR"))
    expect(screen.getByText("Original OCR text")).toBeInTheDocument()

    fireEvent.click(screen.getByText("AI Extracted"))
    expect(screen.getByText("AI extracted text")).toBeInTheDocument()
  })

  it("shows extraction pending state", () => {
    render(
      <SourceTextPanel
        originalText="Original OCR text"
        aiExtractedText={null}
        extractionStatus="pending"
        zoom={100}
      />,
    )
    expect(screen.getByText("Extracting...")).toBeInTheDocument()
    expect(screen.getByText("AI extraction in progress...")).toBeInTheDocument()
  })

  it("shows extraction failed state", () => {
    render(
      <SourceTextPanel
        originalText="Original OCR text"
        aiExtractedText={null}
        extractionStatus="failed"
        isEditor={true}
        zoom={100}
        onExtract={vi.fn()}
      />,
    )
    expect(screen.getByText("Extraction failed")).toBeInTheDocument()
    expect(screen.getByText("Extraction failed — using OCR text")).toBeInTheDocument()
    expect(screen.getByText("Retry Extraction")).toBeInTheDocument()
  })

  it("shows extract button for editors when no AI text", () => {
    const onExtract = vi.fn()
    render(
      <SourceTextPanel
        originalText="Original OCR text"
        aiExtractedText={null}
        isEditor={true}
        zoom={100}
        onExtract={onExtract}
      />,
    )
    expect(screen.getByText("Extract Text")).toBeInTheDocument()
    fireEvent.click(screen.getByText("Extract Text"))
    expect(onExtract).toHaveBeenCalled()
  })

  it("hides extract button for translators", () => {
    render(
      <SourceTextPanel
        originalText="Original OCR text"
        aiExtractedText={null}
        isEditor={false}
        zoom={100}
      />,
    )
    expect(screen.queryByText("Extract Text")).not.toBeInTheDocument()
  })

  it("shows regenerate button when AI text exists for editor", () => {
    render(
      <SourceTextPanel
        originalText="Original OCR text"
        aiExtractedText="AI extracted text"
        isEditor={true}
        zoom={100}
        onExtract={vi.fn()}
      />,
    )
    expect(screen.getByText("Regenerate")).toBeInTheDocument()
  })

  it("scales font size with zoom", () => {
    render(<SourceTextPanel originalText="Original text" aiExtractedText={null} zoom={150} />)
    const textEl = screen.getByText("Original text")
    expect(textEl.style.fontSize).toBe("21px")
  })

  it("shows fallback when no text available", () => {
    render(<SourceTextPanel originalText={null} aiExtractedText={null} zoom={100} />)
    expect(
      screen.getByText("Original text not available — use the image above"),
    ).toBeInTheDocument()
  })

  it("shows green badge for high confidence", () => {
    render(
      <SourceTextPanel
        originalText="text"
        aiExtractedText="AI text"
        confidence={0.95}
        zoom={100}
      />,
    )
    const badge = screen.getByText(/AI Extracted 95%/)
    expect(badge).toHaveStyle({ background: "#16A34A" })
  })

  it("shows yellow badge for medium confidence", () => {
    render(
      <SourceTextPanel
        originalText="text"
        aiExtractedText="AI text"
        confidence={0.78}
        zoom={100}
      />,
    )
    const badge = screen.getByText(/AI Extracted 78%/)
    expect(badge).toHaveStyle({ background: "#F59E0B" })
  })

  it("shows red badge for low confidence", () => {
    render(
      <SourceTextPanel
        originalText="text"
        aiExtractedText="AI text"
        confidence={0.45}
        zoom={100}
      />,
    )
    const badge = screen.getByText(/AI Extracted 45%/)
    expect(badge).toHaveStyle({ background: "#DC2626" })
  })

  it("shows edit button when text is available", () => {
    render(<SourceTextPanel originalText="Original text" aiExtractedText={null} zoom={100} />)
    expect(screen.getByText("Edit")).toBeInTheDocument()
  })

  it("enters edit mode on edit click", () => {
    render(
      <SourceTextPanel
        originalText="Original text"
        aiExtractedText={null}
        zoom={100}
        sectionId="123"
        onSourceTextUpdate={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByText("Edit"))
    expect(screen.getByLabelText("Source text")).toBeInTheDocument()
    expect(screen.getByText("Cancel")).toBeInTheDocument()
    expect(screen.getByText("Save")).toBeInTheDocument()
  })

  it("cancels edit mode", () => {
    render(
      <SourceTextPanel
        originalText="Original text"
        aiExtractedText={null}
        zoom={100}
        sectionId="123"
        onSourceTextUpdate={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByText("Edit"))
    fireEvent.click(screen.getByText("Cancel"))
    expect(screen.queryByLabelText("Source text")).not.toBeInTheDocument()
  })

  it("shows edit link for editors with bookId and pageNumber", () => {
    render(
      <SourceTextPanel
        originalText="Original text"
        aiExtractedText={null}
        isEditor={true}
        bookId="book-123"
        pageNumber={3}
        zoom={100}
      />,
    )
    expect(screen.getByText("Edit original text →")).toHaveAttribute(
      "href",
      "/books/book-123/pages/3",
    )
  })
})
