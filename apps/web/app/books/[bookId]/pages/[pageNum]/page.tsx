import { apiFetch } from "@/lib/apiClient"
import Link from "next/link"
import {
  Clock,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Languages,
  CheckCheck,
  Lock,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"
import { PageStatus } from "@/lib/types"
import PageEditorWrapper from "./PageEditorWrapper"
import css from "./page.module.css"

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
  status: PageStatus
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

async function getPageCount(bookId: string): Promise<number | null> {
  try {
    const res = await apiFetch(`/api/books/${bookId}/pages?limit=1`, { cache: "no-store" })
    if (res.ok) return (await res.json()).total
  } catch {
    /* noop */
  }
  return null
}

interface StatusMeta {
  label: string
  icon: typeof Clock
  color: string
  background: string
  border: string
  spin?: boolean
}

const STATUS_META: Record<PageStatus, StatusMeta> = {
  [PageStatus.PENDING]: {
    label: "Pending",
    icon: Clock,
    color: "#a1a1aa",
    background: "rgba(161, 161, 170, 0.12)",
    border: "rgba(161, 161, 170, 0.35)",
  },
  [PageStatus.PROCESSING]: {
    label: "Processing",
    icon: Loader2,
    color: "#60a5fa",
    background: "rgba(96, 165, 250, 0.12)",
    border: "rgba(96, 165, 250, 0.35)",
    spin: true,
  },
  [PageStatus.DETECTION_FAILED]: {
    label: "Detection Failed",
    icon: AlertTriangle,
    color: "#f87171",
    background: "rgba(248, 113, 113, 0.12)",
    border: "rgba(248, 113, 113, 0.35)",
  },
  [PageStatus.SECTIONS_CONFIRMED]: {
    label: "Sections Confirmed",
    icon: CheckCircle2,
    color: "#34d399",
    background: "rgba(52, 211, 153, 0.12)",
    border: "rgba(52, 211, 153, 0.35)",
  },
  [PageStatus.IN_TRANSLATION]: {
    label: "In Translation",
    icon: Languages,
    color: "#fbbf24",
    background: "rgba(251, 191, 36, 0.12)",
    border: "rgba(251, 191, 36, 0.35)",
  },
  [PageStatus.TRANSLATED]: {
    label: "Translated",
    icon: CheckCheck,
    color: "#22d3ee",
    background: "rgba(34, 211, 238, 0.12)",
    border: "rgba(34, 211, 238, 0.35)",
  },
  [PageStatus.FINALIZED]: {
    label: "Finalized",
    icon: Lock,
    color: "#c084fc",
    background: "rgba(192, 132, 252, 0.12)",
    border: "rgba(192, 132, 252, 0.35)",
  },
}

const FALLBACK_STATUS_META: StatusMeta = {
  label: "Unknown",
  icon: Clock,
  color: "#a1a1aa",
  background: "rgba(161, 161, 170, 0.12)",
  border: "rgba(161, 161, 170, 0.35)",
}

export default async function PageEditorPage({
  params,
}: {
  params: Promise<{ bookId: string; pageNum: string }>
}) {
  const { bookId, pageNum } = await params
  const [page, pageCount] = await Promise.all([getPage(bookId, pageNum), getPageCount(bookId)])

  const currentPageNum = Number(pageNum)
  const hasPrev = currentPageNum > 1
  const hasNext = pageCount !== null ? currentPageNum < pageCount : false
  const statusMeta = page ? (STATUS_META[page.page.status] ?? FALLBACK_STATUS_META) : null
  const StatusIcon = statusMeta?.icon

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <Link href={`/books/${bookId}`} style={styles.backLink}>
          ← Back to book
        </Link>
        <h1 style={styles.title}>Page {pageNum}</h1>
        {statusMeta && StatusIcon && (
          <span
            style={{
              ...styles.badge,
              color: statusMeta.color,
              background: statusMeta.background,
              borderColor: statusMeta.border,
            }}
          >
            <StatusIcon size={13} className={statusMeta.spin ? css.spinIcon : undefined} />
            {statusMeta.label}
          </span>
        )}
        <div style={styles.pageNav}>
          {hasPrev ? (
            <Link href={`/books/${bookId}/pages/${currentPageNum - 1}`} style={styles.navLink}>
              <ChevronLeft size={16} />
              Previous page
            </Link>
          ) : (
            <span style={styles.navLinkDisabled}>
              <ChevronLeft size={16} />
              Previous page
            </span>
          )}
          {hasNext ? (
            <Link href={`/books/${bookId}/pages/${currentPageNum + 1}`} style={styles.navLink}>
              Next page
              <ChevronRight size={16} />
            </Link>
          ) : (
            <span style={styles.navLinkDisabled}>
              Next page
              <ChevronRight size={16} />
            </span>
          )}
        </div>
      </div>

      <PageEditorWrapper
        pageId={page?.page.id ?? ""}
        bookId={bookId}
        pageNum={pageNum}
        pageImageUrl={page?.page.imageUrl}
        initialSections={page?.sections ?? []}
        pageStatus={page?.page.status}
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
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "3px 10px",
    borderRadius: 999,
    border: "1px solid",
    fontSize: 12,
    fontWeight: 600,
  },
  pageNav: { display: "flex", gap: 16, marginLeft: "auto" },
  navLink: {
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
    color: "var(--foreground)",
    fontSize: 14,
    fontWeight: 500,
  },
  navLinkDisabled: {
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
    color: "var(--muted)",
    fontSize: 14,
    fontWeight: 500,
    opacity: 0.4,
  },
}
