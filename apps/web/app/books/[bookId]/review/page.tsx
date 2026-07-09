"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { apiFetchBrowser } from "@/lib/apiClientBrowser"
import {
  approveTranslation,
  rejectTranslation,
  editorOverrideTranslation,
} from "@/lib/api/bookOrganization"

interface SectionReview {
  id: string
  pageNumber: number
  sectionOrder: number
  type: string
  originalText: string | null
  aiExtractedText: string | null
  exactLetterTranslation: string | null
  autoTranslatedText: string | null
  wordByWordMeaning: string | null
  fullMeaning: string | null
  simplifiedMeaning: string | null
  croppedImageUrl: string | null
  translations: TranslationDetail[]
}

interface TranslationDetail {
  id: string
  section: { id: string }
  translator: { id: string }
  translatorName: string | null
  translatedText: string
  exactLetterTranslation: string | null
  isApproved: boolean
  rejected: boolean
  approvedBy: { id: string } | null
  createdAt: string | null
}

interface BookDetail {
  id: string
  title: string
  author: string
  sourceLanguage: string
  translateLanguages: string[]
  status: string
}

interface PageMeta {
  id: string
  pageNumber: number
}

interface ReviewData {
  page: {
    id: string
    pageNumber: number
    imageUrl: string | null
    status: string
    reviewed: boolean
  }
  sections: SectionReview[]
}

const parseMarkdownTable = (markdown: string): { headers: string[]; rows: string[][] } | null => {
  const lines = markdown
    .trim()
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
  if (lines.length < 2) return null

  const splitRow = (line: string) =>
    line
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim())

  const headers = splitRow(lines[0] ?? "")
  const rows = lines.slice(2).map(splitRow)
  return { headers, rows }
}

const MarkdownTable = ({ markdown }: { markdown: string }) => {
  const table = parseMarkdownTable(markdown)
  if (!table) {
    return <div style={styles.fieldValue}>{markdown}</div>
  }

  return (
    <div style={styles.tableWrapper}>
      <table style={styles.table}>
        <thead>
          <tr>
            {table.headers.map((header, i) => (
              <th key={i} style={styles.th}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j} style={styles.td}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface SectionCarouselViewProps {
  sec: SectionReview
  index: number
  total: number
  bookId: string
  zoom: Record<string, number>
  onZoomIn: (key: string) => void
  onZoomOut: (key: string) => void
  onZoomReset: (key: string) => void
  isDragging: boolean
  onImageMouseDown: (e: React.MouseEvent) => void
  onImageMouseMove: (e: React.MouseEvent) => void
  onImageMouseUp: (e: React.MouseEvent) => void
  overrideSectionId: string | null
  overrideText: string
  submitting: boolean
  sourceTranslationId: string | undefined
  rejectReasons: Record<string, string>
  rejecting: Record<string, boolean>
  onGoTo: (i: number) => void
  onApprove: (id: string) => void
  onReject: (id: string) => void
  onRejectReasonChange: (id: string, value: string) => void
  onCopyFromTranslator: (text: string, transId: string, secId: string) => void
  onOverrideTextChange: (secId: string, text: string) => void
  onOverrideFocus: (secId: string) => void
  onOverrideSubmit: () => void
}

const SectionCarouselView = ({
  sec,
  index,
  total,
  bookId,
  zoom,
  onZoomIn,
  onZoomOut,
  onZoomReset,
  isDragging,
  onImageMouseDown,
  onImageMouseMove,
  onImageMouseUp,
  overrideSectionId,
  overrideText,
  submitting,
  sourceTranslationId,
  rejectReasons,
  rejecting,
  onGoTo,
  onApprove,
  onReject,
  onCopyFromTranslator,
  onRejectReasonChange,
  onOverrideTextChange,
  onOverrideFocus,
  onOverrideSubmit,
}: SectionCarouselViewProps) => {
  const router = useRouter()
  const zoomKey = `sec-${sec.id}`
  const isFirst = index === 0
  const isLast = index === total - 1

  return (
    <div style={styles.carouselSection}>
      <div style={styles.carouselNav}>
        <button
          style={{ ...styles.carouselBtn, opacity: isFirst ? 0.4 : 1 }}
          disabled={isFirst}
          onClick={() => onGoTo(index - 1)}
        >
          ← Previous
        </button>
        <div style={styles.carouselDots}>
          {Array.from({ length: total }, (_, i) => (
            <button
              key={i}
              style={{
                ...styles.carouselDot,
                background: i === index ? "var(--primary)" : "var(--border)",
              }}
              onClick={() => onGoTo(i)}
              aria-label={`Section ${i + 1}`}
            />
          ))}
        </div>
        <span style={styles.carouselLabel}>
          Section {index + 1} / {total}
        </span>
        <button
          style={styles.translateBtn}
          onClick={() => router.push(`/translate/${bookId}?section=${sec.id}`)}
        >
          Translate
        </button>
        <button
          style={{ ...styles.carouselBtn, opacity: isLast ? 0.4 : 1 }}
          disabled={isLast}
          onClick={() => onGoTo(index + 1)}
        >
          Next →
        </button>
      </div>

      <div style={styles.sectionCard}>
        <div style={styles.sectionHeader}>
          <span style={styles.sectionTitle}>
            Section {sec.sectionOrder + 1} ({sec.type})
          </span>
          <span
            style={{
              ...styles.sectionStatus,
              ...(sec.translations.some((t) => t.isApproved)
                ? styles.statusApproved
                : sec.translations.some((t) => t.rejected)
                  ? styles.statusRejected
                  : styles.statusPending),
            }}
          >
            {sec.translations.some((t) => t.isApproved)
              ? "Approved"
              : sec.translations.some((t) => t.rejected)
                ? "Rejected"
                : "Pending"}
          </span>
        </div>

        {sec.croppedImageUrl && (
          <div>
            <div
              style={{
                ...styles.secImageScrollWrap,
                cursor: isDragging ? "grabbing" : "grab",
              }}
              onMouseDown={onImageMouseDown}
              onMouseMove={onImageMouseMove}
              onMouseUp={onImageMouseUp}
            >
              <div style={styles.imageInner}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={sec.croppedImageUrl}
                  alt={`Section ${sec.sectionOrder + 1}`}
                  draggable={false}
                  style={{
                    width: `${zoom[zoomKey] ?? 100}%`,
                    height: "auto",
                    display: "block",
                  }}
                />
              </div>
            </div>
            <div style={styles.zoomControls}>
              <button
                style={styles.zoomBtn}
                onClick={() => onZoomOut(zoomKey)}
                aria-label="Zoom out"
              >
                −
              </button>
              <span style={{ fontSize: 13, color: "var(--foreground)" }}>
                {zoom[zoomKey] ?? 100}%
              </span>
              <button style={styles.zoomBtn} onClick={() => onZoomIn(zoomKey)} aria-label="Zoom in">
                +
              </button>
              <button
                style={styles.zoomBtn}
                onClick={() => onZoomReset(zoomKey)}
                aria-label="Reset zoom"
              >
                ⟳
              </button>
            </div>
          </div>
        )}

        {sec.originalText && (
          <div style={styles.fieldCard}>
            <div style={{ ...styles.fieldLabel, color: "var(--foreground)" }}>Original Text</div>
            <div style={styles.fieldValue}>{sec.originalText}</div>
          </div>
        )}

        {sec.aiExtractedText && (
          <div style={styles.fieldCard}>
            <div style={{ ...styles.fieldLabel, color: "var(--foreground)" }}>
              AI Extracted Text
            </div>
            <div style={styles.fieldValue}>{sec.aiExtractedText}</div>
          </div>
        )}

        {sec.exactLetterTranslation && (
          <div style={styles.fieldCard}>
            <div style={{ ...styles.fieldLabel, color: "var(--foreground)" }}>
              Exact Letter Translation
            </div>
            <div style={styles.fieldValue}>{sec.exactLetterTranslation}</div>
          </div>
        )}

        {sec.wordByWordMeaning && (
          <div style={styles.fieldCard}>
            <div style={{ ...styles.fieldLabel, color: "var(--foreground)" }}>
              Word by Word Meaning
            </div>
            <MarkdownTable markdown={sec.wordByWordMeaning} />
          </div>
        )}

        {sec.fullMeaning && (
          <div style={styles.fieldCard}>
            <div style={{ ...styles.fieldLabel, color: "var(--foreground)" }}>Full Meaning</div>
            <div style={styles.fieldValue}>{sec.fullMeaning}</div>
          </div>
        )}

        {sec.simplifiedMeaning && (
          <div style={styles.fieldCard}>
            <div style={{ ...styles.fieldLabel, color: "var(--foreground)" }}>
              Simplified Meaning
            </div>
            <div style={styles.fieldValue}>{sec.simplifiedMeaning}</div>
          </div>
        )}

        <div style={styles.translationsSection}>
          <div style={styles.translationsLabel}>Translations ({sec.translations.length})</div>

          {sec.translations.length === 0 && (
            <div style={styles.noTrans}>No translations for this section.</div>
          )}

          {sec.translations.map((tran) => {
            const isPending = !tran.isApproved && !tran.rejected
            return (
              <div key={tran.id} style={styles.transCard}>
                <div style={styles.transHeader}>
                  <span style={styles.transName}>
                    {tran.translatorName ?? "Unknown Translator"}
                  </span>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    {tran.createdAt && (
                      <span style={styles.transDate}>
                        {new Date(tran.createdAt).toLocaleDateString()}
                      </span>
                    )}
                    <span
                      style={{
                        ...styles.badge,
                        ...(tran.isApproved
                          ? styles.badgeApproved
                          : tran.rejected
                            ? styles.badgeRejected
                            : styles.badgePending),
                      }}
                    >
                      {tran.isApproved ? "Approved" : tran.rejected ? "Rejected" : "Pending"}
                    </span>
                  </div>
                </div>
                <div style={styles.transText}>{tran.translatedText}</div>
                <div style={styles.transActions}>
                  {tran.isApproved ? (
                    <button
                      style={styles.btnReject}
                      disabled={rejecting[tran.id]}
                      onClick={() => onReject(tran.id)}
                    >
                      {rejecting[tran.id] ? "Rejecting..." : "✕ Reject"}
                    </button>
                  ) : tran.rejected ? (
                    <button style={styles.btnApprove} onClick={() => onApprove(tran.id)}>
                      ✓ Approve
                    </button>
                  ) : (
                    <>
                      <button style={styles.btnApprove} onClick={() => onApprove(tran.id)}>
                        ✓ Approve
                      </button>
                      <button
                        style={styles.btnCopy}
                        onClick={() => onCopyFromTranslator(tran.translatedText, tran.id, sec.id)}
                      >
                        Copy
                      </button>
                    </>
                  )}
                </div>
                {isPending && (
                  <div style={styles.rejectRow}>
                    <textarea
                      style={styles.rejectTextarea}
                      placeholder="Optional rejection reason..."
                      value={rejectReasons[tran.id] ?? ""}
                      onChange={(e) => onRejectReasonChange(tran.id, e.target.value)}
                      rows={2}
                    />
                    <button
                      style={styles.btnReject}
                      disabled={rejecting[tran.id]}
                      onClick={() => onReject(tran.id)}
                    >
                      {rejecting[tran.id] ? "Rejecting..." : "✕ Reject"}
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        <div style={styles.overrideCard}>
          <div style={styles.cardTitle}>Editor Override</div>
          <p style={styles.overrideHint}>
            Submit your own translation (auto-approved). Use "Copy" above to start from an existing
            translation.
          </p>
          <textarea
            style={styles.overrideTextarea}
            placeholder="Type your translation here..."
            value={overrideSectionId === sec.id ? overrideText : ""}
            onChange={(e) => onOverrideTextChange(sec.id, e.target.value)}
            onFocus={() => onOverrideFocus(sec.id)}
            rows={4}
          />
          <div style={styles.overrideAction}>
            <button
              style={{
                ...styles.btnSubmit,
                opacity:
                  overrideSectionId !== sec.id || !overrideText.trim() || submitting ? 0.5 : 1,
              }}
              disabled={overrideSectionId !== sec.id || !overrideText.trim() || submitting}
              onClick={onOverrideSubmit}
            >
              {submitting ? "Submitting..." : "Submit as Editor's Choice"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

const TranslationReviewPage = () => {
  const { bookId } = useParams<{ bookId: string }>()
  const [book, setBook] = useState<BookDetail | null>(null)
  const [pages, setPages] = useState<PageMeta[]>([])
  const [selectedPage, setSelectedPage] = useState<number | null>(null)
  const [reviewData, setReviewData] = useState<ReviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [pageLoading, setPageLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [carouselIndex, setCarouselIndex] = useState(0)
  const [rejectReasons, setRejectReasons] = useState<Record<string, string>>({})
  const [rejecting, setRejecting] = useState<Record<string, boolean>>({})
  const [overrideText, setOverrideText] = useState("")
  const [sourceTranslationId, setSourceTranslationId] = useState<string | undefined>(undefined)
  const [overrideSectionId, setOverrideSectionId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [finishing, setFinishing] = useState(false)
  const [zoom, setZoom] = useState<Record<string, number>>({})

  const fetchPageReview = async (pageNum: number) => {
    if (!bookId) return
    setPageLoading(true)
    setSuccessMsg(null)
    setActionError(null)
    setOverrideText("")
    setSourceTranslationId(undefined)
    setOverrideSectionId(null)
    setRejectReasons({})
    setZoom({})
    try {
      const res = await apiFetchBrowser(`/api/books/${bookId}/pages/${pageNum}/review`)
      if (!res.ok) throw new Error("Failed to fetch page review")
      const data: ReviewData = await res.json()
      setReviewData(data)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to load page")
    } finally {
      setPageLoading(false)
    }
  }

  useEffect(() => {
    if (!bookId) return
    let cancelled = false

    const init = async () => {
      try {
        const bookRes = await apiFetchBrowser(`/api/books/${bookId}`)
        if (!bookRes.ok) throw new Error("Book not found")
        const bookData: BookDetail = await bookRes.json()
        if (cancelled) return
        setBook(bookData)

        const pagesRes = await apiFetchBrowser(
          `/api/books/${bookId}/pages?status=ALL&sort=PAGE_NUMBER&skip=0&limit=200`,
        )
        if (!pagesRes.ok) throw new Error("Failed to fetch pages")
        const pagesData = await pagesRes.json()
        const pageItems: PageMeta[] = pagesData.items ?? pagesData.pages ?? []

        if (pageItems.length === 0) {
          if (!cancelled) {
            setError("No pages found")
            setLoading(false)
          }
          return
        }

        setPages(pageItems)

        if (!cancelled) {
          setSelectedPage(pageItems[0]!.pageNumber)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load")
          setLoading(false)
        }
      }
    }

    init()
    return () => {
      cancelled = true
    }
  }, [bookId])

  useEffect(() => {
    if (selectedPage !== null) {
      setCarouselIndex(0)
      fetchPageReview(selectedPage)
      setLoading(false)
    }
  }, [selectedPage])

  const handleApprove = async (translationId: string) => {
    setActionError(null)
    setSuccessMsg(null)
    try {
      await approveTranslation(translationId)
      setSuccessMsg("Translation approved successfully")
      if (selectedPage !== null) fetchPageReview(selectedPage)
      setTimeout(
        () => summaryRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
        100,
      )
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to approve")
    }
  }

  const handleReject = async (translationId: string) => {
    setActionError(null)
    setSuccessMsg(null)
    setRejecting((prev) => ({ ...prev, [translationId]: true }))
    try {
      const reason = rejectReasons[translationId] || undefined
      await rejectTranslation(translationId, reason)
      setSuccessMsg("Translation rejected")
      if (selectedPage !== null) fetchPageReview(selectedPage)
      setTimeout(
        () => summaryRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
        100,
      )
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to reject")
    } finally {
      setRejecting((prev) => ({ ...prev, [translationId]: false }))
    }
  }

  const handleCopyFromTranslator = (text: string, transId: string, secId: string) => {
    setOverrideText(text)
    setSourceTranslationId(transId)
    setOverrideSectionId(secId)
  }

  const handleOverrideSubmit = async () => {
    if (!overrideSectionId || !overrideText.trim()) return
    setActionError(null)
    setSuccessMsg(null)
    setSubmitting(true)
    try {
      await editorOverrideTranslation(overrideSectionId, {
        translatedText: overrideText.trim(),
        sourceTranslationId,
      })
      setSuccessMsg("Editor override submitted and auto-approved")
      setOverrideText("")
      setSourceTranslationId(undefined)
      setOverrideSectionId(null)
      if (selectedPage !== null) fetchPageReview(selectedPage)
      setTimeout(
        () => summaryRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
        100,
      )
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to submit override")
    } finally {
      setSubmitting(false)
    }
  }

  const handleFinishPage = async () => {
    if (!bookId || selectedPage === null) return
    setFinishing(true)
    setActionError(null)
    try {
      const res = await apiFetchBrowser(
        `/api/books/${bookId}/pages/${selectedPage}/finish-review`,
        { method: "POST" },
      )
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || "Failed to finish page")
      }
      setSuccessMsg("Page review completed!")
      if (selectedPage !== null) fetchPageReview(selectedPage)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to finish page")
    } finally {
      setFinishing(false)
    }
  }

  const getZoom = (key: string) => zoom[key] ?? 100

  const handleZoomIn = (key: string) =>
    setZoom((prev) => ({ ...prev, [key]: Math.min((prev[key] ?? 100) + 20, 300) }))

  const handleZoomOut = (key: string) =>
    setZoom((prev) => ({ ...prev, [key]: Math.max((prev[key] ?? 100) - 20, 40) }))

  const handleZoomReset = (key: string) => setZoom((prev) => ({ ...prev, [key]: 100 }))

  const summaryRef = useRef<HTMLDivElement>(null)
  const dragStartRef = useRef({ x: 0, y: 0, scrollLeft: 0, scrollTop: 0 })
  const [isDragging, setIsDragging] = useState(false)

  const handleImageMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return
    const el = e.currentTarget as HTMLDivElement
    setIsDragging(true)
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      scrollLeft: el.scrollLeft,
      scrollTop: el.scrollTop,
    }
    e.preventDefault()
  }, [])

  const handleImageMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging) return
      const el = e.currentTarget as HTMLDivElement
      const dx = e.clientX - dragStartRef.current.x
      const dy = e.clientY - dragStartRef.current.y
      el.scrollLeft = dragStartRef.current.scrollLeft - dx
      el.scrollTop = dragStartRef.current.scrollTop - dy
    },
    [isDragging],
  )

  const handleImageMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  useEffect(() => {
    if (isDragging) {
      const handleGlobalUp = () => setIsDragging(false)
      window.addEventListener("mouseup", handleGlobalUp)
      return () => window.removeEventListener("mouseup", handleGlobalUp)
    }
  }, [isDragging])

  if (loading) {
    return (
      <div style={styles.page}>
        <div style={styles.loading}>
          <div className="spinner" style={styles.spinner} />
          <span>Loading review data...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.page}>
        <div style={styles.errorBox}>
          <div style={styles.errorTitle}>Error</div>
          <div>{error}</div>
          <Link href={`/books/${bookId}`} style={styles.backLink}>
            ← Back to book console
          </Link>
        </div>
      </div>
    )
  }

  if (!book) {
    return (
      <div style={styles.page}>
        <div style={styles.errorBox}>
          <div>Book not found</div>
          <Link href="/books" style={styles.backLink}>
            ← Back to books
          </Link>
        </div>
      </div>
    )
  }

  const sections = reviewData?.sections ?? []
  const allApproved =
    sections.length > 0 && sections.every((s) => s.translations.some((t) => t.isApproved))

  return (
    <div style={styles.page}>
      <Link href={`/books/${bookId}`} style={styles.backLink}>
        ← Back to book console
      </Link>

      <div style={styles.header}>
        <h1 style={styles.title}>Translation Review</h1>
        <div style={styles.meta}>
          <span>{book.title}</span>
          <span style={styles.dot}>·</span>
          <span>{book.author}</span>
        </div>
      </div>

      <div style={styles.controls}>
        <div style={styles.pagination}>
          <button
            style={{
              ...styles.pageBtn,
              opacity: selectedPage !== null && selectedPage > 1 ? 1 : 0.4,
            }}
            disabled={selectedPage === null || selectedPage <= 1}
            onClick={() => selectedPage !== null && setSelectedPage(selectedPage - 1)}
          >
            ‹
          </button>
          {selectedPage !== null &&
            buildPageNumbers(pages, selectedPage).map((item, i) =>
              item === "..." ? (
                <span key={`e${i}`} style={styles.pageEllipsis}>
                  …
                </span>
              ) : (
                <button
                  key={item}
                  style={{
                    ...styles.pageBtn,
                    ...(item === selectedPage ? styles.pageBtnActive : {}),
                  }}
                  onClick={() => setSelectedPage(item)}
                >
                  {item}
                </button>
              ),
            )}
          <button
            style={{
              ...styles.pageBtn,
              opacity: selectedPage !== null && selectedPage < pages.length ? 1 : 0.4,
            }}
            disabled={selectedPage === null || selectedPage >= pages.length}
            onClick={() => selectedPage !== null && setSelectedPage(selectedPage + 1)}
          >
            ›
          </button>
        </div>
      </div>

      {successMsg && <div style={styles.successMsg}>{successMsg}</div>}
      {actionError && <div style={styles.errorMsg}>{actionError}</div>}

      {pageLoading && (
        <div style={styles.loading}>
          <div className="spinner" style={styles.spinner} />
          <span>Loading page...</span>
        </div>
      )}

      {!pageLoading && reviewData && (
        <>
          {reviewData.page.imageUrl && (
            <div style={styles.pageImageCard}>
              <div style={styles.imageCardHeader}>
                <span style={styles.imageLabel}>Page {reviewData.page.pageNumber}</span>
                <span
                  style={
                    reviewData.page.reviewed ? styles.reviewedBadge : styles.pendingReviewBadge
                  }
                >
                  {reviewData.page.reviewed ? "✓ Page reviewed" : "Pending review"}
                </span>
              </div>
              <div
                style={{
                  ...styles.imageScrollWrap,
                  cursor: isDragging ? "grabbing" : "grab",
                }}
                onMouseDown={handleImageMouseDown}
                onMouseMove={handleImageMouseMove}
                onMouseUp={handleImageMouseUp}
              >
                <div style={styles.imageInner}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={reviewData.page.imageUrl}
                    alt={`Page ${reviewData.page.pageNumber}`}
                    draggable={false}
                    style={{
                      width: `${getZoom("page")}%`,
                      height: "auto",
                      display: "block",
                    }}
                  />
                </div>
              </div>
              <div style={styles.zoomControls}>
                <button
                  style={styles.zoomBtn}
                  onClick={() => handleZoomOut("page")}
                  aria-label="Zoom out"
                >
                  −
                </button>
                <span style={{ fontSize: 13, color: "var(--foreground)" }}>{getZoom("page")}%</span>
                <button
                  style={styles.zoomBtn}
                  onClick={() => handleZoomIn("page")}
                  aria-label="Zoom in"
                >
                  +
                </button>
                <button
                  style={styles.zoomBtn}
                  onClick={() => handleZoomReset("page")}
                  aria-label="Reset zoom"
                >
                  ⟳
                </button>
              </div>
            </div>
          )}

          {sections.length === 0 && <div style={styles.infoBox}>No sections on this page.</div>}

          {sections.length > 0 && (
            <>
              <div ref={summaryRef} style={styles.summaryCard}>
                <div style={styles.summaryTitle}>Section Status</div>
                {sections.length === 0 ? (
                  <div style={styles.summaryEmpty}>No sections on this page.</div>
                ) : (
                  <div style={styles.summaryList}>
                    {sections.map((sec, i) => {
                      const approved = sec.translations.filter((t) => t.isApproved)
                      const rejected = sec.translations.some((t) => t.rejected)
                      const statusLabel =
                        approved.length > 0 ? "Approved" : rejected ? "Rejected" : "Pending"
                      const statusStyle =
                        approved.length > 0
                          ? styles.statusApproved
                          : rejected
                            ? styles.statusRejected
                            : styles.statusPending
                      return (
                        <button
                          key={sec.id}
                          type="button"
                          onClick={() => setCarouselIndex(i)}
                          style={{
                            ...styles.summaryItem,
                            ...(i === carouselIndex ? styles.summaryItemActive : {}),
                          }}
                        >
                          <span style={styles.summarySectionNum}>S{sec.sectionOrder + 1}</span>
                          <div style={styles.summaryTexts}>
                            {approved.length > 0 ? (
                              approved.map((t) => (
                                <span key={t.id} style={styles.summaryTransText}>
                                  {t.translatedText}
                                </span>
                              ))
                            ) : (
                              <span style={styles.summaryTransTextMuted}>
                                No approved translation yet
                              </span>
                            )}
                          </div>
                          <span style={{ ...styles.sectionStatus, ...statusStyle, flexShrink: 0 }}>
                            {statusLabel}
                          </span>
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>

              {carouselIndex < sections.length && (
                <SectionCarouselView
                  sec={sections[carouselIndex]!}
                  index={carouselIndex}
                  total={sections.length}
                  bookId={bookId ?? ""}
                  zoom={zoom}
                  onZoomIn={handleZoomIn}
                  onZoomOut={handleZoomOut}
                  onZoomReset={handleZoomReset}
                  isDragging={isDragging}
                  onImageMouseDown={handleImageMouseDown}
                  onImageMouseMove={handleImageMouseMove}
                  onImageMouseUp={handleImageMouseUp}
                  overrideSectionId={overrideSectionId}
                  overrideText={overrideText}
                  submitting={submitting}
                  sourceTranslationId={sourceTranslationId}
                  rejectReasons={rejectReasons}
                  rejecting={rejecting}
                  onGoTo={(i) => setCarouselIndex(i)}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  onCopyFromTranslator={handleCopyFromTranslator}
                  onRejectReasonChange={(id, value) =>
                    setRejectReasons((prev) => ({ ...prev, [id]: value }))
                  }
                  onOverrideTextChange={(secId, text) => {
                    setOverrideSectionId(secId)
                    setOverrideText(text)
                  }}
                  onOverrideFocus={(secId) => {
                    if (overrideSectionId !== secId) {
                      setOverrideSectionId(secId)
                      setOverrideText("")
                      setSourceTranslationId(undefined)
                    }
                  }}
                  onOverrideSubmit={handleOverrideSubmit}
                />
              )}
            </>
          )}

          {sections.length > 0 && (
            <div style={styles.finishRow}>
              <button
                style={{
                  ...styles.btnFinish,
                  opacity: allApproved && !finishing ? 1 : 0.5,
                }}
                disabled={!allApproved || finishing}
                onClick={handleFinishPage}
              >
                {finishing
                  ? "Finishing..."
                  : allApproved
                    ? "✓ Finish Page Review"
                    : "Approve all sections first"}
              </button>
            </div>
          )}
        </>
      )}

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

export default TranslationReviewPage

function buildPageNumbers(pages: PageMeta[], current: number): (number | "...")[] {
  const total = pages.length
  if (total <= 7) return pages.map((p) => p.pageNumber)

  const result: (number | "...")[] = []
  result.push(1)

  if (current > 3) result.push("...")

  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
    result.push(i)
  }

  if (current < total - 2) result.push("...")

  result.push(total)
  return result
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 32, maxWidth: 960, margin: "0 auto" },
  backLink: { color: "var(--primary)", fontSize: 13, marginBottom: 16, display: "inline-block" },
  header: { marginBottom: 20 },
  title: { fontSize: 26, fontWeight: 700, marginBottom: 4 },
  meta: { display: "flex", alignItems: "center", gap: 8, fontSize: 14, color: "var(--muted)" },
  dot: { color: "var(--border)" },
  controls: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 16,
    marginBottom: 20,
    padding: "12px 16px",
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 8,
  },
  controlGroup: { display: "flex", alignItems: "center", gap: 8 },
  controlLabel: { fontSize: 13, fontWeight: 600, color: "var(--muted)" },
  pagination: {
    display: "flex",
    alignItems: "center",
    gap: 4,
  },
  pageBtn: {
    minWidth: 32,
    height: 32,
    padding: "0 6px",
    borderWidth: 1,
    borderStyle: "solid",
    borderColor: "var(--border)",
    borderRadius: 6,
    fontSize: 14,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  pageBtnActive: {
    background: "var(--primary)",
    color: "#fff",
    borderColor: "var(--primary)",
    fontWeight: 700,
  },
  pageEllipsis: {
    padding: "0 4px",
    color: "var(--muted)",
    fontSize: 14,
  },
  toggleLabel: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 13,
    fontWeight: 500,
    color: "var(--foreground)",
    cursor: "pointer",
  },
  pageImageCard: {
    border: "1px solid var(--border)",
    borderRadius: 8,
    overflow: "hidden",
    background: "var(--surface)",
    marginBottom: 20,
  },
  imageCardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px 14px",
    borderBottom: "1px solid var(--border)",
  },
  imageLabel: { fontSize: 13, fontWeight: 600, color: "var(--muted)" },
  imageScrollWrap: {
    overflow: "hidden",
    maxHeight: 600,
    borderBottom: "1px solid var(--border)",
    background: "var(--background)",
    userSelect: "none",
    touchAction: "none",
  },
  secImageScrollWrap: {
    overflow: "hidden",
    maxHeight: 400,
    marginBottom: 8,
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
    padding: "8px 12px",
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
  summaryCard: {
    border: "1px solid #fff",
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
    background: "var(--surface)",
  },
  summaryTitle: { fontSize: 14, fontWeight: 700, color: "var(--foreground)", marginBottom: 12 },
  summaryEmpty: { fontSize: 13, color: "var(--muted)", fontStyle: "italic" },
  summaryList: { display: "flex", flexDirection: "column", gap: 10 },
  summaryItem: {
    display: "flex",
    gap: 10,
    alignItems: "flex-start",
    width: "100%",
    textAlign: "left" as const,
    background: "transparent",
    border: "1px solid transparent",
    borderRadius: 6,
    padding: 6,
    cursor: "pointer",
    font: "inherit",
    color: "inherit",
  },
  summaryItemActive: {
    background: "var(--background)",
    border: "1px solid var(--border)",
  },
  summaryTransTextMuted: {
    fontSize: 13,
    lineHeight: 1.5,
    color: "var(--muted)",
    fontStyle: "italic" as const,
  },
  summarySectionNum: {
    fontSize: 11,
    fontWeight: 700,
    color: "#fff",
    background: "var(--primary)",
    padding: "2px 6px",
    borderRadius: 4,
    whiteSpace: "nowrap",
    minWidth: 28,
    textAlign: "center" as const,
    marginTop: 2,
  },
  summaryTexts: { display: "flex", flexDirection: "column", gap: 4, flex: 1, minWidth: 0 },
  summaryTransText: {
    fontSize: 13,
    lineHeight: 1.5,
    color: "var(--foreground)",
    whiteSpace: "pre-wrap" as const,
  },
  carouselSection: { marginBottom: 20 },
  carouselNav: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 16,
    padding: "10px 14px",
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 8,
  },
  carouselBtn: {
    padding: "6px 14px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    fontSize: 13,
    cursor: "pointer",
  },
  translateBtn: {
    padding: "6px 14px",
    border: "1px solid var(--primary)",
    borderRadius: 6,
    background: "var(--primary)",
    color: "#fff",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    marginLeft: 8,
  },
  carouselDots: {
    display: "flex",
    gap: 6,
    alignItems: "center",
  },
  carouselDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    border: "none",
    cursor: "pointer",
    padding: 0,
  },
  carouselLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--muted)",
    whiteSpace: "nowrap" as const,
  },
  sectionCard: {
    border: "1px solid var(--border)",
    borderRadius: 8,
    padding: 20,
    background: "var(--surface)",
  },
  sectionHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  sectionTitle: { fontSize: 16, fontWeight: 700, color: "var(--foreground)" },
  sectionStatus: {
    fontSize: 11,
    fontWeight: 600,
    padding: "2px 8px",
    borderRadius: 4,
    textTransform: "uppercase" as const,
    letterSpacing: "0.04em",
  },
  statusPending: { background: "#fef3c7", color: "#92400e" },
  statusApproved: { background: "#dcfce7", color: "#166534" },
  statusRejected: { background: "#fef2f2", color: "#991b1b" },
  fieldCard: {
    border: "1px solid #fff",
    borderRadius: 6,
    padding: 12,
    marginBottom: 10,
    background: "var(--background)",
  },
  fieldLabel: {
    fontSize: 11,
    fontWeight: 600,
    textTransform: "uppercase" as const,
    color: "var(--muted)",
    marginBottom: 6,
    letterSpacing: "0.04em",
  },
  fieldValue: {
    fontSize: 14,
    lineHeight: 1.6,
    whiteSpace: "pre-wrap" as const,
    color: "var(--foreground)",
  },
  translationsSection: { marginTop: 16, borderTop: "1px solid var(--border)", paddingTop: 16 },
  translationsLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--muted)",
    marginBottom: 12,
    textTransform: "uppercase" as const,
    letterSpacing: "0.04em",
  },
  noTrans: {
    fontSize: 13,
    color: "var(--muted)",
    padding: 12,
    textAlign: "center" as const,
    border: "1px dashed var(--border)",
    borderRadius: 6,
  },
  transCard: {
    border: "1px solid var(--border)",
    borderRadius: 6,
    padding: 14,
    marginBottom: 10,
    background: "var(--background)",
  },
  transHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  transName: { fontSize: 13, fontWeight: 600, color: "var(--foreground)" },
  transDate: { fontSize: 11, color: "var(--muted)" },
  badge: {
    fontSize: 10,
    fontWeight: 600,
    padding: "2px 6px",
    borderRadius: 3,
    textTransform: "uppercase" as const,
    letterSpacing: "0.03em",
  },
  badgePending: { background: "#fef3c7", color: "#92400e" },
  badgeApproved: { background: "#dcfce7", color: "#166534" },
  badgeRejected: { background: "#fef2f2", color: "#991b1b" },
  transText: { fontSize: 14, lineHeight: 1.6, whiteSpace: "pre-wrap" as const, marginBottom: 8 },
  transExact: {
    fontSize: 12,
    color: "var(--foreground)",
    marginBottom: 8,
    padding: "6px 10px",
    background: "var(--background)",
    borderRadius: 4,
    border: "1px solid var(--border)",
  },
  transExactLabel: { fontWeight: 600 },
  transActions: { display: "flex", gap: 6, marginBottom: 8 },
  btnApprove: {
    padding: "6px 16px",
    background: "#166534",
    color: "#fff",
    border: "none",
    borderRadius: 4,
    fontSize: 12,
    fontWeight: 600,
    cursor: "pointer",
  },
  btnReject: {
    padding: "6px 16px",
    background: "#dc2626",
    color: "#fff",
    border: "none",
    borderRadius: 4,
    fontSize: 12,
    fontWeight: 600,
    cursor: "pointer",
  },
  btnCopy: {
    padding: "6px 12px",
    border: "1px solid var(--border)",
    borderRadius: 4,
    background: "var(--background)",
    color: "var(--foreground)",
    fontSize: 12,
    cursor: "pointer",
  },
  rejectRow: { display: "flex", gap: 6, alignItems: "flex-start" },
  rejectTextarea: {
    flex: 1,
    padding: "6px 10px",
    border: "1px solid var(--border)",
    borderRadius: 4,
    fontSize: 12,
    resize: "vertical" as const,
    background: "var(--background)",
    color: "var(--foreground)",
  },
  overrideCard: {
    marginTop: 16,
    border: "2px solid var(--primary)",
    borderRadius: 8,
    padding: 16,
    background: "var(--surface)",
  },
  cardTitle: { fontSize: 14, fontWeight: 700, marginBottom: 6, color: "var(--foreground)" },
  overrideHint: { fontSize: 12, color: "var(--muted)", marginBottom: 10, lineHeight: 1.5 },
  overrideTextarea: {
    width: "100%",
    padding: 10,
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 13,
    lineHeight: 1.5,
    resize: "vertical" as const,
    background: "var(--background)",
    color: "var(--foreground)",
    marginBottom: 10,
    fontFamily: "inherit",
  },
  overrideAction: { display: "flex", justifyContent: "flex-end" },
  btnSubmit: {
    padding: "8px 20px",
    background: "var(--primary)",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
  },
  finishRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 24,
    borderTop: "1px solid var(--border)",
    marginTop: 8,
  },
  btnFinish: {
    padding: "12px 32px",
    background: "#166534",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 15,
    fontWeight: 700,
    cursor: "pointer",
  },
  reviewedBadge: {
    fontSize: 13,
    fontWeight: 600,
    color: "#166534",
    padding: "6px 14px",
    background: "#dcfce7",
    borderRadius: 6,
  },
  pendingReviewBadge: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--muted)",
    padding: "6px 14px",
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 6,
  },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 48,
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
  tableWrapper: {
    overflowX: "auto",
    border: "1px solid var(--border)",
    borderRadius: 6,
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: 13,
  },
  th: {
    textAlign: "left",
    padding: "6px 10px",
    borderBottom: "1px solid var(--border)",
    background: "var(--background)",
    fontWeight: 600,
    whiteSpace: "nowrap",
  },
  td: {
    padding: "6px 10px",
    borderBottom: "1px solid var(--border)",
    verticalAlign: "top",
  },
  successMsg: {
    padding: "10px 14px",
    background: "#dcfce7",
    color: "#166534",
    borderRadius: 6,
    fontSize: 13,
    marginBottom: 16,
  },
  errorMsg: {
    padding: "10px 14px",
    background: "#fef2f2",
    color: "#991b1b",
    borderRadius: 6,
    fontSize: 13,
    marginBottom: 16,
  },
  errorBox: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 12,
    padding: 48,
    color: "var(--muted)",
  },
  errorTitle: { fontSize: 18, fontWeight: 600, color: "var(--foreground)" },
  infoBox: {
    padding: 24,
    textAlign: "center" as const,
    color: "var(--muted)",
    fontSize: 14,
    border: "1px dashed var(--border)",
    borderRadius: 8,
    marginBottom: 20,
  },
}
