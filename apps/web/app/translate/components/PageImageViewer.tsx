"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { getPageImage } from "@/lib/api/pages"

interface PageImageViewerProps {
  bookId: string
  pageNumber: number
}

export const PageImageViewer = ({ bookId, pageNumber }: PageImageViewerProps) => {
  const [open, setOpen] = useState(false)
  const [viewedPage, setViewedPage] = useState(pageNumber)
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [totalPages, setTotalPages] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const [zoom, setZoom] = useState(100)
  const [isDragging, setIsDragging] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const dragStart = useRef({ x: 0, y: 0, scrollLeft: 0, scrollTop: 0 })

  const loadPage = useCallback(
    async (targetPage: number) => {
      setLoading(true)
      setError(false)
      try {
        const data = await getPageImage(bookId, targetPage)
        setViewedPage(data.pageNumber)
        setImageUrl(data.imageUrl)
        setTotalPages(data.totalPages)
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    },
    [bookId],
  )

  const handleOpen = () => {
    setOpen(true)
    loadPage(pageNumber)
  }

  const handleClose = () => {
    setOpen(false)
    setImageUrl(null)
    setError(false)
    setZoom(100)
  }

  const handleZoomIn = () => setZoom((z) => Math.min(z + 10, 300))
  const handleZoomOut = () => setZoom((z) => Math.max(z - 10, 50))
  const handleZoomReset = () => setZoom(100)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return
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
  }, [])

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

  if (!open) {
    return (
      <button onClick={handleOpen} style={styles.viewFullPageBtn} aria-label="View full page">
        <span aria-hidden="true">🖼️</span> View full page
      </button>
    )
  }

  const hasPrev = viewedPage > 1
  const hasNext = totalPages != null && viewedPage < totalPages

  return (
    <div style={styles.container} role="region" aria-label="Full page viewer">
      <div style={styles.toolbar}>
        {hasPrev && (
          <button
            onClick={() => loadPage(viewedPage - 1)}
            disabled={loading}
            style={styles.navBtn}
            aria-label="Previous page"
            title="Previous page"
          >
            ⬅
          </button>
        )}
        <span style={styles.pageLabel}>
          Page {viewedPage}
          {totalPages != null ? ` / ${totalPages}` : ""}
        </span>
        {hasNext && (
          <button
            onClick={() => loadPage(viewedPage + 1)}
            disabled={loading}
            style={styles.navBtn}
            aria-label="Next page"
            title="Next page"
          >
            ➡
          </button>
        )}
        <button
          onClick={handleClose}
          style={styles.closeBtn}
          aria-label="Close full page view"
          title="Close"
        >
          ✕
        </button>
      </div>

      {loading ? (
        <div style={styles.loadingBox}>
          <div style={styles.spinner} />
          <span>Loading page...</span>
        </div>
      ) : error ? (
        <div style={styles.errorBox}>Failed to load page image</div>
      ) : imageUrl ? (
        <>
          <div
            ref={scrollRef}
            style={{
              ...styles.imageScroll,
              cursor: isDragging ? "grabbing" : "grab",
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            <div style={styles.imageInner}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imageUrl}
                alt={`Page ${viewedPage}`}
                draggable={false}
                style={{
                  width: `${zoom}%`,
                  height: "auto",
                  display: "block",
                  pointerEvents: "none",
                }}
              />
            </div>
          </div>
          <div style={styles.zoomControls}>
            <button onClick={handleZoomOut} style={styles.zoomBtn} aria-label="Zoom out full page">
              −
            </button>
            <span style={{ fontSize: 13, color: "var(--foreground)" }}>{zoom}%</span>
            <button onClick={handleZoomIn} style={styles.zoomBtn} aria-label="Zoom in full page">
              +
            </button>
            <button
              onClick={handleZoomReset}
              style={styles.zoomBtn}
              aria-label="Reset full page zoom"
            >
              ⟳
            </button>
          </div>
        </>
      ) : (
        <div style={styles.errorBox}>Page image not available</div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  viewFullPageBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "6px 14px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 13,
  },
  container: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
    padding: 8,
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
  },
  navBtn: {
    width: 28,
    height: 28,
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 14,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  closeBtn: {
    marginLeft: "auto",
    width: 28,
    height: 28,
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 13,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  pageLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--foreground)",
  },
  loadingBox: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    padding: 48,
    color: "var(--muted)",
    fontSize: 13,
  },
  errorBox: {
    padding: 24,
    textAlign: "center",
    color: "var(--muted)",
    fontSize: 13,
  },
  spinner: {
    width: 16,
    height: 16,
    border: "2px solid var(--border)",
    borderTopColor: "var(--primary)",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  imageScroll: {
    overflow: "hidden",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    userSelect: "none",
    touchAction: "none",
  },
  imageInner: {
    padding: 8,
    minWidth: 0,
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
}
