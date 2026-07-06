"use client"

import { useEffect, useState } from "react"
import { apiFetchBrowser } from "@/lib/apiClientBrowser"
import type { TranslationStatsResponse, TranslatorStatsResponse } from "@/lib/api/translations"
import { TranslatorStatsRow } from "./components/TranslatorStatsRow"

interface StatsTabProps {
  bookId: string | null
}

export const StatsTab = ({ bookId }: StatsTabProps) => {
  const [stats, setStats] = useState<TranslationStatsResponse | null>(null)
  const [translatorStats, setTranslatorStats] = useState<TranslatorStatsResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedTranslator, setExpandedTranslator] = useState<string | null>(null)

  useEffect(() => {
    if (!bookId) return

    const fetchStats = async () => {
      setLoading(true)
      setError(null)
      try {
        const [statsRes, translatorRes] = await Promise.all([
          apiFetchBrowser(`/api/books/${bookId}/stats`),
          apiFetchBrowser(`/api/books/${bookId}/translators/stats`),
        ])

        if (!statsRes.ok) throw new Error("Failed to fetch stats")
        const statsData = await statsRes.json()
        setStats(statsData)

        if (translatorRes.ok) {
          const translatorData = await translatorRes.json()
          setTranslatorStats(translatorData)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error loading stats")
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [bookId])

  if (loading && !stats) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner} />
        <span>Loading statistics...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>⚠️</div>
        <div style={styles.emptyTitle}>Failed to load statistics</div>
        <button onClick={() => window.location.reload()} style={styles.retryBtn}>
          Retry
        </button>
      </div>
    )
  }

  if (!stats) return null

  const progressWidth = `${stats.translationPercent}%`

  return (
    <div style={styles.container}>
      {/* Progress Card */}
      <div style={styles.card}>
        <div style={styles.cardTitle}>Translation Progress</div>
        <div style={styles.progressBar}>
          <div
            style={{ ...styles.progressFill, width: progressWidth }}
            role="progressbar"
            aria-valuenow={stats.translationPercent}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Translation progress: ${stats.translationPercent}%`}
          />
        </div>
        <div style={styles.progressLabel}>{stats.translationPercent}%</div>
        <div style={styles.statNumbers}>
          <div style={styles.statItem}>
            <span style={styles.statIcon}>✅</span>
            <span>Approved: {stats.translatedSections}</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statIcon}>⏳</span>
            <span>Pending: {stats.pendingSections}</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statIcon}>🔄</span>
            <span>In Progress: {stats.inProgressSections}</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statIcon}>📊</span>
            <span>Total: {stats.totalSections}</span>
          </div>
        </div>
      </div>

      {/* Per-Language Breakdown */}
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
                  <div
                    style={{
                      ...styles.langBarFill,
                      width: `${langStats.percent}%`,
                    }}
                  />
                </div>
                <div style={styles.langStats}>
                  {langStats.percent}% ({langStats.translated}/{langStats.total})
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Per-Page Breakdown */}
      {stats.byPage.length > 0 && (
        <div style={styles.card}>
          <div style={styles.cardTitle}>Per-Page Breakdown</div>
          <div style={styles.pageGrid}>
            {stats.byPage.map((pg) => {
              let color = "#E5E7EB" // gray - not started
              if (pg.percent === 100) color = "#22C55E" // green
              else if (pg.percent > 0) color = "#EAB308" // yellow

              return (
                <div key={pg.pageNumber} style={styles.pageCell}>
                  <div
                    style={{
                      ...styles.pageIndicator,
                      background: color,
                    }}
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

      {/* Translator Performance */}
      {translatorStats.length > 0 && (
        <div style={styles.card}>
          <div style={styles.cardTitle}>Translator Performance</div>
          <div style={styles.tableWrapper}>
            <div style={styles.tableHeader}>
              <div style={styles.thCell}>Name</div>
              <div style={styles.thCell}>Assigned</div>
              <div style={styles.thCell}>Approved</div>
              <div style={styles.thCell}>Rejected</div>
              <div style={styles.thCell}>Rate</div>
              <div style={styles.thCell}>Avg Time</div>
              <div style={styles.thCellSmall}>Last Active</div>
            </div>
            {translatorStats.map((stat) => (
              <TranslatorStatsRow
                key={stat.userId}
                stat={stat}
                isExpanded={expandedTranslator === stat.userId}
                onToggle={() =>
                  setExpandedTranslator(
                    expandedTranslator === stat.userId ? null : stat.userId
                  )
                }
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
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
    marginBottom: 8,
    color: "var(--foreground)",
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
  progressBar: {
    height: 12,
    background: "var(--border)",
    borderRadius: 6,
    overflow: "hidden",
    marginBottom: 8,
  },
  progressFill: {
    height: "100%",
    background: "var(--primary)",
    borderRadius: 6,
    transition: "width 0.6s ease-out",
  },
  progressLabel: {
    fontSize: 24,
    fontWeight: 700,
    color: "var(--foreground)",
    marginBottom: 12,
  },
  statNumbers: {
    display: "flex",
    gap: 24,
    flexWrap: "wrap",
  },
  statItem: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 14,
    color: "var(--foreground)",
  },
  statIcon: {
    fontSize: 14,
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
  thCell: {},
  thCellSmall: {
    fontSize: 11,
  },
}
