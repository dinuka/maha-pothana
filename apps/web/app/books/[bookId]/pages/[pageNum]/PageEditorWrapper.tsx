"use client"

import { useState, useCallback } from "react"
import { publicEnv } from "@/lib/env/publicEnv"
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
}

export default function PageEditorWrapper({
  pageId,
  bookId,
  pageNum,
  pageImageUrl,
  initialSections = [],
}: PageEditorWrapperProps) {
  const [refreshKey, setRefreshKey] = useState(0)
  const [sections, setSections] = useState<Section[]>(initialSections)

  const triggerDetection = useCallback(async () => {
    const res = await fetch(`${publicEnv.apiUrl}/api/pages/${pageId}/sections/detect`, {
      method: "POST",
    })
    if (!res.ok) return

    for (let attempt = 0; attempt < 30; attempt++) {
      await new Promise((r) => setTimeout(r, 1000))
      try {
        const pageRes = await fetch(`${publicEnv.apiUrl}/api/books/${bookId}/pages/${pageNum}`)
        if (!pageRes.ok) continue
        const data = await pageRes.json()
        if (data.page.status !== "PROCESSING") {
          setSections(data.sections ?? [])
          setRefreshKey((k) => k + 1)
          return
        }
      } catch {
        /* retry */
      }
    }
  }, [pageId, bookId, pageNum])

  return (
    <PageEditor
      key={refreshKey}
      pageImageUrl={pageImageUrl}
      initialSections={refreshKey > 0 ? sections : initialSections}
      onSave={async (saveSections) => {
        const ordered = saveSections.map((s, i) => ({ ...s, sectionOrder: i }))
        await fetch(`${publicEnv.apiUrl}/api/pages/${pageId}/sections`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(ordered),
        })
      }}
      onDetectSections={triggerDetection}
    />
  )
}
