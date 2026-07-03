"use client"

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
  pageImageUrl?: string
  initialSections?: Section[]
}

export default function PageEditorWrapper({
  pageId,
  pageImageUrl,
  initialSections = [],
}: PageEditorWrapperProps) {
  return (
    <PageEditor
      pageImageUrl={pageImageUrl}
      initialSections={initialSections}
      onSave={async (sections) => {
        const ordered = sections.map((s, i) => ({ ...s, sectionOrder: i }))
        await fetch(`${publicEnv.apiUrl}/api/pages/${pageId}/sections`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(ordered),
        })
      }}
    />
  )
}
