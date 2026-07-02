"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { Stage, Layer, Rect, Text, Transformer } from "react-konva"

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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const stageRef = useRef<any>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const trRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (pageImageUrl) {
      const img = new window.Image()
      img.onload = () => {
        const maxW = (containerRef.current?.offsetWidth ?? 800) - 40
        const scale = Math.min(maxW / img.width, 1)
        setImageSize({ width: img.width * scale, height: img.height * scale })
      }
      img.src = pageImageUrl
    }
  }, [pageImageUrl])

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
    setSections((prev) =>
      prev.map((s) => (s.id === id ? { ...s, x: e.target.x(), y: e.target.y() } : s)),
    )
  }, [])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleTransformEnd = useCallback((id: string, e: any) => {
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
  }, [])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleStageClick = (e: any) => {
    if (e.target === e.target.getStage()) {
      setSelectedId(null)
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleMouseDown = (e: any) => {
    if (!isDrawing) return
    const pos = e.target.getStage()?.getPointerPosition()
    if (pos) setDrawStart(pos)
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleMouseUp = (e: any) => {
    if (!isDrawing) return
    const pos = e.target.getStage()?.getPointerPosition()
    if (!pos) return
    const x = Math.min(drawStart.x, pos.x)
    const y = Math.min(drawStart.y, pos.y)
    const w = Math.abs(pos.x - drawStart.x)
    const h = Math.abs(pos.y - drawStart.y)
    if (w > 10 && h > 10) {
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
    setSections((prev) => prev.filter((s) => s.id !== selectedId))
    setSelectedId(null)
  }

  const changeType = (id: string, type: Section["type"]) => {
    setSections((prev) => prev.map((s) => (s.id === id ? { ...s, type } : s)))
  }

  const handleSave = () => {
    onSave?.(sections)
  }

  const stageWidth = imageSize.width * zoom
  const stageHeight = imageSize.height * zoom

  return (
    <div style={styles.container}>
      <div style={styles.toolbar}>
        <div style={styles.toolbarLeft}>
          <button
            onClick={() => setIsDrawing(!isDrawing)}
            style={{
              ...styles.toolBtn,
              background: isDrawing ? "var(--primary)" : "var(--surface)",
              color: isDrawing ? "#fff" : "var(--foreground)",
            }}
          >
            {isDrawing ? "Cancel Draw" : "Add Section"}
          </button>
          <button onClick={deleteSelected} disabled={!selectedId} style={styles.toolBtn}>
            Delete
          </button>
          {selectedId && (
            <select
              value={sections.find((s) => s.id === selectedId)?.type ?? "PARAGRAPH"}
              onChange={(e) => changeType(selectedId, e.target.value as Section["type"])}
              style={styles.typeSelect}
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
          <button onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))} style={styles.zoomBtn}>
            -
          </button>
          <span style={styles.zoomLabel}>{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom((z) => Math.min(3, z + 0.1))} style={styles.zoomBtn}>
            +
          </button>
          <button onClick={handleSave} style={styles.saveBtn}>
            Confirm Sections
          </button>
        </div>
      </div>

      <div ref={containerRef} style={styles.canvasWrapper}>
        {pageImageUrl && (
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
          >
            <Layer>
              <Rect
                x={0}
                y={0}
                width={imageSize.width}
                height={imageSize.height}
                fillPatternImage={undefined}
              />
              <Text text="Page image would render here" x={20} y={20} fontSize={14} fill="#999" />
            </Layer>
            <Layer>
              {sections.map((section) => (
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
              {sections.map((section) => (
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
        {!pageImageUrl && (
          <div style={styles.noImage}>
            <p>No page image available</p>
            <p style={{ fontSize: 13, color: "var(--muted)" }}>
              Upload a book and process it to see pages here
            </p>
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
    overflow: "auto",
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
