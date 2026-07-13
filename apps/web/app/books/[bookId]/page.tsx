"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import Link from "next/link"
import { publicEnv } from "@/lib/env/publicEnv"
import { PageStatus, ReviewStatus, BuildStatus, VersionStatus, BookStatus } from "@/lib/types"
import { REVIEW_STATUS_ORDER, REVIEW_STATUS_TITLES } from "@/lib/reviewStatus"
import {
  reorderPages,
  addBlankPage,
  deletePage,
  triggerBuild,
  getLatestBuild,
  cancelBuild,
  getVersions,
  getDownloadUrl,
  getMarkdownDownloadUrl,
  getHtmlDownloadUrl,
} from "@/lib/api/bookOrganization"
import type { BuildProgress, VersionListItem } from "@/lib/api/bookOrganization"

const FIRST_BATCH_SIZE = 35
const NEXT_BATCH_SIZE = 7

interface Page {
  id: string
  pageNumber: number
  originalPageNumber?: string
  status: PageStatus
  reviewStatus?: ReviewStatus
  thumbnailUrl?: string | null
  sectionCount?: number
  translatedPercent?: number
  order?: number
}

interface PageListResponse {
  items: Page[]
  total: number
  skip: number
  limit: number
}

interface BookDetail {
  id: string
  title: string
  author: string
  sourceLanguage: string
  translateLanguages: string[]
  status: BookStatus
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

interface GetPagesParams {
  reviewStatusFilter: string
  sortBy: "PAGE_NUMBER" | "PROGRESS"
  skip: number
  limit: number
}

async function getPages(
  bookId: string,
  { reviewStatusFilter, sortBy, skip, limit }: GetPagesParams,
): Promise<PageListResponse | null> {
  try {
    const query = new URLSearchParams({
      reviewStatus: reviewStatusFilter,
      sort: sortBy,
      skip: String(skip),
      limit: String(limit),
    })
    const res = await fetch(`/api/books/${bookId}/pages?${query.toString()}`, { cache: "no-store" })
    if (res.ok) {
      const data = await res.json()
      // Handle both response shapes: { items, total, skip, limit } (fast path)
      // and { pages, pagination, stats } (aggregation path)
      if (data.items) return data as PageListResponse
      if (data.pages) {
        return {
          items: data.pages,
          total: data.pagination?.total ?? data.pages.length,
          skip,
          limit,
        }
      }
    }
  } catch {
    /* noop */
  }
  return null
}

const isPagesReady = (bookStatus: BookStatus) => bookStatus === BookStatus.READY

const REVIEW_STATUS_META: Record<ReviewStatus, { color: string; border?: string }> = {
  [ReviewStatus.REJECTED]: { color: "#ef4444" },
  [ReviewStatus.NOT_STARTED]: { color: "#ffffff", border: "var(--muted)" },
  [ReviewStatus.NO_TRANSLATIONS]: { color: "#4b5563" },
  [ReviewStatus.PARTIALLY_TRANSLATED]: { color: "#f59e0b" },
  [ReviewStatus.FULLY_TRANSLATED]: { color: "#22d3ee" },
  [ReviewStatus.PARTIALLY_APPROVED]: { color: "#3b82f6" },
  [ReviewStatus.FULLY_APPROVED]: { color: "var(--success)" },
}

export default function BookConsolePage({ params }: { params: Promise<{ bookId: string }> }) {
  const [bookId, setBookId] = useState<string | null>(null)
  const [book, setBook] = useState<BookDetail | null>(null)
  const [pages, setPages] = useState<Page[]>([])
  const [loading, setLoading] = useState(true)
  const [reviewStatusFilter, setReviewStatusFilter] = useState<string>("ALL")
  const [sortBy, setSortBy] = useState<"PAGE_NUMBER" | "PROGRESS">("PAGE_NUMBER")
  const [skip, setSkip] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)

  // Book stats
  const [totalSections, setTotalSections] = useState(0)
  const [translatedSections, setTranslatedSections] = useState(0)

  // Build state
  const [buildProgress, setBuildProgress] = useState<BuildProgress | null>(null)
  const [buildPolling, setBuildPolling] = useState(false)
  const [buildError, setBuildError] = useState<string | null>(null)
  const [building, setBuilding] = useState(false)

  // Version state
  const [versions, setVersions] = useState<VersionListItem[]>([])

  const buildHasResult =
    buildProgress?.status === BuildStatus.COMPLETED ||
    buildProgress?.status === BuildStatus.FAILED ||
    buildProgress?.status === BuildStatus.CANCELLED

  // Reorder state
  const [reordering, setReordering] = useState<string | null>(null)

  // Sentinels
  const skipRef = useRef(skip)
  const hasMoreRef = useRef(hasMore)
  const loadingMoreRef = useRef(loadingMore)
  const sentinelRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    params.then(({ bookId }) => setBookId(bookId))
  }, [params])

  useEffect(() => {
    if (!bookId) return

    let cancelled = false
    let pollTimer: ReturnType<typeof setTimeout> | null = null

    const fetchData = async () => {
      setPages([])
      skipRef.current = 0
      setSkip(0)
      hasMoreRef.current = true
      setHasMore(true)
      setTotalSections(0)
      setTranslatedSections(0)

      const b = await getBook(bookId!)
      if (cancelled) return
      if (b) {
        setBook(b)
        if (isPagesReady(b.status)) {
          const p = await getPages(bookId!, {
            reviewStatusFilter,
            sortBy,
            skip: 0,
            limit: FIRST_BATCH_SIZE,
          })
          if (!cancelled && p && p.items) {
            const nextSkip = p.skip + p.items.length
            const nextHasMore = nextSkip < p.total
            setPages(p.items)
            skipRef.current = nextSkip
            setSkip(nextSkip)
            hasMoreRef.current = nextHasMore
            setHasMore(nextHasMore)

            // Compute summary stats
            let totalSec = 0
            let transSec = 0
            for (const page of p.items) {
              if (page.sectionCount) totalSec += page.sectionCount
              if (page.translatedPercent)
                transSec += Math.round(((page.sectionCount ?? 0) * page.translatedPercent) / 100)
            }
            setTotalSections(totalSec)
            setTranslatedSections(transSec)

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
  }, [bookId, reviewStatusFilter, sortBy])

  const loadMore = useCallback(async () => {
    if (!bookId || !hasMoreRef.current || loadingMoreRef.current) return
    loadingMoreRef.current = true
    setLoadingMore(true)
    const p = await getPages(bookId, {
      reviewStatusFilter,
      sortBy,
      skip: skipRef.current,
      limit: NEXT_BATCH_SIZE,
    })
    if (p && p.items) {
      const nextSkip = p.skip + p.items.length
      const nextHasMore = nextSkip < p.total
      setPages((prev) => [...prev, ...p.items])
      skipRef.current = nextSkip
      setSkip(nextSkip)
      hasMoreRef.current = nextHasMore
      setHasMore(nextHasMore)
    }
    loadingMoreRef.current = false
    setLoadingMore(false)
  }, [bookId, reviewStatusFilter, sortBy])

  useEffect(() => {
    if (!book || !isPagesReady(book.status)) return
    if (pages.length === 0 || !hasMore) return
    const sentinel = sentinelRef.current
    if (!sentinel) return

    const observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting) loadMore()
    })
    observer.observe(sentinel)

    return () => observer.disconnect()
  }, [book, pages.length, hasMore, loadMore])

  // ── Build polling ──────────────────────────────────────────────────
  useEffect(() => {
    if (!buildPolling || !bookId) return

    const interval = setInterval(async () => {
      try {
        const progress = await getLatestBuild(bookId!)
        setBuildProgress(progress)
        if (progress.status !== BuildStatus.BUILDING) {
          setBuildPolling(false)
          setBuilding(false)
        }
      } catch {
        setBuildPolling(false)
        setBuilding(false)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [buildPolling, bookId])

  // ── Version fetching ────────────────────────────────────────────────
  useEffect(() => {
    if (!bookId) return
    getVersions(bookId)
      .then((data) => setVersions(data.versions))
      .catch(() => {
        /* ignore */
      })
  }, [bookId, buildProgress?.status])

  // ── Reorder handlers ────────────────────────────────────────────────
  const handleMoveUp = async (index: number) => {
    if (index === 0 || !bookId) return
    const newPages = [...pages]
    const temp = newPages[index]!
    newPages[index] = newPages[index - 1]!
    newPages[index - 1] = temp

    setReordering("moving")
    try {
      const orders = newPages.map((p, i) => ({ pageId: p.id, order: i + 1 }))
      await reorderPages(bookId, orders)
      setPages(newPages)
    } catch {
      // Revert on failure: refetch
      const p = await getPages(bookId, {
        reviewStatusFilter,
        sortBy,
        skip: 0,
        limit: FIRST_BATCH_SIZE,
      })
      if (p && p.items) setPages(p.items)
    } finally {
      setReordering(null)
    }
  }

  const handleMoveDown = async (index: number) => {
    if (index === pages.length - 1 || !bookId) return
    const newPages = [...pages]
    const temp = newPages[index]!
    newPages[index] = newPages[index + 1]!
    newPages[index + 1] = temp

    setReordering("moving")
    try {
      const orders = newPages.map((p, i) => ({ pageId: p.id, order: i + 1 }))
      await reorderPages(bookId, orders)
      setPages(newPages)
    } catch {
      const p = await getPages(bookId, {
        reviewStatusFilter,
        sortBy,
        skip: 0,
        limit: FIRST_BATCH_SIZE,
      })
      if (p && p.items) setPages(p.items)
    } finally {
      setReordering(null)
    }
  }

  // ── Add page handler ────────────────────────────────────────────────
  const handleAddPage = async () => {
    if (!bookId) return
    const insertAfterOrder = pages.length
    try {
      await addBlankPage(bookId, insertAfterOrder)
      // Refetch
      const p = await getPages(bookId, {
        reviewStatusFilter,
        sortBy,
        skip: 0,
        limit: FIRST_BATCH_SIZE,
      })
      if (p && p.items) setPages(p.items)
    } catch {
      /* ignore */
    }
  }

  // ── Delete page handler ─────────────────────────────────────────────
  const handleDeletePage = async (pageId: string) => {
    if (
      !window.confirm(
        "Are you sure you want to delete this page? This action cannot be undone and will remove all sections and translations for this page.",
      )
    )
      return
    try {
      await deletePage(pageId)
      // Refetch
      const p = await getPages(bookId!, {
        reviewStatusFilter,
        sortBy,
        skip: 0,
        limit: FIRST_BATCH_SIZE,
      })
      if (p && p.items) setPages(p.items)
    } catch {
      /* ignore */
    }
  }

  // ── Build handlers ────────────────────────────────────────────────────
  const handleTriggerBuild = async () => {
    if (!bookId) return
    setBuildError(null)
    setBuilding(true)
    try {
      await triggerBuild(bookId)
      setBuildPolling(true)
      // Fetch initial progress
      const progress = await getLatestBuild(bookId)
      setBuildProgress(progress)
    } catch (err) {
      setBuildError(err instanceof Error ? err.message : "Failed to start build")
      setBuilding(false)
    }
  }

  const handleCancelBuild = async () => {
    if (!bookId) return
    try {
      await cancelBuild(bookId)
      setBuildPolling(false)
      setBuilding(false)
      const progress = await getLatestBuild(bookId)
      setBuildProgress(progress)
    } catch {
      /* ignore */
    }
  }

  const handleDownloadVersion = async (versionNumber: number) => {
    if (!bookId) return
    try {
      const downloadData = await getDownloadUrl(bookId, versionNumber)
      window.open(downloadData.downloadUrl, "_blank")
    } catch {
      /* ignore */
    }
  }

  const handleDownloadVersionMarkdown = async (versionNumber: number) => {
    if (!bookId) return
    try {
      const downloadData = await getMarkdownDownloadUrl(bookId, versionNumber)
      window.open(downloadData.downloadUrl, "_blank")
    } catch {
      /* ignore */
    }
  }

  const handleDownloadVersionHtml = async (versionNumber: number) => {
    if (!bookId) return
    try {
      const downloadData = await getHtmlDownloadUrl(bookId, versionNumber)
      window.open(downloadData.downloadUrl, "_blank")
    } catch {
      /* ignore */
    }
  }

  // ── Render ──────────────────────────────────────────────────────────

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
    background: book.status === BookStatus.READY ? "var(--success)" : "var(--surface)",
    borderColor: book.status === BookStatus.READY ? "var(--success)" : "var(--border)",
    color: book.status === BookStatus.READY ? "#fff" : "var(--foreground)",
  }

  return (
    <div style={styles.page}>
      <Link href="/books" style={styles.backLink}>
        ← Back to books
      </Link>

      {/* Header */}
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

      {book.status !== BookStatus.READY && (
        <div style={styles.processing}>
          <div className="spinner" style={styles.spinner} />
          <span>Processing book pages... This may take a moment.</span>
        </div>
      )}

      {book.status === BookStatus.READY && (
        <div style={styles.layout} className="bookLayout">
          {/* ── Main Column ─────────────────────────────────────── */}
          <div style={styles.mainColumn}>
            {/* Summary Stats Bar */}
            {totalSections > 0 && (
              <div style={styles.statsBar}>
                <div style={styles.statItem}>
                  <span style={styles.statValue}>{pages.length}</span>
                  <span style={styles.statLabel}>Pages</span>
                </div>
                <div style={styles.statDivider} />
                <div style={styles.statItem}>
                  <span style={styles.statValue}>{totalSections}</span>
                  <span style={styles.statLabel}>Sections</span>
                </div>
                <div style={styles.statDivider} />
                <div style={styles.statItem}>
                  <span style={styles.statValue}>
                    {totalSections > 0 ? Math.round((translatedSections / totalSections) * 100) : 0}
                    %
                  </span>
                  <span style={styles.statLabel}>Translated</span>
                </div>
                <div style={styles.statDivider} />
                <div style={styles.statItem}>
                  <span style={styles.statValue}>{translatedSections}</span>
                  <span style={styles.statLabel}>Approved</span>
                </div>
              </div>
            )}

            {/* Filters */}
            <div style={styles.controls}>
              <select
                style={styles.filter}
                value={reviewStatusFilter}
                onChange={(e) => setReviewStatusFilter(e.target.value)}
              >
                <option value="ALL">All Pages</option>
                {REVIEW_STATUS_ORDER.map((status) => (
                  <option key={status} value={status}>
                    {REVIEW_STATUS_TITLES[status]}
                  </option>
                ))}
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

            {/* Page Grid */}
            <div style={styles.pageGrid}>
              {pages.map((page, index) => (
                <div key={page.id} style={styles.pageCardWrapper}>
                  <Link href={`/books/${bookId}/pages/${page.pageNumber}`} style={styles.pageCard}>
                    <div style={styles.thumbnail}>
                      {page.thumbnailUrl ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img
                          src={page.thumbnailUrl}
                          alt={`Page ${page.originalPageNumber || page.pageNumber}`}
                          style={styles.thumbnailImg}
                        />
                      ) : (
                        <div style={styles.thumbnailPlaceholder} />
                      )}
                      {page.reviewStatus && (
                        <span
                          style={{
                            ...styles.statusDot,
                            background: REVIEW_STATUS_META[page.reviewStatus].color,
                            border: `2.5px solid ${REVIEW_STATUS_META[page.reviewStatus].border ?? "var(--background)"}`,
                          }}
                          title={REVIEW_STATUS_TITLES[page.reviewStatus]}
                        />
                      )}
                    </div>
                    <div style={styles.pageNum}>{page.originalPageNumber || page.pageNumber}</div>
                  </Link>

                  {/* Progress bar */}
                  {page.sectionCount !== undefined && page.sectionCount > 0 && (
                    <div style={styles.pageProgressBar}>
                      <div
                        style={{
                          ...styles.pageProgressFill,
                          width: `${page.translatedPercent ?? 0}%`,
                        }}
                      />
                    </div>
                  )}

                  {/* Reorder buttons */}
                  <div style={styles.reorderButtons}>
                    <button
                      style={{
                        ...styles.reorderBtn,
                        opacity: index === 0 || reordering === "moving" ? 0.3 : 1,
                      }}
                      disabled={index === 0 || reordering === "moving"}
                      onClick={(e) => {
                        e.preventDefault()
                        handleMoveUp(index)
                      }}
                      title="Move up"
                    >
                      ▲
                    </button>
                    <button
                      style={{
                        ...styles.reorderBtn,
                        opacity: index === pages.length - 1 || reordering === "moving" ? 0.3 : 1,
                      }}
                      disabled={index === pages.length - 1 || reordering === "moving"}
                      onClick={(e) => {
                        e.preventDefault()
                        handleMoveDown(index)
                      }}
                      title="Move down"
                    >
                      ▼
                    </button>
                    <button
                      style={styles.deleteBtn}
                      onClick={(e) => {
                        e.preventDefault()
                        handleDeletePage(page.id)
                      }}
                      title="Delete page"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
              {pages.length === 0 && (
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

            {/* Add Page Button */}
            <button style={styles.addPageBtn} onClick={handleAddPage}>
              + Add Blank Page
            </button>

            {/* Sentinel for infinite scroll */}
            {pages.length > 0 && hasMore && <div ref={sentinelRef} style={styles.sentinel} />}
          </div>

          {/* ── Sticky Sidebar: Review / Build & Publish / Version History ── */}
          <div style={styles.sidebar} className="bookSidebar">
            <Link href={`/books/${bookId}/review`} style={styles.reviewLink}>
              Review Translations
            </Link>

            {/* Build & Publish */}
            <div style={styles.actionPanel}>
              <div style={styles.actionPanelHeader}>
                <h3 style={styles.actionPanelTitle}>Build & Publish</h3>
              </div>

              {buildError && <div style={styles.buildError}>{buildError}</div>}

              <div style={styles.actionPanelBody}>
                <div style={styles.buildInfo}>
                  <span>Generate a compiled PDF of the finalized book.</span>
                </div>

                {/* Build Progress */}
                {buildProgress && buildProgress.status === BuildStatus.BUILDING && (
                  <div style={styles.buildProgressSection}>
                    <div style={styles.buildProgressLabel}>
                      Building: page {buildProgress.currentPage ?? 0} of{" "}
                      {buildProgress.totalPages ?? "..."}
                      {buildProgress.estimatedRemainingMs != null && (
                        <span style={styles.buildEstimate}>
                          {" "}
                          · ~{Math.round(buildProgress.estimatedRemainingMs / 1000)}s remaining
                        </span>
                      )}
                    </div>
                    <div style={styles.barTrack}>
                      <div
                        style={{
                          ...styles.barFill,
                          width:
                            buildProgress.totalPages && buildProgress.totalPages > 0
                              ? `${((buildProgress.currentPage ?? 0) / buildProgress.totalPages) * 100}%`
                              : "0%",
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Completed Build */}
                {buildHasResult && (
                  <div style={styles.buildResultSection}>
                    {buildProgress!.status === BuildStatus.COMPLETED ? (
                      <div style={styles.buildCompleted}>
                        Build completed in{" "}
                        {buildProgress!.buildDurationMs != null
                          ? `${(buildProgress!.buildDurationMs / 1000).toFixed(1)}s`
                          : "N/A"}
                      </div>
                    ) : buildProgress!.status === BuildStatus.FAILED ? (
                      <div style={styles.buildFailed}>
                        Build failed: {buildProgress!.errorMessage ?? "Unknown error"}
                      </div>
                    ) : (
                      <div style={styles.buildCancelled}>Build was cancelled</div>
                    )}
                  </div>
                )}

                {/* Action Buttons */}
                <div style={styles.buildActions}>
                  {buildProgress?.status !== BuildStatus.BUILDING && !building && (
                    <button style={styles.buildButton} onClick={handleTriggerBuild}>
                      Build Book
                    </button>
                  )}
                  {(buildProgress?.status === BuildStatus.BUILDING || building) && (
                    <button style={styles.cancelBuildButton} onClick={handleCancelBuild}>
                      Cancel Build
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Version History */}
            <div style={styles.actionPanel}>
              <div style={styles.actionPanelHeader}>
                <h3 style={styles.actionPanelTitle}>Version History</h3>
              </div>

              <div style={styles.versionList}>
                {versions.length === 0 && (
                  <div style={styles.versionEmpty}>No versions created yet.</div>
                )}
                {versions.map((version, index) => {
                  const statusColor =
                    version.status === VersionStatus.FINALIZED
                      ? "var(--success)"
                      : version.status === VersionStatus.DRAFT
                        ? "var(--muted)"
                        : version.status === VersionStatus.ARCHIVED
                          ? "#ef4444"
                          : "var(--muted)"
                  const showLabel = version.label && version.label !== `v${version.versionNumber}`
                  const isLast = index === versions.length - 1

                  return (
                    <div
                      key={version.versionNumber}
                      style={{
                        ...styles.versionRow,
                        borderBottom: isLast ? "none" : "1px solid var(--border)",
                      }}
                    >
                      <div style={styles.versionTopLine}>
                        <div style={styles.versionTopLineLeft}>
                          <span style={styles.versionNumber}>v{version.versionNumber}</span>
                          <span
                            style={{
                              ...styles.versionStatus,
                              color: statusColor,
                              borderColor: statusColor,
                            }}
                          >
                            {version.status}
                          </span>
                        </div>
                        {version.status === VersionStatus.FINALIZED && (
                          <div style={styles.versionDownloadGroup}>
                            <button
                              className="versionDownloadBtn"
                              style={styles.versionDownloadBtn}
                              onClick={() => handleDownloadVersion(version.versionNumber)}
                              title={`Download v${version.versionNumber} PDF`}
                              aria-label={`Download v${version.versionNumber} PDF`}
                            >
                              <svg width="20" height="20" viewBox="0 0 24 24">
                                <path
                                  d="M6 1.5h8.5L19 6v15.5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V2.5a1 1 0 0 1 1-1z"
                                  fill="#f4f4f5"
                                  stroke="#c4c4c8"
                                  strokeWidth="1"
                                />
                                <path
                                  d="M14.5 1.5V6H19z"
                                  fill="#dcdce0"
                                  stroke="#c4c4c8"
                                  strokeWidth="1"
                                />
                                <rect
                                  x="2.5"
                                  y="12"
                                  width="15"
                                  height="8"
                                  rx="1.5"
                                  fill="#e53935"
                                />
                                <text
                                  x="10"
                                  y="17.9"
                                  textAnchor="middle"
                                  fontSize="6.5"
                                  fontWeight="700"
                                  fontFamily="Arial, sans-serif"
                                  fill="#ffffff"
                                >
                                  PDF
                                </text>
                              </svg>
                            </button>
                            {version.hasMarkdown && (
                              <button
                                className="versionDownloadBtn"
                                style={styles.versionDownloadBtn}
                                onClick={() => handleDownloadVersionMarkdown(version.versionNumber)}
                                title={`Download v${version.versionNumber} Markdown`}
                                aria-label={`Download v${version.versionNumber} Markdown`}
                              >
                                <svg width="20" height="20" viewBox="0 0 24 24">
                                  <path
                                    d="M6 1.5h8.5L19 6v15.5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V2.5a1 1 0 0 1 1-1z"
                                    fill="#f4f4f5"
                                    stroke="#c4c4c8"
                                    strokeWidth="1"
                                  />
                                  <path
                                    d="M14.5 1.5V6H19z"
                                    fill="#dcdce0"
                                    stroke="#c4c4c8"
                                    strokeWidth="1"
                                  />
                                  <rect
                                    x="2.5"
                                    y="12"
                                    width="15"
                                    height="8"
                                    rx="1.5"
                                    fill="#2563eb"
                                  />
                                  <text
                                    x="10"
                                    y="17.9"
                                    textAnchor="middle"
                                    fontSize="6.5"
                                    fontWeight="700"
                                    fontFamily="Arial, sans-serif"
                                    fill="#ffffff"
                                  >
                                    MD
                                  </text>
                                </svg>
                              </button>
                            )}
                            {version.hasHtml && (
                              <button
                                className="versionDownloadBtn"
                                style={styles.versionDownloadBtn}
                                onClick={() => handleDownloadVersionHtml(version.versionNumber)}
                                title={`Download v${version.versionNumber} HTML`}
                                aria-label={`Download v${version.versionNumber} HTML`}
                              >
                                <svg width="20" height="20" viewBox="0 0 24 24">
                                  <path
                                    d="M6 1.5h8.5L19 6v15.5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V2.5a1 1 0 0 1 1-1z"
                                    fill="#f4f4f5"
                                    stroke="#c4c4c8"
                                    strokeWidth="1"
                                  />
                                  <path
                                    d="M14.5 1.5V6H19z"
                                    fill="#dcdce0"
                                    stroke="#c4c4c8"
                                    strokeWidth="1"
                                  />
                                  <rect
                                    x="2.5"
                                    y="12"
                                    width="15"
                                    height="8"
                                    rx="1.5"
                                    fill="#f97316"
                                  />
                                  <text
                                    x="10"
                                    y="17.9"
                                    textAnchor="middle"
                                    fontSize="6.5"
                                    fontWeight="700"
                                    fontFamily="Arial, sans-serif"
                                    fill="#ffffff"
                                  >
                                    HTML
                                  </text>
                                </svg>
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                      {showLabel && <div style={styles.versionLabel}>{version.label}</div>}
                      <div style={styles.versionMeta}>
                        {version.createdBy && <span>{version.createdBy.name}</span>}
                        {version.createdBy && version.createdAt && <span>·</span>}
                        {version.createdAt && (
                          <span>{new Date(version.createdAt).toLocaleDateString()}</span>
                        )}
                      </div>
                      {version.changelog && (
                        <div style={styles.versionChangelog}>{version.changelog}</div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @media (max-width: 860px) {
          .bookLayout {
            flex-direction: column;
          }
          .bookSidebar {
            position: static;
            flex: 1 1 auto;
            width: 100%;
          }
        }
        .versionDownloadBtn:hover {
          background: var(--surface);
          border-color: var(--primary);
        }
        .versionDownloadBtn:active {
          transform: scale(0.94);
        }
      `}</style>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 48, maxWidth: 1280, margin: "0 auto" },
  sentinel: { height: 1 },

  // ── Two-Column Layout ──────────────────────────────────────────
  layout: {
    display: "flex",
    alignItems: "flex-start",
    gap: 32,
  },
  mainColumn: {
    flex: "1 1 auto",
    minWidth: 0,
  },
  sidebar: {
    flex: "0 0 300px",
    display: "flex",
    flexDirection: "column" as const,
    gap: 16,
    position: "sticky" as const,
    top: 24,
  },
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

  // ── Stats Bar ────────────────────────────────────────────────
  statsBar: {
    display: "flex",
    alignItems: "center",
    gap: 0,
    padding: "12px 20px",
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    marginBottom: 24,
  },
  statItem: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 2,
    flex: 1,
  },
  statValue: { fontSize: 22, fontWeight: 700, color: "var(--foreground)" },
  statLabel: { fontSize: 11, color: "var(--muted)", textTransform: "uppercase" as const },
  statDivider: {
    width: 1,
    height: 32,
    background: "var(--border)",
    margin: "0 8px",
  },

  // ── Controls ─────────────────────────────────────────────────
  controls: { display: "flex", gap: 12, marginBottom: 24, alignItems: "center" },
  filter: {
    padding: "8px 12px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 13,
    background: "var(--background)",
    color: "var(--foreground)",
  },
  reviewLink: {
    padding: "12px 16px",
    background: "var(--primary)",
    color: "#fff",
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
    textDecoration: "none",
    textAlign: "center" as const,
  },

  // ── Page Grid ────────────────────────────────────────────────
  pageGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))",
    gap: 16,
  },
  pageCardWrapper: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 4,
  },
  pageCard: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 8,
    padding: 12,
    border: "1px solid var(--border)",
    borderRadius: 8,
    cursor: "pointer",
    transition: "box-shadow 0.2s",
    width: "100%",
  },
  pageNum: { fontSize: 16, fontWeight: 600 },
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
    top: 6,
    right: 6,
    width: 14,
    height: 14,
    borderRadius: "50%",
    border: "2.5px solid var(--background)",
    boxShadow: "0 1px 3px rgba(0,0,0,0.35)",
  },
  thumbnailImg: { width: "100%", height: "100%", objectFit: "cover" },
  thumbnailPlaceholder: { width: "100%", height: "100%", background: "var(--surface)" },

  // ── Progress Per Page ────────────────────────────────────────
  pageProgressBar: {
    width: "100%",
    height: 4,
    background: "var(--border)",
    borderRadius: 2,
    overflow: "hidden",
  },
  pageProgressFill: {
    height: "100%",
    background: "var(--primary)",
    borderRadius: 2,
    transition: "width 0.3s ease",
  },

  // ── Reorder + Delete Buttons ───────────────────────────────────
  reorderButtons: {
    display: "flex",
    gap: 4,
    alignItems: "center",
  },
  reorderBtn: {
    padding: "2px 6px",
    border: "1px solid var(--border)",
    borderRadius: 4,
    background: "var(--background)",
    color: "var(--foreground)",
    fontSize: 11,
    cursor: "pointer",
    lineHeight: 1,
  },
  deleteBtn: {
    padding: "2px 6px",
    border: "1px solid #ef4444",
    borderRadius: 4,
    background: "#fef2f2",
    color: "#dc2626",
    fontSize: 11,
    cursor: "pointer",
    lineHeight: 1,
    marginLeft: 2,
  },

  // ── Add Page ─────────────────────────────────────────────────
  addPageBtn: {
    marginTop: 20,
    padding: "10px 20px",
    border: "2px dashed var(--border)",
    borderRadius: 8,
    background: "transparent",
    color: "var(--muted)",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    width: "100%",
    textAlign: "center" as const,
  },

  // ── Sidebar Panels (Build & Publish / Version History) ────────
  actionPanel: {
    border: "1px solid var(--border)",
    borderRadius: 8,
    overflow: "hidden",
    background: "var(--surface)",
  },
  actionPanelHeader: {
    padding: "14px 20px",
    borderBottom: "1px solid var(--border)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  actionPanelTitle: { fontSize: 16, fontWeight: 700, margin: 0 },
  actionPanelBody: { padding: 20 },
  buildInfo: {
    fontSize: 14,
    color: "var(--muted)",
    marginBottom: 16,
  },
  buildError: {
    padding: "8px 14px",
    margin: "12px 20px 0",
    background: "#fef2f2",
    color: "#991b1b",
    fontSize: 13,
    borderRadius: 6,
  },
  barTrack: {
    height: 8,
    background: "var(--border)",
    borderRadius: 4,
    overflow: "hidden",
    marginTop: 6,
  },
  barFill: {
    height: "100%",
    background: "var(--primary)",
    borderRadius: 4,
    transition: "width 0.5s ease",
  },
  buildResultSection: { marginBottom: 16 },
  buildCompleted: { fontSize: 14, color: "#166534", fontWeight: 600 },
  buildFailed: { fontSize: 14, color: "#991b1b" },
  buildCancelled: { fontSize: 14, color: "var(--muted)" },
  buildActions: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 10,
  },
  buildButton: {
    width: "100%",
    padding: "10px 24px",
    background: "var(--primary)",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  cancelBuildButton: {
    width: "100%",
    padding: "10px 24px",
    background: "#dc2626",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  buildProgressSection: {
    marginBottom: 16,
  },
  buildProgressLabel: {
    fontSize: 13,
    color: "var(--muted)",
    marginBottom: 6,
  },

  // ── Version History ──────────────────────────────────────────
  versionList: { padding: 12 },
  versionEmpty: {
    padding: "12px 8px",
    fontSize: 13,
    color: "var(--muted)",
  },
  versionRow: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 4,
    padding: "12px 8px",
    borderBottom: "1px solid var(--border)",
  },
  versionTopLine: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8,
  },
  versionTopLineLeft: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  versionNumber: { fontSize: 14, fontWeight: 700 },
  versionLabel: { fontSize: 13, color: "var(--muted)" },
  versionStatus: {
    fontSize: 11,
    fontWeight: 600,
    textTransform: "uppercase" as const,
    padding: "2px 8px",
    borderRadius: 999,
    border: "1px solid var(--border)",
    whiteSpace: "nowrap" as const,
  },
  versionDownloadGroup: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    flexShrink: 0,
  },
  versionDownloadBtn: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: 28,
    height: 28,
    padding: 0,
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    flexShrink: 0,
    transition: "background 0.15s ease, border-color 0.15s ease, color 0.15s ease",
  },
  versionMeta: {
    display: "flex",
    gap: 6,
    alignItems: "center",
    fontSize: 12,
    color: "var(--muted)",
  },
  versionChangelog: {
    fontSize: 12,
    fontStyle: "italic" as const,
    color: "var(--muted)",
  },
}
