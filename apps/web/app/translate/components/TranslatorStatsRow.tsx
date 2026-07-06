"use client"

import type { TranslatorStatsResponse } from "@/lib/api/translations"

interface TranslatorStatsRowProps {
  stat: TranslatorStatsResponse
  isExpanded: boolean
  onToggle: () => void
}

export const TranslatorStatsRow = ({ stat, isExpanded, onToggle }: TranslatorStatsRowProps) => {
  const rateText = stat.approvalRate !== null ? `${stat.approvalRate}%` : "—"
  const avgTimeText = stat.avgTurnaroundHours !== null ? `${stat.avgTurnaroundHours}h` : "—"
  const lastActive = stat.lastActiveAt
    ? new Date(stat.lastActiveAt).toLocaleDateString("en-US", { month: "short", day: "numeric" })
    : "—"

  return (
    <div>
      <button
        style={styles.row}
        onClick={onToggle}
        type="button"
        aria-expanded={isExpanded}
      >
        <div style={styles.nameCell}>{stat.userName}</div>
        <div style={styles.cell}>{stat.totalAssigned}</div>
        <div style={styles.cell}>{stat.approvedCount}</div>
        <div style={styles.cell}>{stat.rejectedCount}</div>
        <div style={{ ...styles.cell, fontWeight: 600 }}>{rateText}</div>
        <div style={styles.cell}>{avgTimeText}</div>
        <div style={styles.cellSmall}>{lastActive}</div>
      </button>
      {isExpanded && (
        <div style={styles.expanded}>
          <div style={styles.expandedHeader}>
            {stat.userName} — Recent Activity
          </div>
          <div style={styles.emptyActivity}>No recent activity to display</div>
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  row: {
    display: "grid",
    gridTemplateColumns: "1.5fr repeat(5, 1fr) 1fr",
    alignItems: "center",
    width: "100%",
    padding: "10px 12px",
    borderBottom: "1px solid var(--border)",
    background: "var(--background)",
    cursor: "pointer",
    textAlign: "left",
    fontSize: 13,
  },
  nameCell: {
    fontWeight: 600,
    color: "var(--foreground)",
  },
  cell: {
    color: "var(--foreground)",
  },
  cellSmall: {
    color: "var(--muted)",
    fontSize: 12,
  },
  expanded: {
    padding: "12px 16px",
    borderBottom: "1px solid var(--border)",
    background: "var(--surface)",
  },
  expandedHeader: {
    fontSize: 13,
    fontWeight: 600,
    marginBottom: 8,
    color: "var(--foreground)",
  },
  emptyActivity: {
    fontSize: 13,
    color: "var(--muted)",
    fontStyle: "italic",
  },
}
