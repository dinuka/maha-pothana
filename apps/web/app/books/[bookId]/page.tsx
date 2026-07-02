"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { publicEnv } from "@/lib/env/publicEnv"
import { PageStatus } from "@/lib/types"

interface Page {
  id: string
  pageNumber: number
  originalPageNumber?: string
  status: PageStatus
  thumbnailUrl?: string | null
  sectionCount?: number
  translatedPercent?: number
}

interface BookDetail {
  id: string
  title: string
  author: string
  sourceLanguage: string
  translateLanguages: string[]
  status: string
}

async function fetchWithAuth(path: string) {
  const tokenRes = await fetch("/api/auth/token")
  if (!tokenRes.ok) throw new Error("Not authenticated")
  const { token } = await tokenRes.json()
  const res = await fetch(`${publicEnv.apiUrl}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })
  return res
}

async function getBook(bookId: string): Promise<BookDetail | null> {
  try {
    const res = await fetchWithAuth(`/api/books/${bookId}`)
    if (res.ok) return await res.json()
  } catch {
    /* noop */
  }
  return null
}

async function getPages(bookId: string): Promise<Page[]> {
  try {
    const res = await fetchWithAuth(`/api/books/${bookId}/pages`)
    if (res.ok) return await res.json()
  } catch {
    /* noop */
  }
  return []
}

export default function BookConsolePage({ params }: { params: Promise<{ bookId: string }> }) {
  const [bookId, setBookId] = useState<string | null>(null)
  const [book, setBook] = useState<BookDetail | null>(null)
  const [pages, setPages] = useState<Page[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<"ALL" | PageStatus>("ALL")
  const [sortBy, setSortBy] = useState<"PAGE_NUMBER" | "PROGRESS">("PAGE_NUMBER")

  useEffect(() => {
    params.then(({ bookId }) => setBookId(bookId))
  }, [params])

  useEffect(() => {
    if (!bookId) return

    let cancelled = false
    let pollTimer: ReturnType<typeof setTimeout> | null = null

    const fetchData = async () => {
      const b = await getBook(bookId!)
      if (cancelled) return
      if (b) {
        setBook(b)
        if (b.status === "READY" || b.status === "BUILDING" || b.status === "COMPLETED") {
          const p = await getPages(bookId!)
          if (!cancelled) {
            setPages(p)
            setLoading(false)
            return
          }
        }
      }
      if (!cancelled) {
        setLoading(false)
        pollTimer = setTimeout(fetchData, 3000)
      }
    }

    fetchData()

    return () => {
      cancelled = true
      if (pollTimer) clearTimeout(pollTimer)
    }
  }, [bookId])

  if (!book && loading) {
    return (
      <div style={styles.page}>
        <p>Loading book...</p>
      </div>
    )
  }

  if (!book) {
    return (
      <div style={styles.page}>
        <p>Book not found</p>
        <Link href="/books" style={{ color: "var(--primary)" }}>
          ← Back to books
        </Link>
      </div>
    )
  }

  const badgeStyle = {
    ...styles.badge,
    background: book.status === "READY" ? "var(--success)" : "var(--surface)",
    borderColor: book.status === "READY" ? "var(--success)" : "var(--border)",
    color: book.status === "READY" ? "#fff" : "var(--foreground)",
  }

  const visiblePages = pages
    .filter((page) => statusFilter === "ALL" || page.status === statusFilter)
    .sort((a, b) =>
      sortBy === "PROGRESS"
        ? (b.translatedPercent ?? 0) - (a.translatedPercent ?? 0)
        : a.pageNumber - b.pageNumber,
    )

  return (
    <div style={styles.page}>
      <Link href="/books" style={styles.backLink}>
        ← Back to books
      </Link>
      <div style={styles.header}>
        <h1 style={styles.title}>{book.title}</h1>
        <div style={styles.meta}>
          <span>{book.author}</span>
          <span style={styles.dot}>·</span>
          <span>
            {book.sourceLanguage} → {book.translateLanguages.join(", ")}
          </span>
          <span style={styles.dot}>·</span>
          <span style={badgeStyle}>{book.status}</span>
        </div>
      </div>

      {book.status !== "READY" && book.status !== "BUILDING" && book.status !== "COMPLETED" && (
        <div style={styles.processing}>
          <div className="spinner" style={styles.spinner} />
          <span>Processing book pages... This may take a moment.</span>
        </div>
      )}

      {book.status === "READY" && (
        <div style={styles.controls}>
          <select
            style={styles.filter}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as "ALL" | PageStatus)}
          >
            <option value="ALL">All Pages</option>
            <option value={PageStatus.SECTIONS_CONFIRMED}>Completed</option>
            <option value={PageStatus.PROCESSING}>In Progress</option>
            <option value={PageStatus.PENDING}>Not Started</option>
          </select>
          <select
            style={styles.filter}
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "PAGE_NUMBER" | "PROGRESS")}
          >
            <option value="PAGE_NUMBER">Sort by Page Number</option>
            <option value="PROGRESS">Sort by Progress</option>
          </select>
        </div>
      )}

      <div style={styles.pageGrid}>
        {visiblePages.map((page) => (
          <Link
            key={page.id}
            href={`/books/${bookId}/pages/${page.pageNumber}`}
            style={styles.pageCard}
          >
            <div style={styles.thumbnail}>
              {page.thumbnailUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={page.thumbnailUrl}
                  alt={`Page ${page.originalPageNumber || page.pageNumber}`}
                  style={styles.thumbnailImg}
                />
              ) : (
                <div style={styles.thumbnailPlaceholder} />
              )}
              <span
                style={{
                  ...styles.statusDot,
                  ...(page.status === PageStatus.SECTIONS_CONFIRMED
                    ? styles.statusDotConfirmed
                    : page.status === PageStatus.PROCESSING
                      ? styles.statusDotProcessing
                      : styles.statusDotPending),
                }}
                title={
                  page.status === PageStatus.SECTIONS_CONFIRMED
                    ? "Confirmed"
                    : page.status === PageStatus.PROCESSING
                      ? "Processing"
                      : "Pending"
                }
              />
            </div>
            <div style={styles.pageNum}>{page.originalPageNumber || page.pageNumber}</div>
          </Link>
        ))}
        {book.status === "READY" && visiblePages.length === 0 && (
          <p
            style={{
              color: "var(--muted)",
              gridColumn: "1 / -1",
              textAlign: "center",
              padding: 48,
            }}
          >
            No pages found for this book.
          </p>
        )}
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 48, maxWidth: 960, margin: "0 auto" },
  backLink: { color: "var(--muted)", fontSize: 14, display: "inline-block", marginBottom: 16 },
  header: { marginBottom: 32 },
  title: { fontSize: 28, fontWeight: 700, marginBottom: 8 },
  meta: { display: "flex", alignItems: "center", gap: 8, fontSize: 14, color: "var(--muted)" },
  dot: { color: "var(--border)" },
  badge: {
    padding: "2px 8px",
    borderRadius: 4,
    border: "1px solid var(--border)",
    textTransform: "capitalize",
    fontSize: 12,
  },
  processing: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: 16,
    background: "var(--surface)",
    borderRadius: 8,
    fontSize: 14,
    color: "var(--muted)",
    marginBottom: 24,
  },
  spinner: {
    width: 18,
    height: 18,
    border: "2px solid var(--border)",
    borderTopColor: "var(--primary)",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  controls: { display: "flex", gap: 12, marginBottom: 24 },
  filter: {
    padding: "8px 12px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 13,
    background: "var(--background)",
    color: "var(--foreground)",
  },
  pageGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))",
    gap: 12,
  },
  pageCard: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 8,
    padding: 16,
    border: "1px solid var(--border)",
    borderRadius: 8,
    cursor: "pointer",
    transition: "box-shadow 0.2s",
  },
  pageNum: { fontSize: 18, fontWeight: 600 },
  thumbnail: {
    position: "relative",
    width: "100%",
    aspectRatio: "3 / 4",
    borderRadius: 6,
    overflow: "hidden",
    background: "var(--surface)",
  },
  statusDot: {
    position: "absolute",
    top: 8,
    right: 8,
    width: 16,
    height: 16,
    borderRadius: "50%",
    border: "2.5px solid var(--background)",
    boxShadow: "0 1px 3px rgba(0,0,0,0.35)",
  },
  statusDotConfirmed: {
    background: "var(--success)",
  },
  statusDotProcessing: {
    background: "#f5a623",
  },
  statusDotPending: {
    background: "var(--muted)",
  },
  thumbnailImg: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },
  thumbnailPlaceholder: {
    width: "100%",
    height: "100%",
    background: "var(--surface)",
  },
}
