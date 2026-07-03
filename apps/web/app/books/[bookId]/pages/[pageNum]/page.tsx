import { apiFetch } from "@/lib/apiClient"
import Link from "next/link"
import PageEditorWrapper from "./PageEditorWrapper"

interface Section {
  id: string
  type: "HEADER" | "PARAGRAPH" | "FOOTNOTE" | "IMAGE_CAPTION" | "PAGE_NUMBER" | "OTHER"
  x: number
  y: number
  width: number
  height: number
}

interface PageData {
  id: string
  pageNumber: number
  imageKey: string
  imageUrl?: string
  status: string
}

interface PageDetail {
  page: PageData
  sections: Section[]
}

async function getPage(bookId: string, pageNum: string): Promise<PageDetail | null> {
  try {
    const res = await apiFetch(`/api/books/${bookId}/pages/${pageNum}`, { cache: "no-store" })
    if (res.ok) return res.json()
  } catch {
    /* noop */
  }
  return null
}

const STATUS_LABELS: Record<string, string> = {
  PENDING: "Pending",
  PROCESSING: "Processing",
  SECTIONS_CONFIRMED: "Sections Confirmed",
  DETECTION_FAILED: "Detection Failed",
  READY: "Ready",
}

export default async function PageEditorPage({
  params,
}: {
  params: Promise<{ bookId: string; pageNum: string }>
}) {
  const { bookId, pageNum } = await params
  const page = await getPage(bookId, pageNum)

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <Link href={`/books/${bookId}`} style={styles.backLink}>
          ← Back to book
        </Link>
        <h1 style={styles.title}>Page {pageNum}</h1>
        {page && (
          <span style={styles.badge}>{STATUS_LABELS[page.page.status] ?? page.page.status}</span>
        )}
      </div>

      <PageEditorWrapper
        pageId={page?.page.id ?? ""}
        bookId={bookId}
        pageNum={pageNum}
        pageImageUrl={page?.page.imageUrl}
        initialSections={page?.sections ?? []}
      />
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 32, maxWidth: 1200, margin: "0 auto" },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    marginBottom: 24,
  },
  backLink: { color: "var(--muted)", fontSize: 14 },
  title: { fontSize: 24, fontWeight: 700 },
  badge: {
    padding: "2px 8px",
    borderRadius: 4,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    fontSize: 12,
    textTransform: "capitalize",
  },
}
