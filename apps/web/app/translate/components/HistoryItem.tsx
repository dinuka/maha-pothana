"use client"

import type { TranslationHistoryItem } from "@/lib/api/translations"

interface HistoryItemProps {
  item: TranslationHistoryItem
  onClick?: (sectionId: string) => void
}

const statusConfig = {
  APPROVED: { color: "#16A34A", bg: "#DCFCE7", label: "APPROVED", icon: "✅" },
  PENDING: { color: "#D97706", bg: "#FEF3C7", label: "PENDING", icon: "⏳" },
  REJECTED: { color: "#DC2626", bg: "#FEE2E2", label: "REJECTED", icon: "❌" },
  SUBMITTED: { color: "#2563EB", bg: "#DBEAFE", label: "SUBMITTED", icon: "⏳" },
}

export const HistoryItem = ({ item, onClick }: HistoryItemProps) => {
  const config = statusConfig[item.action] ?? statusConfig.SUBMITTED
  const snippet =
    item.translatedText.length > 80 ? `${item.translatedText.slice(0, 80)}...` : item.translatedText

  const formattedDate = new Date(item.createdAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })

  return (
    <button style={styles.container} onClick={() => onClick?.(item.sectionId)} type="button">
      <div style={styles.content}>
        <div style={styles.info}>
          <div style={styles.location}>
            Page {item.pageNumber}, Section {item.sectionOrder}
          </div>
          <div style={styles.snippet}>&ldquo;{snippet}&rdquo;</div>
          <div style={styles.meta}>
            <span
              style={{
                ...styles.badge,
                color: config.color,
                background: config.bg,
              }}
            >
              {config.icon} {config.label}
            </span>
            {item.performedByName && (
              <span style={styles.reviewer}>
                · {item.action === "SUBMITTED" ? "" : `Reviewed by ${item.performedByName}`}
              </span>
            )}
            <span style={styles.date}>· {formattedDate}</span>
          </div>
        </div>
      </div>
    </button>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "block",
    width: "100%",
    textAlign: "left",
    padding: 16,
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--background)",
    cursor: "pointer",
    transition: "border-color 0.15s",
  },
  content: {
    display: "flex",
    gap: 12,
    alignItems: "flex-start",
  },
  info: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  location: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--foreground)",
  },
  snippet: {
    fontSize: 14,
    color: "var(--muted)",
    lineHeight: 1.5,
  },
  meta: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 12,
    color: "var(--muted)",
    flexWrap: "wrap",
  },
  badge: {
    padding: "2px 8px",
    borderRadius: 4,
    fontSize: 11,
    fontWeight: 600,
  },
  reviewer: {
    fontSize: 12,
    color: "var(--muted)",
  },
  date: {
    fontSize: 12,
    color: "var(--muted)",
  },
}
