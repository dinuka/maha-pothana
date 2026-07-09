"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { useSession } from "next-auth/react"
import type { Role } from "@/lib/auth"
import type { BookDetail } from "@/lib/api/books"
import { getBook } from "@/lib/api/books"
import type { TranslationFilters } from "@/hooks/useTranslationFilters"
import { TranslateTab } from "../TranslateTab"
import { HistoryTab } from "../HistoryTab"
import { BookProgressHeader } from "../components/BookProgressHeader"

const TABS = ["translate", "history"] as const
type Tab = (typeof TABS)[number]

const languageLabel = (lang: string): string =>
  lang === "si" ? "Sinhala" : lang === "sa" ? "Sanskrit" : lang === "ta" ? "Tamil" : lang

const BookWorkspacePage = () => {
  const { bookId } = useParams<{ bookId: string }>()
  const router = useRouter()
  const searchParams = useSearchParams()
  const { data: session } = useSession()
  const [book, setBook] = useState<BookDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>("translate")
  const [language, setLanguage] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [statsRefreshSignal, setStatsRefreshSignal] = useState(0)

  useEffect(() => {
    getBook(bookId)
      .then((data) => setBook(data))
      .catch(() => setError("Failed to load book"))
      .finally(() => setLoading(false))
  }, [bookId])

  useEffect(() => {
    if (searchParams.has("section")) {
      router.replace(`/translate/${bookId}`, { scroll: false })
    }
  }, [bookId, router, searchParams])

  const roles = ((session?.user as unknown as { roles: Role[] })?.roles ?? []) as Role[]
  const isEditor = roles.includes("EDITOR")

  const translateFilters: TranslationFilters = {
    tab: "",
    bookId,
    language,
    page: null,
    status,
    sectionId: searchParams.get("section") ?? undefined,
  }

  const historyFilters: TranslationFilters = {
    tab: "",
    bookId,
    language: null,
    page: null,
    status: null,
  }

  if (loading) {
    return (
      <div style={styles.page}>
        <div style={styles.loading}>
          <div style={styles.spinner} />
          <span>Loading book...</span>
        </div>
      </div>
    )
  }

  if (error || !book) {
    return (
      <div style={styles.page}>
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>⚠️</div>
          <div style={styles.emptyTitle}>{error ?? "Book not found"}</div>
          <Link href="/translate" style={styles.backLink}>
            ← Back to books
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.page}>
      <Link href="/translate" style={styles.backLink}>
        ← Back to books
      </Link>
      <h1 style={styles.title}>{book.title}</h1>
      <p style={styles.subtitle}>{book.author}</p>

      <BookProgressHeader bookId={bookId} refreshSignal={statsRefreshSignal} />

      <div style={styles.tabBar} role="tablist" aria-label="Book workspace tabs">
        {TABS.map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            aria-controls={`panel-${tab}`}
            id={`tab-${tab}`}
            onClick={() => setActiveTab(tab)}
            style={{
              ...styles.tab,
              ...(activeTab === tab ? styles.tabActive : {}),
            }}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <div style={styles.content}>
        {activeTab === "translate" && (
          <div role="tabpanel" id="panel-translate" aria-labelledby="tab-translate">
            <div style={styles.filterRow}>
              {book.translateLanguages.length > 1 && (
                <div style={styles.filterGroup}>
                  <label htmlFor="lang-filter" style={styles.label}>
                    Language
                  </label>
                  <select
                    id="lang-filter"
                    value={language ?? ""}
                    onChange={(e) => setLanguage(e.target.value || null)}
                    style={styles.select}
                  >
                    <option value="">All</option>
                    {book.translateLanguages.map((lang) => (
                      <option key={lang} value={lang}>
                        {languageLabel(lang)}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div style={styles.filterGroup}>
                <label htmlFor="status-filter" style={styles.label}>
                  Status
                </label>
                <select
                  id="status-filter"
                  value={status ?? ""}
                  onChange={(e) => setStatus(e.target.value || null)}
                  style={styles.select}
                >
                  <option value="">All</option>
                  <option value="pending">Pending</option>
                  <option value="translated">Translated</option>
                  <option value="approved">Approved</option>
                </select>
              </div>
            </div>

            <TranslateTab
              filters={translateFilters}
              isEditor={isEditor}
              onSubmitted={() => setStatsRefreshSignal((prev) => prev + 1)}
            />
          </div>
        )}
        {activeTab === "history" && (
          <div role="tabpanel" id="panel-history" aria-labelledby="tab-history">
            <HistoryTab filters={historyFilters} />
          </div>
        )}
      </div>
    </div>
  )
}

export default BookWorkspacePage

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: 32,
    maxWidth: 1200,
    margin: "0 auto",
  },
  backLink: {
    fontSize: 13,
    color: "var(--primary)",
    marginBottom: 16,
    display: "inline-block",
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "var(--muted)",
    marginBottom: 24,
  },
  filterRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    flexWrap: "wrap",
    padding: "12px 0",
    borderBottom: "1px solid var(--border)",
    marginBottom: 16,
  },
  filterGroup: {
    display: "flex",
    alignItems: "center",
    gap: 6,
  },
  label: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--muted)",
  },
  select: {
    padding: "6px 8px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    fontSize: 13,
  },
  tabBar: {
    display: "flex",
    gap: 0,
    borderBottom: "2px solid var(--border)",
    marginBottom: 24,
  },
  tab: {
    padding: "12px 24px",
    background: "none",
    border: "none",
    borderBottomWidth: 2,
    borderBottomStyle: "solid",
    borderBottomColor: "transparent",
    marginBottom: -2,
    fontSize: 14,
    fontWeight: 600,
    color: "var(--muted)",
    cursor: "pointer",
    transition: "color 0.15s, border-color 0.15s",
  },
  tabActive: {
    color: "var(--primary)",
    borderBottomColor: "var(--primary)",
  },
  content: {
    minHeight: 400,
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
    color: "var(--foreground)",
  },
}
