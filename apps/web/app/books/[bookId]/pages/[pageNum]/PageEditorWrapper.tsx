"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Lock } from "lucide-react"
import { publicEnv } from "@/lib/env/publicEnv"
import { PageStatus } from "@/lib/types"
import PageEditor from "@/components/PageEditor"

interface Section {
  id: string
  type: "HEADER" | "PARAGRAPH" | "FOOTNOTE" | "IMAGE_CAPTION" | "PAGE_NUMBER" | "OTHER"
  x: number
  y: number
  width: number
  height: number
}

interface PageEditorWrapperProps {
  pageId: string
  bookId: string
  pageNum: string
  pageImageUrl?: string
  initialSections?: Section[]
  pageStatus?: PageStatus
}

export default function PageEditorWrapper({
  pageId,
  bookId,
  pageNum,
  pageImageUrl,
  initialSections = [],
  pageStatus,
}: PageEditorWrapperProps) {
  const router = useRouter()
  const [refreshKey, setRefreshKey] = useState(0)
  const [sections, setSections] = useState<Section[]>(initialSections)
  const [isFinalizing, setIsFinalizing] = useState(false)
  const [finalizeError, setFinalizeError] = useState<string | null>(null)
  const pollingActiveRef = useRef(true)

  const canFinalize =
    pageStatus === PageStatus.SECTIONS_CONFIRMED ||
    pageStatus === PageStatus.IN_TRANSLATION ||
    pageStatus === PageStatus.TRANSLATED

  const finalizePage = useCallback(async () => {
    setIsFinalizing(true)
    setFinalizeError(null)
    try {
      const res = await fetch(`${publicEnv.apiUrl}/api/pages/${pageId}/finalize`, {
        method: "POST",
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        setFinalizeError(body?.detail ?? "Failed to finalize page")
        return
      }
      router.refresh()
    } finally {
      setIsFinalizing(false)
    }
  }, [pageId, router])

  const triggerDetection = useCallback(async () => {
    const res = await fetch(`${publicEnv.apiUrl}/api/pages/${pageId}/sections/detect`, {
      method: "POST",
    })
    if (!res.ok) return

    pollingActiveRef.current = true
    for (let attempt = 0; attempt < 30; attempt++) {
      if (!pollingActiveRef.current) return
      await new Promise((r) => setTimeout(r, 1000))
      if (!pollingActiveRef.current) return
      try {
        const pageRes = await fetch(`${publicEnv.apiUrl}/api/books/${bookId}/pages/${pageNum}`)
        if (!pageRes.ok) continue
        const data = await pageRes.json()
        if (data.page.status !== "PROCESSING") {
          setSections(data.sections ?? [])
          setRefreshKey((k) => k + 1)
          router.refresh()
          return
        }
      } catch {
        /* retry */
      }
    }
  }, [pageId, bookId, pageNum, router])

  useEffect(() => {
    return () => {
      pollingActiveRef.current = false
    }
  }, [])

  return (
    <>
      <PageEditor
        key={refreshKey}
        pageImageUrl={pageImageUrl}
        initialSections={refreshKey > 0 ? sections : initialSections}
        startDirty={refreshKey > 0}
        onSave={async (saveSections) => {
          const ordered = saveSections.map((s, i) => ({ ...s, sectionOrder: i }))
          await fetch(`${publicEnv.apiUrl}/api/pages/${pageId}/sections`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(ordered),
          })
          router.refresh()
        }}
        onDetectSections={triggerDetection}
      />
      {(canFinalize || pageStatus === PageStatus.FINALIZED) && (
        <div style={styles.finalizePanel}>
          {pageStatus === PageStatus.FINALIZED ? (
            <span style={styles.finalizedLabel}>
              <Lock size={14} />
              This page has been finalized
            </span>
          ) : (
            <button
              onClick={finalizePage}
              disabled={isFinalizing}
              style={{ ...styles.finalizeBtn, opacity: isFinalizing ? 0.6 : 1 }}
            >
              <Lock size={14} />
              {isFinalizing ? "Finalizing..." : "Finalize page"}
            </button>
          )}
          {finalizeError && <span style={styles.finalizeError}>{finalizeError}</span>}
        </div>
      )}
    </>
  )
}

const styles: Record<string, React.CSSProperties> = {
  finalizePanel: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginTop: 16,
    padding: "10px 14px",
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
  },
  finalizeBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    height: 32,
    padding: "0 14px",
    border: "none",
    borderRadius: 6,
    background: "#c084fc",
    color: "#1a0b26",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
  },
  finalizedLabel: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    color: "#c084fc",
    fontSize: 13,
    fontWeight: 600,
  },
  finalizeError: {
    color: "#f87171",
    fontSize: 13,
  },
}
