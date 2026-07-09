"use client"

import { useEffect, useState } from "react"
import { apiFetchBrowser } from "@/lib/apiClientBrowser"
import type { TranslationStatsResponse, TranslatorStatsResponse } from "@/lib/api/translations"
import { SectionProgressBar } from "@/components/SectionProgressBar"
import { TranslatorStatsRow } from "./TranslatorStatsRow"

interface BookProgressHeaderProps {
  bookId: string | null
  refreshSignal?: number
}

export const BookProgressHeader = ({ bookId, refreshSignal = 0 }: BookProgressHeaderProps) => {
  const [stats, setStats] = useState<TranslationStatsResponse | null>(null)
  const [translatorStats, setTranslatorStats] = useState<TranslatorStatsResponse[]>([])
  const [expanded, setExpanded] = useState(false)
  const [expandedTranslator, setExpandedTranslator] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!bookId) return

    const fetchStats = async () => {
      try {
        const statsRes = await apiFetchBrowser(`/api/books/${bookId}/stats`)
        if (!statsRes.ok) throw new Error("Failed to fetch stats")
        setStats(await statsRes.json())
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error loading stats")
      }
    }

    // On the initial mount (refreshSignal === 0) fetch right away. A later
    // refreshSignal bump means a translation was just submitted and its stats
    // recompute runs asynchronously on a worker, so give it a moment to land
    // before refetching, or we'd just redisplay the pre-submit numbers.
    const delay = refreshSignal > 0 ? 1500 : 0
    const kickoff = setTimeout(fetchStats, delay)
    const interval = setInterval(fetchStats, 30000)
    return () => {
      clearTimeout(kickoff)
      clearInterval(interval)
    }
  }, [bookId, refreshSignal])

  useEffect(() => {
    if (!bookId || !expanded) return

    const fetchTranslatorStats = async () => {
      const res = await apiFetchBrowser(`/api/books/${bookId}/translators/stats`)
      if (res.ok) setTranslatorStats(await res.json())
    }

    fetchTranslatorStats()
    const interval = setInterval(fetchTranslatorStats, 30000)
    return () => clearInterval(interval)
  }, [bookId, expanded, refreshSignal])

  if (error) {
    return <div style={styles.error}>Failed to load progress</div>
  }

  if (!stats) return null

  return (
    <div style={styles.container}>
      <div style={styles.strip}>
        <SectionProgressBar
          approved={stats.translatedSections}
          inProgress={stats.inProgressSections}
          pending={stats.pendingSections}
          total={stats.totalSections}
          size="md"
          showLabel
        />
        <div style={styles.counts}>
          <span style={styles.countItem}>✅ {stats.translatedSections}</span>
          <span style={styles.countItem}>🔄 {stats.inProgressSections}</span>
          <span style={styles.countItem}>⏳ {stats.pendingSections}</span>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          style={styles.toggle}
          aria-expanded={expanded}
        >
          {expanded ? "Hide details ▴" : "View details ▾"}
        </button>
      </div>

      {expanded && (
        <div style={styles.details}>
          {Object.keys(stats.byLanguage).length > 0 && (
            <div style={styles.card}>
              <div style={styles.cardTitle}>Per-Language Breakdown</div>
              <div style={styles.languageGrid}>
                {Object.entries(stats.byLanguage).map(([lang, langStats]) => (
                  <div key={lang} style={styles.languageCard}>
                    <div style={styles.langName}>
                      {lang === "si" ? "Sinhala" : lang === "ta" ? "Tamil" : lang}
                    </div>
                    <div style={styles.langBar}>
                      <div style={{ ...styles.langBarFill, width: `${langStats.percent}%` }} />
                    </div>
                    <div style={styles.langStats}>
                      {langStats.percent}% ({langStats.translated}/{langStats.total})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {stats.byPage.length > 0 && (
            <div style={styles.card}>
              <div style={styles.cardTitle}>Per-Page Breakdown</div>
              <div style={styles.pageGrid}>
                {stats.byPage.map((pg) => {
                  let color = "#E5E7EB"
                  if (pg.percent === 100) color = "#22C55E"
                  else if (pg.percent > 0) color = "#EAB308"

                  return (
                    <div key={pg.pageNumber} style={styles.pageCell}>
                      <div
                        style={{ ...styles.pageIndicator, background: color }}
                        aria-label={`Page ${pg.pageNumber}: ${pg.percent}% complete`}
                      />
                      <div style={styles.pageLabel}>{pg.pageNumber}</div>
                      <div style={styles.pagePercent}>{pg.percent}%</div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {translatorStats.length > 0 && (
            <div style={styles.card}>
              <div style={styles.cardTitle}>Translator Performance</div>
              <div style={styles.tableWrapper}>
                <div style={styles.tableHeader}>
                  <div>Name</div>
                  <div>Assigned</div>
                  <div>Approved</div>
                  <div>Rejected</div>
                  <div>Rate</div>
                  <div>Avg Time</div>
                  <div style={{ fontSize: 11 }}>Last Active</div>
                </div>
                {translatorStats.map((stat) => (
                  <TranslatorStatsRow
                    key={stat.userId}
                    stat={stat}
                    isExpanded={expandedTranslator === stat.userId}
                    onToggle={() =>
                      setExpandedTranslator(expandedTranslator === stat.userId ? null : stat.userId)
                    }
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginBottom: 24,
  },
  strip: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    flexWrap: "wrap",
    padding: "12px 16px",
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
  },
  counts: {
    display: "flex",
    gap: 12,
    fontSize: 13,
    color: "var(--foreground)",
  },
  countItem: {
    whiteSpace: "nowrap",
  },
  toggle: {
    marginLeft: "auto",
    padding: "6px 12px",
    background: "none",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 13,
    fontWeight: 600,
    color: "var(--primary)",
    cursor: "pointer",
  },
  error: {
    fontSize: 13,
    color: "var(--muted)",
    marginBottom: 16,
  },
  details: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
    marginTop: 16,
  },
  card: {
    padding: 20,
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 600,
    marginBottom: 16,
    color: "var(--foreground)",
  },
  languageGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
    gap: 12,
  },
  languageCard: {
    padding: 12,
    border: "1px solid var(--border)",
    borderRadius: 6,
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  langName: {
    fontSize: 14,
    fontWeight: 600,
  },
  langBar: {
    height: 8,
    background: "var(--border)",
    borderRadius: 4,
    overflow: "hidden",
  },
  langBarFill: {
    height: "100%",
    background: "var(--primary)",
    borderRadius: 4,
    transition: "width 0.6s ease-out",
  },
  langStats: {
    fontSize: 12,
    color: "var(--muted)",
  },
  pageGrid: {
    display: "flex",
    gap: 8,
    flexWrap: "wrap",
  },
  pageCell: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 4,
    minWidth: 40,
  },
  pageIndicator: {
    width: 32,
    height: 32,
    borderRadius: 4,
  },
  pageLabel: {
    fontSize: 11,
    fontWeight: 600,
  },
  pagePercent: {
    fontSize: 10,
    color: "var(--muted)",
  },
  tableWrapper: {
    overflowX: "auto",
  },
  tableHeader: {
    display: "grid",
    gridTemplateColumns: "1.5fr repeat(5, 1fr) 1fr",
    padding: "10px 12px",
    borderBottom: "2px solid var(--border)",
    fontSize: 12,
    fontWeight: 600,
    color: "var(--muted)",
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
  },
}
