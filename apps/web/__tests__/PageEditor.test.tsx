import { describe, it, expect, vi, beforeAll, afterAll } from "vitest"
import React from "react"
import { createRoot, Root } from "react-dom/client"
import { flushSync } from "react-dom"

vi.mock("react-konva", () => ({
  Stage: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", { "data-testid": "stage" }, children),
  Layer: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", { "data-testid": "layer" }, children),
  Rect: ({ id, onClick }: { id: string; onClick?: () => void }) =>
    React.createElement("div", { "data-testid": "rect", "data-id": id, onClick }),
  Text: ({ text }: { text: string }) =>
    React.createElement("span", { "data-testid": "label" }, text),
  Transformer: () => React.createElement("div", { "data-testid": "transformer" }),
  Image: () => React.createElement("div", { "data-testid": "konva-image" }),
}))

import PageEditor from "@/components/PageEditor"

const mockSections = [
  { id: "s1", type: "HEADER" as const, x: 0, y: 0, width: 100, height: 50 },
  { id: "s2", type: "PARAGRAPH" as const, x: 0, y: 60, width: 200, height: 150 },
]

function setupMockImage(onloadFire: "sync" | "never" = "sync") {
  const MockImage = function (this: void) {
    const img: Record<string, unknown> = {
      onload: null,
      onerror: null,
      crossOrigin: "",
      width: 800,
      height: 600,
    }
    Object.defineProperty(img, "src", {
      get() {
        return ""
      },
      set(value: string) {
        if (!value) return
        if (onloadFire === "sync" && typeof img.onload === "function") {
          ;(img.onload as () => void)()
        }
      },
      configurable: true,
    })
    return img
  }
  vi.stubGlobal("Image", MockImage as unknown as typeof globalThis.Image)
}

describe("PageEditor — no image", () => {
  let root: Root
  let container: HTMLDivElement

  beforeAll(() => {
    container = document.createElement("div")
    document.body.appendChild(container)
    root = createRoot(container)
  })

  afterAll(() => {
    root.unmount()
    document.body.removeChild(container)
  })

  it("renders no image message when no url", () => {
    flushSync(() => {
      root.render(React.createElement(PageEditor))
    })
    expect(document.body.textContent).toContain("No page image available")
  })

  it("shows loading state when url provided", () => {
    flushSync(() => {
      root.render(React.createElement(PageEditor, { pageImageUrl: "/test.png" }))
    })
    expect(document.body.textContent).toContain("Loading page image...")
    expect(document.body.textContent).toContain("Add")
    expect(container.querySelector('button[title*="Delete section"]')).not.toBeNull()
    expect(document.body.textContent).toContain("100%")
    expect(document.body.textContent).toContain("Confirm")
  })
})

describe("PageEditor — loaded (mock Image sync onload)", () => {
  let root: Root
  let container: HTMLDivElement

  beforeAll(() => {
    setupMockImage("sync")
    container = document.createElement("div")
    document.body.appendChild(container)
    root = createRoot(container)
  })

  afterAll(() => {
    root.unmount()
    document.body.removeChild(container)
    vi.unstubAllGlobals()
  })

  function renderWithProps(props: Record<string, unknown> = {}) {
    flushSync(() => {
      root.render(
        React.createElement(PageEditor, {
          pageImageUrl: "/test.png",
          initialSections: mockSections,
          ...props,
        }),
      )
    })
  }

  it("renders toolbar and stage", () => {
    renderWithProps()
    expect(container.querySelector('button[title*="Add section"]')).not.toBeNull()
    expect(container.querySelector('button[title*="Delete section"]')).not.toBeNull()
    expect(container.querySelector('button[title*="Undo"]')).not.toBeNull()
    expect(container.querySelector('button[title*="Redo"]')).not.toBeNull()
    expect(document.body.textContent).toContain("100%")
    expect(document.body.textContent).toContain("Confirm")
    expect(document.querySelector('[data-testid="stage"]')).not.toBeNull()
    const rects = document.querySelectorAll('[data-testid="rect"]')
    expect(rects.length).toBe(2)
  })

  it("zoom in increases zoom display", () => {
    renderWithProps({ key: "zoom-in" })
    const zoomInBtn = container.querySelector('button[title*="Zoom In"]') as HTMLButtonElement
    expect(zoomInBtn).not.toBeNull()
    zoomInBtn.click()
    flushSync(() => {})
    expect(document.body.textContent).toContain("110%")
  })

  it("zoom out decreases zoom display", () => {
    renderWithProps({ key: "zoom-out" })
    const zoomOutBtn = container.querySelector('button[title*="Zoom Out"]') as HTMLButtonElement
    expect(zoomOutBtn).not.toBeNull()
    zoomOutBtn.click()
    flushSync(() => {})
    expect(document.body.textContent).toContain("90%")
  })

  it("confirm button is disabled on fresh load with no unsaved changes", () => {
    renderWithProps()
    const confirmBtn = Array.from(container.querySelectorAll("button")).find((b) =>
      b.textContent?.includes("Confirm"),
    ) as HTMLButtonElement
    expect(confirmBtn).not.toBeNull()
    expect(confirmBtn.disabled).toBe(true)
  })

  it("confirm button is enabled when startDirty is set (e.g. after detection)", () => {
    renderWithProps({ key: "start-dirty", startDirty: true })
    const confirmBtn = Array.from(container.querySelectorAll("button")).find((b) =>
      b.textContent?.includes("Confirm"),
    ) as HTMLButtonElement
    expect(confirmBtn).not.toBeNull()
    expect(confirmBtn.disabled).toBe(false)
  })

  it("confirm button enables after modifying a section", () => {
    renderWithProps({ key: "modify-enables" })
    const confirmBtn = Array.from(container.querySelectorAll("button")).find((b) =>
      b.textContent?.includes("Confirm"),
    ) as HTMLButtonElement
    expect(confirmBtn.disabled).toBe(true)
    const rect = document.querySelector('[data-testid="rect"][data-id="s1"]') as HTMLElement
    rect.click()
    flushSync(() => {})
    const deleteBtn = container.querySelector(
      'button[title*="Delete section"]',
    ) as HTMLButtonElement
    deleteBtn.click()
    flushSync(() => {})
    expect(confirmBtn.disabled).toBe(false)
  })

  it("calls onSave with ordered sections on confirm, then disables confirm again", () => {
    const onSave = vi.fn()
    renderWithProps({ key: "on-save", startDirty: true, onSave })
    const confirmBtn = Array.from(container.querySelectorAll("button")).find((b) =>
      b.textContent?.includes("Confirm"),
    ) as HTMLButtonElement
    flushSync(() => {
      confirmBtn.click()
    })
    expect(onSave).toHaveBeenCalledTimes(1)
    const args = onSave.mock.calls[0][0]
    expect(args).toHaveLength(2)
    expect(args[0]).toMatchObject({ id: "s1", sectionOrder: 0 })
    expect(args[1]).toMatchObject({ id: "s2", sectionOrder: 1 })
    expect(confirmBtn.disabled).toBe(true)
  })

  it("delete button is disabled when no selection", () => {
    renderWithProps()
    const deleteBtn = container.querySelector(
      'button[title*="Delete section"]',
    ) as HTMLButtonElement
    expect(deleteBtn).not.toBeNull()
    expect(deleteBtn.disabled).toBe(true)
  })

  it("draw toggle button changes text", () => {
    renderWithProps({ key: "draw" })
    const drawBtn = container.querySelector('button[title*="Add section"]') as HTMLButtonElement
    expect(drawBtn).not.toBeNull()
    expect(drawBtn.textContent).toContain("Add")
    drawBtn.click()
    flushSync(() => {})
    expect(document.body.textContent).toContain("Cancel")
  })

  it("undo button is disabled initially", () => {
    renderWithProps()
    const undoBtn = container.querySelector('button[title*="Undo"]') as HTMLButtonElement
    expect(undoBtn).not.toBeNull()
    expect(undoBtn.disabled).toBe(true)
  })

  it("redo button is disabled initially", () => {
    renderWithProps()
    const redoBtn = container.querySelector('button[title*="Redo"]') as HTMLButtonElement
    expect(redoBtn).not.toBeNull()
    expect(redoBtn.disabled).toBe(true)
  })

  it("confirm shows loading state when unsaved changes exist then clears", () => {
    const onSave = vi.fn().mockImplementation(() => {})
    renderWithProps({ key: "loading-state", startDirty: true, onSave })
    const confirmBtn = Array.from(container.querySelectorAll("button")).find((b) =>
      b.textContent?.includes("Confirm"),
    ) as HTMLButtonElement
    confirmBtn.click()
    expect(onSave).toHaveBeenCalledTimes(1)
    // After save, undo/redo stacks should be cleared
    const undoBtn = container.querySelector('button[title*="Undo"]') as HTMLButtonElement
    expect(undoBtn.disabled).toBe(true)
  })
})

describe("PageEditor — loaded, no sections (mock Image sync onload)", () => {
  let root: Root
  let container: HTMLDivElement

  beforeAll(() => {
    setupMockImage("sync")
    container = document.createElement("div")
    document.body.appendChild(container)
    root = createRoot(container)
  })

  afterAll(() => {
    root.unmount()
    document.body.removeChild(container)
    vi.unstubAllGlobals()
  })

  it("shows no sections message when image loaded with empty sections", () => {
    flushSync(() => {
      root.render(
        React.createElement(PageEditor, {
          pageImageUrl: "/test.png",
          initialSections: [],
        }),
      )
    })
    expect(document.body.textContent).toContain("No sections yet")
    const confirmBtn = Array.from(container.querySelectorAll("button")).find((b) =>
      b.textContent?.includes("Confirm"),
    ) as HTMLButtonElement
    expect(confirmBtn.disabled).toBe(true)
  })
})

describe("PageEditor — error state (mock Image that never fires)", () => {
  let root: Root
  let container: HTMLDivElement

  beforeAll(() => {
    // Image mock that never fires onload → image stays loading → covered by "loading" test above
    // For error state, mock needs to fire onerror
    const MockImage = function (this: void) {
      const img: Record<string, unknown> = {
        onload: null,
        onerror: null,
        crossOrigin: "",
        width: 800,
        height: 600,
      }
      Object.defineProperty(img, "src", {
        get() {
          return ""
        },
        set(value: string) {
          if (!value) return
          if (typeof img.onerror === "function") (img.onerror as () => void)()
        },
        configurable: true,
      })
      return img
    }
    vi.stubGlobal("Image", MockImage as unknown as typeof globalThis.Image)
    container = document.createElement("div")
    document.body.appendChild(container)
    root = createRoot(container)
  })

  afterAll(() => {
    root.unmount()
    document.body.removeChild(container)
    vi.unstubAllGlobals()
  })

  it("shows error state when image load fails", () => {
    flushSync(() => {
      root.render(React.createElement(PageEditor, { pageImageUrl: "/test.png" }))
    })
    expect(document.body.textContent).toContain("Failed to load page image")
    expect(document.body.textContent).toContain("Retry")
  })
})
