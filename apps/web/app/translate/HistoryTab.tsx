"use client"

import { useEffect, useRef, useState } from "react"
import { apiFetchBrowser } from "@/lib/apiClientBrowser"
import type { TranslationHistoryItem } from "@/lib/api/translations"
import { HistoryItem } from "./components/HistoryItem"
import type { TranslationFilters } from "@/hooks/useTranslationFilters"

interface HistoryTabProps {
  filters: TranslationFilters
  onSectionClick?: (sectionId: string) => void
}

export const HistoryTab = ({ filters, onSectionClick }: HistoryTabProps) => {
  const [items, setItems] = useState<TranslationHistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(false)
  const cursorRef = useRef<string | null>(null)
  const observerRef = useRef<HTMLDivElement | null>(null)

  const fetchHistory = async (reset = false) => {
    if (!filters.bookId) return

    const isLoadingMore = !reset && cursorRef.current
    if (isLoadingMore) {
      setLoadingMore(true)
    } else {
      setLoading(true)
    }
    if (reset) {
      setHasMore(false)
    }
    setError(null)

    try {
      const params = new URLSearchParams()
      params.set("bookId", filters.bookId)
      if (filters.language) params.set("language", filters.language)
      if (filters.page) params.set("page", String(filters.page))
      if (filters.status) params.set("status", filters.status)
      if (cursorRef.current && !reset) params.set("cursor", cursorRef.current)
      params.set("limit", "20")

      const res = await apiFetchBrowser(`/api/translations/history?${params.toString()}`)
      if (!res.ok) throw new Error("Failed to fetch history")
      const data = await res.json()

      if (reset) {
        setItems(data.items)
      } else {
        setItems((prev) => [...prev, ...data.items])
      }
      setHasMore(data.hasMore)
      cursorRef.current = data.nextCursor
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading history")
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  // Reset and fetch on filter change
  useEffect(() => {
    cursorRef.current = null
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchHistory(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.bookId, filters.language, filters.page, filters.status])

  // Infinite scroll observer
  useEffect(() => {
    const el = observerRef.current
    if (!el) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && hasMore && !loadingMore) {
          fetchHistory(false)
        }
      },
      { threshold: 0.1 },
    )

    observer.observe(el)
    return () => observer.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasMore, loadingMore])

  if (loading && items.length === 0) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner} />
        <span>Loading history...</span>
      </div>
    )
  }

  if (error && items.length === 0) {
    return (
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>⚠️</div>
        <div style={styles.emptyTitle}>Failed to load history</div>
        <button onClick={() => fetchHistory(true)} style={styles.retryBtn}>
          Retry
        </button>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>📝</div>
        <div style={styles.emptyTitle}>No translations yet</div>
        <div style={styles.emptyDesc}>Start translating to see your submission history here.</div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>Translation History</div>
      <div style={styles.list}>
        {items.map((item) => (
          <HistoryItem key={item.translationId} item={item} onClick={onSectionClick} />
        ))}
        <div ref={observerRef} style={styles.observer} />
        {loadingMore && (
          <div style={styles.loadingMore}>
            <div style={styles.spinnerSmall} />
            <span>Loading more translations...</span>
          </div>
        )}
        {!hasMore && items.length > 0 && <div style={styles.endOfList}>End of history</div>}
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
  header: {
    fontSize: 16,
    fontWeight: 600,
    color: "var(--foreground)",
  },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 64,
    color: "var(--muted)",
  },
  spinner: {
    width: 20,
    height: 20,
    border: "2px solid var(--border)",
    borderTopColor: "var(--primary)",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  spinnerSmall: {
    width: 16,
    height: 16,
    border: "2px solid var(--border)",
    borderTopColor: "var(--primary)",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  emptyState: {
    textAlign: "center",
    padding: 64,
    color: "var(--muted)",
  },
  emptyIcon: {
    fontSize: 32,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 600,
    marginBottom: 8,
    color: "var(--foreground)",
  },
  emptyDesc: {
    fontSize: 14,
    lineHeight: 1.5,
    marginBottom: 16,
  },
  retryBtn: {
    padding: "8px 24px",
    background: "var(--primary)",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  loadingMore: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    padding: 16,
    color: "var(--muted)",
    fontSize: 13,
  },
  endOfList: {
    textAlign: "center",
    padding: 16,
    color: "var(--muted)",
    fontSize: 13,
  },
  observer: {
    height: 1,
  },
}
