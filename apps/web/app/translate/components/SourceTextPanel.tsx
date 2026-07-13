"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import Link from "next/link"
import { apiFetchBrowser } from "@/lib/apiClientBrowser"

interface SourceTextPanelProps {
  originalText: string | null
  aiExtractedText: string | null
  extractionStatus?: "extracted" | "pending" | "failed" | null
  confidence?: number | null
  isEditor?: boolean
  zoom: number
  onZoomIn?: () => void
  onZoomOut?: () => void
  onZoomReset?: () => void
  onExtract?: (force?: boolean) => void
  sectionId?: string
  onSourceTextUpdate?: (text: string, source: "ai" | "ocr") => void
  aiError?: string | null
  reverseTransliterating?: boolean
  bookId?: string
  pageNumber?: number
}

const CONFIDENCE_GREEN = "#16A34A"
const CONFIDENCE_YELLOW = "#F59E0B"
const CONFIDENCE_RED = "#DC2626"
const CONFIDENCE_GRAY = "#94A3B8"

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.9) return CONFIDENCE_GREEN
  if (confidence >= 0.7) return CONFIDENCE_YELLOW
  return CONFIDENCE_RED
}

export const SourceTextPanel = ({
  originalText,
  aiExtractedText,
  extractionStatus,
  confidence,
  isEditor = false,
  zoom,
  onZoomIn,
  onZoomOut,
  onZoomReset,
  onExtract,
  sectionId,
  onSourceTextUpdate,
  aiError,
  reverseTransliterating = false,
  bookId,
  pageNumber,
}: SourceTextPanelProps) => {
  const [showAI, setShowAI] = useState(true)
  const [editing, setEditing] = useState(false)
  const [editText, setEditText] = useState("")
  const [saving, setSaving] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const dragStart = useRef({ x: 0, y: 0, scrollLeft: 0, scrollTop: 0 })

  const displayText = showAI && aiExtractedText ? aiExtractedText : originalText
  const fontSize = 22 * (zoom / 100)

  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [editing, editText])

  const handleEditStart = useCallback(() => {
    setEditText(displayText || "")
    setEditing(true)
  }, [displayText])

  const handleEditCancel = useCallback(() => {
    setEditing(false)
    setEditText("")
  }, [])

  const handleSaveEdit = useCallback(async () => {
    if (!sectionId || !onSourceTextUpdate) return
    setSaving(true)
    try {
      const source = showAI && aiExtractedText ? "ai" : "ocr"
      await apiFetchBrowser(`/api/sections/${sectionId}/source-text`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: editText, source }),
      })
      onSourceTextUpdate(editText, source)
      setEditing(false)
    } catch {
      /* noop */
    } finally {
      setSaving(false)
    }
  }, [sectionId, editText, showAI, aiExtractedText, onSourceTextUpdate])

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (editing || e.button !== 0) return
      const el = scrollRef.current
      if (!el) return
      setIsDragging(true)
      dragStart.current = {
        x: e.clientX,
        y: e.clientY,
        scrollLeft: el.scrollLeft,
        scrollTop: el.scrollTop,
      }
      e.preventDefault()
    },
    [editing],
  )

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging) return
      const el = scrollRef.current
      if (!el) return
      const dx = e.clientX - dragStart.current.x
      const dy = e.clientY - dragStart.current.y
      el.scrollLeft = dragStart.current.scrollLeft - dx
      el.scrollTop = dragStart.current.scrollTop - dy
    },
    [isDragging],
  )

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  useEffect(() => {
    if (isDragging) {
      const handleGlobalUp = () => setIsDragging(false)
      window.addEventListener("mouseup", handleGlobalUp)
      return () => window.removeEventListener("mouseup", handleGlobalUp)
    }
  }, [isDragging])

  const getStatusBadge = () => {
    if (extractionStatus === "pending") {
      return <span style={{ ...styles.badge, ...styles.badgePending }}>Extracting...</span>
    }
    if (extractionStatus === "failed") {
      return <span style={{ ...styles.badge, ...styles.badgeFailed }}>Extraction failed</span>
    }
    if (showAI && aiExtractedText && confidence != null) {
      return (
        <span
          style={{
            ...styles.badge,
            background: getConfidenceColor(confidence),
            color: "#fff",
          }}
        >
          AI Extracted {Math.round(confidence * 100)}%
        </span>
      )
    }
    return <span style={{ ...styles.badge, background: CONFIDENCE_GRAY, color: "#fff" }}>OCR</span>
  }

  return (
    <div style={styles.container} role="region" aria-label="Source text panel">
      <div style={styles.header}>
        <span style={styles.icon}>📄</span>
        <span style={styles.title}>Source Text</span>
        {getStatusBadge()}
        {reverseTransliterating && (
          <span style={{ ...styles.badge, ...styles.badgePending }}>
            Reverse transliterating...
          </span>
        )}
      </div>

      {aiExtractedText && originalText && (
        <div style={styles.toggleRow}>
          <button
            onClick={() => setShowAI(true)}
            style={{
              ...styles.toggleBtn,
              ...(showAI ? styles.toggleBtnActive : {}),
            }}
          >
            AI Extracted
          </button>
          <button
            onClick={() => setShowAI(false)}
            style={{
              ...styles.toggleBtn,
              ...(!showAI ? styles.toggleBtnActive : {}),
            }}
          >
            Show OCR
          </button>
        </div>
      )}

      {onZoomIn && onZoomOut && onZoomReset && displayText && !editing && (
        <div style={styles.zoomControls}>
          <button onClick={onZoomOut} style={styles.zoomBtn} aria-label="Zoom out">
            −
          </button>
          <span style={{ fontSize: 13, color: "var(--foreground)" }}>{zoom}%</span>
          <button onClick={onZoomIn} style={styles.zoomBtn} aria-label="Zoom in">
            +
          </button>
          <button onClick={onZoomReset} style={styles.zoomBtn} aria-label="Reset zoom">
            ⟳
          </button>
        </div>
      )}

      {editing ? (
        <div style={styles.editContainer}>
          <textarea
            ref={textareaRef}
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            style={{
              ...styles.textArea,
              fontSize,
            }}
            aria-label="Source text"
          />
          <div style={styles.editActions}>
            <button onClick={handleEditCancel} style={styles.cancelBtn}>
              Cancel
            </button>
            <button onClick={handleSaveEdit} disabled={saving} style={styles.saveBtn}>
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      ) : displayText ? (
        <div
          ref={scrollRef}
          style={{
            ...styles.textScroll,
            cursor: isDragging ? "grabbing" : "grab",
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          <div
            style={{
              ...styles.textDisplay,
              fontSize,
              lineHeight: `${fontSize * 1.6}px`,
            }}
          >
            {displayText}
          </div>
        </div>
      ) : (
        <div style={styles.fallback}>Original text not available — use the image above</div>
      )}

      <div style={styles.actions}>
        {aiError && (
          <div style={styles.aiErrorBox}>
            <span style={styles.aiErrorIcon}>⚠</span>
            <span>{aiError}</span>
          </div>
        )}
        {extractionStatus === "pending" && (
          <div style={styles.extractingIndicator}>
            <div style={styles.miniSpinner} />
            <span>AI extraction in progress...</span>
          </div>
        )}
        {reverseTransliterating && (
          <div style={styles.extractingIndicator}>
            <div style={styles.miniSpinner} />
            <span>Reverse transliterating, please wait...</span>
          </div>
        )}
        {extractionStatus === "failed" && isEditor && (
          <div style={styles.failedIndicator}>
            <span>Extraction failed — using OCR text</span>
            {onExtract && (
              <button onClick={() => onExtract()} style={styles.retryBtn}>
                Retry Extraction
              </button>
            )}
          </div>
        )}
        {!aiExtractedText && !extractionStatus && isEditor && onExtract && (
          <button onClick={() => onExtract()} style={styles.extractBtn}>
            Extract Text
          </button>
        )}
        {aiExtractedText && isEditor && onExtract && (
          <button onClick={() => onExtract(true)} style={styles.regenerateBtn}>
            Regenerate
          </button>
        )}
        {displayText && !editing && (
          <button
            onClick={handleEditStart}
            disabled={reverseTransliterating}
            style={{
              ...styles.editBtn,
              ...(reverseTransliterating ? styles.editBtnDisabled : {}),
            }}
          >
            Edit
          </button>
        )}
        {isEditor && bookId && pageNumber != null && (
          <Link href={`/books/${bookId}/pages/${pageNumber}`} style={styles.pageLink}>
            Edit original text →
          </Link>
        )}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    padding: 12,
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 13,
    fontWeight: 600,
    color: "var(--muted)",
  },
  icon: {
    fontSize: 14,
  },
  title: {
    fontSize: 13,
    fontWeight: 600,
  },
  badge: {
    marginLeft: 8,
    padding: "2px 8px",
    borderRadius: 12,
    fontSize: 11,
    fontWeight: 600,
  },
  badgePending: {
    background: "#3B82F6",
    color: "#fff",
    animation: "pulse 1.5s ease-in-out infinite",
  },
  badgeFailed: {
    background: CONFIDENCE_RED,
    color: "#fff",
  },
  toggleRow: {
    display: "flex",
    gap: 4,
  },
  toggleBtn: {
    padding: "4px 10px",
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--muted)",
    cursor: "pointer",
    fontSize: 12,
  },
  toggleBtnActive: {
    background: "var(--primary)",
    color: "#fff",
    borderColor: "var(--primary)",
  },
  textScroll: {
    border: "1px solid var(--border)",
    borderRadius: 8,
    overflow: "hidden",
    maxHeight: 400,
    background: "var(--background)",
    userSelect: "none",
    touchAction: "none",
  },
  textDisplay: {
    padding: 12,
    color: "var(--foreground)",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  fallback: {
    padding: 12,
    border: "1px dashed var(--border)",
    borderRadius: 8,
    fontSize: 14,
    color: "var(--muted)",
    fontStyle: "italic",
  },
  zoomControls: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 8,
    border: "1px solid var(--border)",
    borderRadius: 8,
  },
  zoomBtn: {
    width: 28,
    height: 28,
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 16,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  editContainer: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  textArea: {
    padding: 12,
    border: "1px solid var(--primary)",
    borderRadius: 8,
    background: "var(--background)",
    color: "var(--foreground)",
    fontFamily: "inherit",
    lineHeight: 1.6,
    resize: "none",
    overflow: "hidden",
  },
  editActions: {
    display: "flex",
    gap: 8,
    justifyContent: "flex-end",
  },
  cancelBtn: {
    padding: "4px 12px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 12,
  },
  saveBtn: {
    padding: "4px 12px",
    border: "none",
    borderRadius: 6,
    background: "var(--primary)",
    color: "#fff",
    cursor: "pointer",
    fontSize: 12,
    fontWeight: 600,
  },
  actions: {
    display: "flex",
    gap: 8,
    flexWrap: "wrap",
  },
  extractBtn: {
    padding: "6px 14px",
    border: "none",
    borderRadius: 6,
    background: "var(--primary)",
    color: "#fff",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 600,
  },
  regenerateBtn: {
    padding: "6px 14px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 13,
  },
  editBtn: {
    padding: "6px 14px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 13,
  },
  editBtnDisabled: {
    opacity: 0.6,
    cursor: "not-allowed",
  },
  pageLink: {
    fontSize: 13,
    color: "var(--primary)",
    textDecoration: "underline",
    cursor: "pointer",
    marginLeft: "auto",
  },
  retryBtn: {
    padding: "4px 12px",
    border: "none",
    borderRadius: 6,
    background: CONFIDENCE_RED,
    color: "#fff",
    cursor: "pointer",
    fontSize: 12,
    fontWeight: 600,
  },
  extractingIndicator: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 13,
    color: "#3B82F6",
  },
  miniSpinner: {
    width: 14,
    height: 14,
    border: "2px solid #3B82F633",
    borderTopColor: "#3B82F6",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  failedIndicator: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 13,
    color: CONFIDENCE_RED,
  },
  aiErrorBox: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "8px 12px",
    border: "1px solid #F59E0B",
    borderRadius: 6,
    background: "#FFFBEB",
    color: "#92400E",
    fontSize: 13,
    lineHeight: 1.4,
  },
  aiErrorIcon: {
    fontSize: 16,
    flexShrink: 0,
  },
}
