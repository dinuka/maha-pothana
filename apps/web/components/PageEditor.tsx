"use client"

import { useState, useRef, useEffect, useLayoutEffect, useCallback } from "react"
import { Stage, Layer, Rect, Text, Transformer, Image as KonvaImage } from "react-konva"
import { Plus, Trash2, Undo2, Redo2, ZoomIn, ZoomOut, Check, X, Sparkles } from "lucide-react"

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
  onDetectSections?: () => void
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

const SECTION_LABELS: Record<string, string> = {
  HEADER: "Header",
  PARAGRAPH: "Paragraph",
  FOOTNOTE: "Footnote",
  IMAGE_CAPTION: "Image Caption",
  PAGE_NUMBER: "Page Number",
  OTHER: "Other",
}

const MAX_UNDO = 50

export default function PageEditor({
  pageImageUrl,
  initialSections = [],
  onSave,
  onDetectSections,
}: PageEditorProps) {
  const [sections, setSections] = useState<Section[]>(initialSections)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [drawStart, setDrawStart] = useState({ x: 0, y: 0 })
  const [drawCurrent, setDrawCurrent] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [imageSize, setImageSize] = useState({ width: 800, height: 600 })
  const [zoom, setZoom] = useState(1)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)
  const [imageLoading, setImageLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isDetecting, setIsDetecting] = useState(false)
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
    if (!stageRef.current) return
    if (selectedId) {
      const node = stageRef.current.findOne(`#${selectedId}`)
      if (node) {
        trRef.current.nodes([node])
        trRef.current.getLayer()?.batchDraw()
        return
      }
    }
    trRef.current.nodes([])
    trRef.current.getLayer()?.batchDraw()
  }, [selectedId, sections])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleDragEnd = useCallback(
    (id: string, e: any) => {
      saveSnapshot()
      setSections((prev) =>
        prev.map((s) => (s.id === id ? { ...s, x: e.target.x(), y: e.target.y() } : s)),
      )
    },
    [saveSnapshot],
  )

  const handleTransformEnd = useCallback(
    (id: string) => {
      const node = stageRef.current?.findOne(`#${id}`)
      if (!node) return
      saveSnapshot()
      const newX = node.x()
      const newY = node.y()
      const newWidth = node.width() * node.scaleX()
      const newHeight = node.height() * node.scaleY()
      node.scaleX(1)
      node.scaleY(1)
      setSections((prev) =>
        prev.map((s) =>
          s.id === id ? { ...s, x: newX, y: newY, width: newWidth, height: newHeight } : s,
        ),
      )
    },
    [saveSnapshot],
  )

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleStageClick = (e: any) => {
    if (e.target === e.target.getStage()) {
      setSelectedId(null)
      if (isDrawingRef.current) {
        setIsDrawing(false)
      }
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleMouseDown = (e: any) => {
    if (!isDrawingRef.current) return
    const pos = e.target.getStage()?.getPointerPosition()
    if (!pos) return
    setIsDragging(true)
    setDrawStart(pos)
    setDrawCurrent(pos)
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleMouseMove = (e: any) => {
    if (!isDrawingRef.current || !isDragging) return
    const pos = e.target.getStage()?.getPointerPosition()
    if (pos) setDrawCurrent(pos)
  }

  const handleMouseUp = () => {
    if (!isDrawingRef.current || !isDragging) return
    setIsDragging(false)
    const x = Math.min(drawStart.x, drawCurrent.x)
    const y = Math.min(drawStart.y, drawCurrent.y)
    const w = Math.abs(drawCurrent.x - drawStart.x)
    const h = Math.abs(drawCurrent.y - drawStart.y)
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

  const handleDetect = async () => {
    if (!onDetectSections || isDetecting) return
    setIsDetecting(true)
    try {
      await onDetectSections()
    } finally {
      setIsDetecting(false)
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
    setSelectedId(null)
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

  const drawRect =
    isDrawing && isDragging
      ? {
          x: Math.min(drawStart.x, drawCurrent.x),
          y: Math.min(drawStart.y, drawCurrent.y),
          width: Math.abs(drawCurrent.x - drawStart.x),
          height: Math.abs(drawCurrent.y - drawStart.y),
        }
      : null

  if (!pageImageUrl) {
    return (
      <div style={styles.container}>
        <div style={styles.canvasWrapper}>
          <div style={styles.noImage}>
            <span style={{ fontSize: 48, opacity: 0.4 }}>📄</span>
            <p
              style={{ fontSize: 16, fontWeight: 600, color: "var(--muted)", margin: "8px 0 4px" }}
            >
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
            <button disabled className="pe-icon-btn" style={styles.iconBtn} title="Add section (D)">
              <span style={{ marginLeft: 0 }}>Add</span>
            </button>
            <button
              disabled
              className="pe-icon-btn"
              style={styles.iconBtn}
              title="Delete section (Delete)"
            >
              <Trash2 size={16} />
            </button>
            <div style={styles.separator} />
            <button disabled className="pe-icon-btn" style={styles.iconBtn} title="Undo (Ctrl+Z)">
              <Undo2 size={16} />
            </button>
            <button
              disabled
              className="pe-icon-btn"
              style={styles.iconBtn}
              title="Redo (Ctrl+Shift+Z)"
            >
              <Redo2 size={16} />
            </button>
            <div style={styles.separator} />
            <button
              disabled
              className="pe-icon-btn"
              style={{ ...styles.iconBtn, color: "var(--primary)" }}
              title="Auto-detect sections"
            >
              <Sparkles size={16} />
              <span style={{ marginLeft: 6 }}>Detect</span>
            </button>
          </div>
          <div style={styles.toolbarRight}>
            <button disabled className="pe-icon-btn" style={styles.iconBtn} title="Zoom Out (-)">
              <ZoomOut size={16} />
            </button>
            <span style={styles.zoomLabel}>100%</span>
            <button disabled className="pe-icon-btn" style={styles.iconBtn} title="Zoom In (+)">
              <ZoomIn size={16} />
            </button>
            <button
              disabled
              className="pe-save-btn"
              style={{ ...styles.saveBtn, opacity: 0.6 }}
              title="Confirm sections (Ctrl+S)"
            >
              <Check size={16} />
              <span style={{ marginLeft: 6 }}>Confirm</span>
            </button>
          </div>
        </div>
        <div
          ref={containerRef}
          style={{
            ...styles.canvasWrapper,
            alignItems: "center",
            justifyContent: "center",
            minHeight: 400,
          }}
        >
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
            <button disabled className="pe-icon-btn" style={styles.iconBtn} title="Add section (D)">
              <span style={{ marginLeft: 0 }}>Add</span>
            </button>
            <button
              disabled
              className="pe-icon-btn"
              style={styles.iconBtn}
              title="Delete section (Delete)"
            >
              <Trash2 size={16} />
            </button>
            <div style={styles.separator} />
            <button disabled className="pe-icon-btn" style={styles.iconBtn} title="Undo (Ctrl+Z)">
              <Undo2 size={16} />
            </button>
            <button
              disabled
              className="pe-icon-btn"
              style={styles.iconBtn}
              title="Redo (Ctrl+Shift+Z)"
            >
              <Redo2 size={16} />
            </button>
            <div style={styles.separator} />
            <button
              disabled
              className="pe-icon-btn"
              style={{ ...styles.iconBtn, color: "var(--primary)" }}
              title="Auto-detect sections"
            >
              <Sparkles size={16} />
              <span style={{ marginLeft: 6 }}>Detect</span>
            </button>
          </div>
          <div style={styles.toolbarRight}>
            <button disabled className="pe-icon-btn" style={styles.iconBtn} title="Zoom Out (-)">
              <ZoomOut size={16} />
            </button>
            <span style={styles.zoomLabel}>100%</span>
            <button disabled className="pe-icon-btn" style={styles.iconBtn} title="Zoom In (+)">
              <ZoomIn size={16} />
            </button>
            <button
              disabled
              className="pe-save-btn"
              style={{ ...styles.saveBtn, opacity: 0.6 }}
              title="Confirm sections (Ctrl+S)"
            >
              <Check size={16} />
              <span style={{ marginLeft: 6 }}>Confirm</span>
            </button>
          </div>
        </div>
        <div
          ref={containerRef}
          style={{
            ...styles.canvasWrapper,
            alignItems: "center",
            justifyContent: "center",
            minHeight: 400,
          }}
        >
          <div role="alert" style={{ textAlign: "center" }}>
            <div style={{ fontSize: 48, marginBottom: 12, opacity: 0.5 }}>⚠️</div>
            <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 12 }}>
              Failed to load page image
            </p>
            <button
              onClick={loadImage}
              style={{ ...styles.toolBtn, borderColor: "var(--primary)", color: "var(--primary)" }}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  // eslint-disable-next-line react-hooks/refs
  const currentImage = imgRef.current
  return (
    <div style={styles.container}>
      <style>{`
        .pe-icon-btn:hover:not(:disabled) {
          background: var(--accent) !important;
          box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        .pe-icon-btn:active:not(:disabled) {
          transform: scale(0.96);
        }
        .pe-icon-btn[aria-pressed="true"]:hover:not(:disabled) {
          filter: brightness(1.1) !important;
        }
        .pe-save-btn:hover:not(:disabled) {
          filter: brightness(1.08);
        }
        .pe-save-btn:active:not(:disabled) {
          transform: scale(0.96);
        }
      `}</style>
      <div style={styles.toolbar} role="toolbar" aria-label="Section editing tools">
        <div style={styles.toolbarLeft}>
          <button
            onClick={toggleDrawMode}
            disabled={isSaving}
            className="pe-icon-btn"
            style={{
              ...styles.iconBtn,
              background: isDrawing ? "var(--primary)" : "var(--surface)",
              color: isDrawing ? "#fff" : "var(--foreground)",
              opacity: isSaving ? 0.5 : 1,
            }}
            aria-pressed={isDrawing}
            title={isDrawing ? "Cancel drawing (D)" : "Add section (D)"}
          >
            {isDrawing ? <X size={16} /> : <Plus size={16} />}
            <span style={{ marginLeft: 6 }}>{isDrawing ? "Cancel" : "Add"}</span>
          </button>
          <button
            onClick={deleteSelected}
            disabled={!selectedId || isSaving}
            className="pe-icon-btn"
            style={{
              ...styles.iconBtn,
              opacity: !selectedId || isSaving ? 0.4 : 1,
              cursor: !selectedId || isSaving ? "not-allowed" : "pointer",
            }}
            title="Delete section (Delete)"
          >
            <Trash2 size={16} />
          </button>
          <div style={styles.separator} />
          <button
            onClick={undo}
            disabled={!canUndo || isSaving}
            className="pe-icon-btn"
            style={{
              ...styles.iconBtn,
              opacity: !canUndo || isSaving ? 0.4 : 1,
              cursor: !canUndo || isSaving ? "not-allowed" : "pointer",
            }}
            title="Undo (Ctrl+Z)"
          >
            <Undo2 size={16} />
          </button>
          <button
            onClick={redo}
            disabled={!canRedo || isSaving}
            className="pe-icon-btn"
            style={{
              ...styles.iconBtn,
              opacity: !canRedo || isSaving ? 0.4 : 1,
              cursor: !canRedo || isSaving ? "not-allowed" : "pointer",
            }}
            title="Redo (Ctrl+Shift+Z)"
          >
            <Redo2 size={16} />
          </button>
          <button
            onClick={handleDetect}
            disabled={isDetecting || isSaving}
            className="pe-icon-btn"
            style={{
              ...styles.iconBtn,
              opacity: isDetecting || isSaving ? 0.6 : 1,
              cursor: isDetecting || isSaving ? "not-allowed" : "pointer",
              color: "var(--primary)",
            }}
            title="Auto-detect sections"
          >
            <Sparkles size={16} />
            <span style={{ marginLeft: 6 }}>{isDetecting ? "Detecting..." : "Detect"}</span>
          </button>
          <div style={styles.separator} />
          {selectedId && (
            <select
              value={sections.find((s) => s.id === selectedId)?.type ?? "PARAGRAPH"}
              onChange={(e) => changeType(selectedId, e.target.value as Section["type"])}
              disabled={isSaving}
              style={styles.typeSelect}
            >
              {SECTION_TYPES.map((t) => (
                <option key={t} value={t}>
                  {SECTION_LABELS[t]}
                </option>
              ))}
            </select>
          )}
        </div>
        <div style={styles.toolbarRight}>
          <button
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}
            disabled={zoom <= 0.5}
            className="pe-icon-btn"
            style={{
              ...styles.iconBtn,
              opacity: zoom <= 0.5 ? 0.4 : 1,
              cursor: zoom <= 0.5 ? "not-allowed" : "pointer",
            }}
            title="Zoom Out (-)"
          >
            <ZoomOut size={16} />
          </button>
          <span style={styles.zoomLabel} aria-live="polite">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(3, z + 0.1))}
            disabled={zoom >= 3}
            className="pe-icon-btn"
            style={{
              ...styles.iconBtn,
              opacity: zoom >= 3 ? 0.4 : 1,
              cursor: zoom >= 3 ? "not-allowed" : "pointer",
            }}
            title="Zoom In (+)"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={handleSave}
            disabled={sections.length === 0 || isSaving}
            className="pe-save-btn"
            style={{
              ...styles.saveBtn,
              opacity: sections.length === 0 || isSaving ? 0.6 : 1,
              cursor: sections.length === 0 || isSaving ? "not-allowed" : "pointer",
            }}
            title="Confirm sections (Ctrl+S)"
          >
            <Check size={16} />
            <span style={{ marginLeft: 6 }}>{isSaving ? "Saving..." : "Confirm"}</span>
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
            onMouseMove={handleMouseMove}
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
                  name="section"
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
                  onTransformEnd={() => handleTransformEnd(section.id)}
                />
              ))}
              {drawRect && (
                <Rect
                  x={drawRect.x}
                  y={drawRect.y}
                  width={drawRect.width}
                  height={drawRect.height}
                  fill={"#A855F7" + "30"}
                  stroke="#A855F7"
                  strokeWidth={1}
                  dash={[5, 5]}
                />
              )}
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
                  text={SECTION_LABELS[section.type] ?? section.type}
                  fontSize={11}
                  fill={SECTION_COLORS[section.type]}
                  fontStyle="bold"
                />
              ))}
            </Layer>
          </Stage>
        )}
        {imageLoaded && sections.length === 0 && !isDrawing && (
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
            No sections yet. Click &quot;Add&quot; to draw sections.
          </div>
        )}
        {isDrawing && (
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
            Click and drag on the page to draw a section
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
    position: "sticky",
    top: 56,
    zIndex: 10,
    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
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
  iconBtn: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    height: 32,
    padding: "0 10px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 13,
    cursor: "pointer",
    background: "var(--surface)",
    color: "var(--foreground)",
    fontFamily: "inherit",
    transition: "background 0.15s, box-shadow 0.15s",
  },
  separator: {
    width: 1,
    height: 20,
    background: "var(--border)",
    margin: "0 4px",
  },
  typeSelect: {
    padding: "4px 8px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 13,
    background: "var(--background)",
    color: "var(--foreground)",
    fontFamily: "inherit",
    height: 32,
  },
  zoomLabel: {
    fontSize: 13,
    minWidth: 40,
    textAlign: "center",
    color: "var(--foreground)",
  },
  saveBtn: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    height: 32,
    padding: "0 14px",
    border: "none",
    borderRadius: 6,
    background: "var(--primary)",
    color: "#fff",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
    transition: "opacity 0.15s",
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
