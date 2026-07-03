"use client"

import { useState, useRef, useEffect, useLayoutEffect, useCallback } from "react"
import { Stage, Layer, Rect, Text, Transformer, Image as KonvaImage } from "react-konva"

interface Section {
  id: string
  type: "HEADER" | "PARAGRAPH" | "FOOTNOTE" | "IMAGE_CAPTION" | "PAGE_NUMBER" | "OTHER"
  x: number
  y: number
  width: number
  height: number
}

interface PageEditorProps {
  pageImageUrl?: string
  initialSections?: Section[]
  onSave?: (sections: Section[]) => void
}

const SECTION_COLORS: Record<string, string> = {
  HEADER: "#3B82F6",
  PARAGRAPH: "#22C55E",
  FOOTNOTE: "#F97316",
  IMAGE_CAPTION: "#A855F7",
  PAGE_NUMBER: "#6B7280",
  OTHER: "#8B5CF6",
}

const SECTION_TYPES = [
  "HEADER",
  "PARAGRAPH",
  "FOOTNOTE",
  "IMAGE_CAPTION",
  "PAGE_NUMBER",
  "OTHER",
] as const

const MAX_UNDO = 50

export default function PageEditor({
  pageImageUrl,
  initialSections = [],
  onSave,
}: PageEditorProps) {
  const [sections, setSections] = useState<Section[]>(initialSections)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [drawStart, setDrawStart] = useState({ x: 0, y: 0 })
  const [imageSize, setImageSize] = useState({ width: 800, height: 600 })
  const [zoom, setZoom] = useState(1)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)
  const [imageLoading, setImageLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [canUndo, setCanUndo] = useState(false)
  const [canRedo, setCanRedo] = useState(false)
  const undoStackRef = useRef<Section[][]>([])
  const redoStackRef = useRef<Section[][]>([])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const stageRef = useRef<any>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const trRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const imgRef = useRef<HTMLImageElement | null>(null)
  const isDrawingRef = useRef(false)
  const sectionsRef = useRef(sections)

  const saveSnapshot = useCallback(() => {
    undoStackRef.current.push([...sectionsRef.current.map((s) => ({ ...s }))])
    if (undoStackRef.current.length > MAX_UNDO) undoStackRef.current.shift()
    redoStackRef.current = []
    setCanUndo(true)
    setCanRedo(false)
  }, [])

  const loadImage = useCallback(() => {
    if (!pageImageUrl) return
    setImageLoading(true)
    setImageError(false)
    setImageLoaded(false)
    const img = new window.Image()
    img.crossOrigin = "anonymous"
    img.onload = () => {
      const maxW = (containerRef.current?.offsetWidth ?? 800) - 40
      const scale = Math.min(maxW / img.width, 1)
      setImageSize({ width: img.width * scale, height: img.height * scale })
      imgRef.current = img
      setImageLoaded(true)
      setImageLoading(false)
    }
    img.onerror = () => {
      setImageLoading(false)
      setImageError(true)
    }
    img.src = pageImageUrl
  }, [pageImageUrl])

  useLayoutEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadImage()
  }, [loadImage])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSections(initialSections)
    undoStackRef.current = []
    redoStackRef.current = []
    setCanUndo(false)
    setCanRedo(false)
  }, [initialSections])

  useEffect(() => {
    if (trRef.current && selectedId) {
      const node = stageRef.current?.findOne(`#${selectedId}`)
      if (node) {
        trRef.current.nodes([node])
        trRef.current.getLayer()?.batchDraw()
        return
      }
    }
    trRef.current?.nodes([])
    trRef.current?.getLayer()?.batchDraw()
  }, [selectedId])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleDragEnd = useCallback((id: string, e: any) => {
    saveSnapshot()
    setSections((prev) =>
      prev.map((s) =>
        s.id === id ? { ...s, x: e.target.x(), y: e.target.y() } : s,
      ),
    )
  }, [saveSnapshot])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleTransformEnd = useCallback((id: string, e: any) => {
    saveSnapshot()
    const node = e.target
    setSections((prev) =>
      prev.map((s) =>
        s.id === id
          ? {
              ...s,
              x: node.x(),
              y: node.y(),
              width: node.width() * node.scaleX(),
              height: node.height() * node.scaleY(),
            }
          : s,
      ),
    )
  }, [saveSnapshot])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleStageClick = (e: any) => {
    if (e.target === e.target.getStage()) {
      setSelectedId(null)
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleMouseDown = (e: any) => {
    if (!isDrawingRef.current) return
    const pos = e.target.getStage()?.getPointerPosition()
    if (pos) setDrawStart(pos)
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleMouseUp = (e: any) => {
    if (!isDrawingRef.current) return
    const pos = e.target.getStage()?.getPointerPosition()
    if (!pos) return
    const x = Math.min(drawStart.x, pos.x)
    const y = Math.min(drawStart.y, pos.y)
    const w = Math.abs(pos.x - drawStart.x)
    const h = Math.abs(pos.y - drawStart.y)
    if (w > 10 && h > 10) {
      saveSnapshot()
      const newSection: Section = {
        id: `section-${Date.now()}`,
        type: "PARAGRAPH",
        x,
        y,
        width: w,
        height: h,
      }
      setSections((prev) => [...prev, newSection])
    }
    setIsDrawing(false)
  }

  const deleteSelected = () => {
    if (!selectedId) return
    saveSnapshot()
    setSections((prev) => prev.filter((s) => s.id !== selectedId))
    setSelectedId(null)
  }

  const changeType = (id: string, type: Section["type"]) => {
    saveSnapshot()
    setSections((prev) => prev.map((s) => (s.id === id ? { ...s, type } : s)))
  }

  const handleSave = () => {
    if (isSaving || sections.length === 0) return
    setIsSaving(true)
    undoStackRef.current = []
    redoStackRef.current = []
    setCanUndo(false)
    setCanRedo(false)
    const ordered = sections.map((s, i) => ({ ...s, sectionOrder: i }))
    try {
      onSave?.(ordered)
    } finally {
      setIsSaving(false)
    }
  }

  const undo = useCallback(() => {
    const stack = undoStackRef.current
    if (stack.length === 0) return
    const prevState = stack.pop()!
    redoStackRef.current.push(sectionsRef.current.map((s) => ({ ...s })))
    setSections(prevState)
    setCanUndo(stack.length > 0)
    setCanRedo(true)
  }, [])

  const redo = useCallback(() => {
    const stack = redoStackRef.current
    if (stack.length === 0) return
    const nextState = stack.pop()!
    undoStackRef.current.push(sectionsRef.current.map((s) => ({ ...s })))
    setSections(nextState)
    setCanRedo(stack.length > 0)
    setCanUndo(true)
  }, [])

  const toggleDrawMode = () => {
    setIsDrawing((d) => !d)
  }

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return

      if (e.key === "Delete" || e.key === "Backspace") {
        if (selectedId) {
          e.preventDefault()
          deleteSelected()
        }
        return
      }

      if ((e.ctrlKey || e.metaKey) && e.key === "z") {
        e.preventDefault()
        undo()
        return
      }

      if ((e.ctrlKey || e.metaKey) && (e.key === "Z" || e.key === "y")) {
        e.preventDefault()
        redo()
        return
      }

      if (e.key === "Escape") {
        if (isDrawingRef.current) {
          setIsDrawing(false)
        } else {
          setSelectedId(null)
        }
        return
      }

      if (e.key === "d" || e.key === "D") {
        if (!isSaving) {
          e.preventDefault()
          toggleDrawMode()
        }
        return
      }

      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault()
        handleSave()
        return
      }

      if (e.key === "+" || e.key === "=") {
        e.preventDefault()
        setZoom((z) => Math.min(3, z + 0.1))
        return
      }

      if (e.key === "-") {
        e.preventDefault()
        setZoom((z) => Math.max(0.5, z - 0.1))
        return
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selectedId, isSaving, undo, redo],
  )

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])

  useLayoutEffect(() => {
    sectionsRef.current = sections
    isDrawingRef.current = isDrawing
  })

  const stageWidth = imageSize.width * zoom
  const stageHeight = imageSize.height * zoom

  const sortedSections = [...sections].sort((a, b) => {
    if (a.y !== b.y) return a.y - b.y
    return a.x - b.x
  })

  if (!pageImageUrl) {
    return (
      <div style={styles.container}>
        <div style={styles.canvasWrapper}>
          <div style={styles.noImage}>
            <span style={{ fontSize: 48, opacity: 0.4 }}>📄</span>
            <p style={{ fontSize: 16, fontWeight: 600, color: "var(--muted)", margin: "8px 0 4px" }}>
              No page image available
            </p>
            <p style={{ fontSize: 13, color: "var(--muted)" }}>
              Upload a book and process it to see pages here
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (imageLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.toolbar}>
          <div style={styles.toolbarLeft}>
            <button disabled style={styles.toolBtn}>📐 Add Section</button>
            <button disabled style={styles.toolBtn}>🗑 Delete</button>
          </div>
          <div style={styles.toolbarRight}>
            <button disabled style={styles.zoomBtn}>−</button>
            <span style={styles.zoomLabel}>100%</span>
            <button disabled style={styles.zoomBtn}>+</button>
            <button disabled style={{ ...styles.saveBtn, opacity: 0.5 }}>✓ Confirm Sections</button>
          </div>
        </div>
        <div ref={containerRef} style={{ ...styles.canvasWrapper, alignItems: "center", justifyContent: "center", minHeight: 400 }}>
          <div role="status" aria-live="polite" style={{ textAlign: "center" }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>⏳</div>
            <p style={{ color: "var(--muted)", fontSize: 14 }}>Loading page image...</p>
          </div>
        </div>
      </div>
    )
  }

  if (imageError) {
    return (
      <div style={styles.container}>
        <div style={styles.toolbar}>
          <div style={styles.toolbarLeft}>
            <button disabled style={styles.toolBtn}>📐 Add Section</button>
            <button disabled style={styles.toolBtn}>🗑 Delete</button>
          </div>
          <div style={styles.toolbarRight}>
            <button disabled style={styles.zoomBtn}>−</button>
            <span style={styles.zoomLabel}>100%</span>
            <button disabled style={styles.zoomBtn}>+</button>
            <button disabled style={{ ...styles.saveBtn, opacity: 0.5 }}>✓ Confirm Sections</button>
          </div>
        </div>
        <div ref={containerRef} style={{ ...styles.canvasWrapper, alignItems: "center", justifyContent: "center", minHeight: 400 }}>
          <div role="alert" style={{ textAlign: "center" }}>
            <div style={{ fontSize: 48, marginBottom: 12, opacity: 0.5 }}>⚠️</div>
            <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 12 }}>
              Failed to load page image
            </p>
            <button onClick={loadImage} style={{ ...styles.toolBtn, borderColor: "var(--primary)", color: "var(--primary)" }}>
              🔄 Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  const currentImage = imgRef.current // eslint-disable-line react-hooks/refs

  return (
    <div style={styles.container}>
      <div style={styles.toolbar} role="toolbar" aria-label="Section editing tools">
        <div style={styles.toolbarLeft}>
          <button
            onClick={toggleDrawMode}
            disabled={isSaving}
            style={{
              ...styles.toolBtn,
              background: isDrawing ? "var(--primary)" : "var(--surface)",
              color: isDrawing ? "#fff" : "var(--foreground)",
              opacity: isSaving ? 0.5 : 1,
            }}
            aria-pressed={isDrawing}
            title="Add Section (D)"
          >
            {isDrawing ? "✕ Cancel Draw" : "📐 Add Section"}
          </button>
          <button
            onClick={deleteSelected}
            disabled={!selectedId || isSaving}
            style={{
              ...styles.toolBtn,
              opacity: !selectedId || isSaving ? 0.5 : 1,
            }}
            title="Delete (Delete)"
          >
            🗑 Delete
          </button>
          <button
            onClick={undo}
            disabled={!canUndo || isSaving}
            style={{
              ...styles.toolBtn,
              opacity: !canUndo || isSaving ? 0.5 : 1,
            }}
            title="Undo (Ctrl+Z)"
          >
            ↩ Undo
          </button>
          <button
            onClick={redo}
            disabled={!canRedo || isSaving}
            style={{
              ...styles.toolBtn,
              opacity: !canRedo || isSaving ? 0.5 : 1,
            }}
            title="Redo (Ctrl+Shift+Z)"
          >
            ↪ Redo
          </button>
          {selectedId && (
            <select
              value={sections.find((s) => s.id === selectedId)?.type ?? "PARAGRAPH"}
              onChange={(e) => changeType(selectedId, e.target.value as Section["type"])}
              disabled={isSaving}
              style={{
                ...styles.typeSelect,
                opacity: isSaving ? 0.5 : 1,
              }}
            >
              {SECTION_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          )}
        </div>
        <div style={styles.toolbarRight}>
          <button
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}
            disabled={zoom <= 0.5}
            style={{
              ...styles.zoomBtn,
              opacity: zoom <= 0.5 ? 0.5 : 1,
            }}
            title="Zoom Out (-)"
          >
            −
          </button>
          <span style={styles.zoomLabel} aria-live="polite">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(3, z + 0.1))}
            disabled={zoom >= 3}
            style={{
              ...styles.zoomBtn,
              opacity: zoom >= 3 ? 0.5 : 1,
            }}
            title="Zoom In (+)"
          >
            +
          </button>
          <button
            onClick={handleSave}
            disabled={sections.length === 0 || isSaving}
            style={{
              ...styles.saveBtn,
              opacity: sections.length === 0 || isSaving ? 0.7 : 1,
            }}
            title="Confirm Sections (Ctrl+S)"
          >
            {isSaving ? "⏳" : "✓"} Confirm Sections
          </button>
        </div>
      </div>

      <div ref={containerRef} style={{ ...styles.canvasWrapper, position: "relative" }}>
        {pageImageUrl && imageLoaded && (
          <Stage
            ref={stageRef}
            width={stageWidth}
            height={stageHeight}
            scaleX={zoom}
            scaleY={zoom}
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            onClick={handleStageClick}
            style={{ background: "#f0f0f0", borderRadius: 8 }}
            role="application"
            aria-label="Page section editor"
          >
            <Layer>
              <KonvaImage
                image={currentImage!}
                x={0}
                y={0}
                width={imageSize.width}
                height={imageSize.height}
              />
            </Layer>
            <Layer>
              {sortedSections.map((section) => (
                <Rect
                  key={section.id}
                  id={section.id}
                  x={section.x}
                  y={section.y}
                  width={section.width}
                  height={section.height}
                  fill={SECTION_COLORS[section.type] + "40"}
                  stroke={selectedId === section.id ? "#fff" : SECTION_COLORS[section.type]}
                  strokeWidth={selectedId === section.id ? 2 : 1}
                  draggable
                  onClick={() => setSelectedId(section.id)}
                  onTap={() => setSelectedId(section.id)}
                  onDragEnd={(e) => handleDragEnd(section.id, e)}
                  onTransformEnd={(e) => handleTransformEnd(section.id, e)}
                />
              ))}
              <Transformer
                ref={trRef}
                boundBoxFunc={(oldBox, newBox) =>
                  newBox.width < 10 || newBox.height < 10 ? oldBox : newBox
                }
              />
            </Layer>
            <Layer>
              {sortedSections.map((section) => (
                <Text
                  key={`label-${section.id}`}
                  x={section.x + 4}
                  y={section.y + 4}
                  text={section.type}
                  fontSize={11}
                  fill={SECTION_COLORS[section.type]}
                  fontStyle="bold"
                />
              ))}
            </Layer>
          </Stage>
        )}
        {imageLoaded && sections.length === 0 && (
          <div
            style={{
              position: "absolute",
              bottom: 16,
              left: "50%",
              transform: "translateX(-50%)",
              background: "rgba(0,0,0,0.6)",
              color: "#fff",
              padding: "8px 16px",
              borderRadius: 8,
              fontSize: 13,
              pointerEvents: "none",
            }}
          >
            No sections yet. Click &quot;Detect Sections&quot; or draw manually.
          </div>
        )}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  toolbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "8px 12px",
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
  },
  toolbarLeft: {
    display: "flex",
    gap: 8,
    alignItems: "center",
  },
  toolbarRight: {
    display: "flex",
    gap: 8,
    alignItems: "center",
  },
  toolBtn: {
    padding: "6px 12px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 13,
    cursor: "pointer",
    background: "var(--surface)",
  },
  typeSelect: {
    padding: "6px 8px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 13,
    background: "var(--background)",
    color: "var(--foreground)",
  },
  zoomBtn: {
    width: 28,
    height: 28,
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 16,
    cursor: "pointer",
    background: "var(--background)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  zoomLabel: {
    fontSize: 13,
    minWidth: 40,
    textAlign: "center",
  },
  saveBtn: {
    padding: "6px 16px",
    border: "none",
    borderRadius: 6,
    background: "var(--primary)",
    color: "#fff",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
  },
  canvasWrapper: {
    border: "1px solid var(--border)",
    borderRadius: 8,
    overflow: "hidden",
    display: "flex",
    justifyContent: "center",
    padding: 20,
    minHeight: 400,
  },
  noImage: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: 64,
    color: "var(--muted)",
    gap: 8,
  },
}
