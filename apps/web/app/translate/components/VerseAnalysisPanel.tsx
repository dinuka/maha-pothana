"use client"

interface VerseAnalysisPanelProps {
  wordByWordMeaning: string | null
  fullMeaning: string | null
  simplifiedMeaning: string | null
  loading: boolean
  error: string | null
  onGenerate: () => void
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
    return <div style={styles.plainText}>{markdown}</div>
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

export const VerseAnalysisPanel = ({
  wordByWordMeaning,
  fullMeaning,
  simplifiedMeaning,
  loading,
  error,
  onGenerate,
}: VerseAnalysisPanelProps) => {
  const hasAnalysis = wordByWordMeaning || fullMeaning || simplifiedMeaning

  return (
    <div style={styles.panel}>
      <div style={styles.panelHeader}>
        <span>📖</span>
        <span style={styles.panelTitle}>Verse Analysis (reference only)</span>
        <button
          onClick={onGenerate}
          disabled={loading}
          style={hasAnalysis ? styles.regenerateBtn : styles.generateBtn}
        >
          {loading ? "Analyzing..." : hasAnalysis ? "Regenerate" : "Generate with AI"}
        </button>
      </div>

      {loading ? (
        <div style={styles.loadingPanel}>
          <div style={styles.miniSpinner} />
          <span>Analyzing verse...</span>
        </div>
      ) : error ? (
        <div style={styles.errorPanel}>{error}</div>
      ) : hasAnalysis ? (
        <div style={styles.sections}>
          {wordByWordMeaning && (
            <div style={styles.section}>
              <div style={styles.sectionLabel}>Word-by-word meaning</div>
              <MarkdownTable markdown={wordByWordMeaning} />
            </div>
          )}
          {fullMeaning && (
            <div style={styles.section}>
              <div style={styles.sectionLabel}>Full meaning</div>
              <div style={styles.plainText}>{fullMeaning}</div>
            </div>
          )}
          {simplifiedMeaning && (
            <div style={styles.section}>
              <div style={styles.sectionLabel}>Simplified meaning</div>
              <div style={styles.plainText}>{simplifiedMeaning}</div>
            </div>
          )}
        </div>
      ) : (
        <div style={styles.emptyPanel}>
          Generate a word-by-word breakdown and meaning to help with your translation.
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  panel: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    padding: 12,
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
  },
  panelHeader: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 13,
    fontWeight: 600,
    color: "var(--muted)",
  },
  panelTitle: {
    fontSize: 13,
    fontWeight: 600,
  },
  generateBtn: {
    marginLeft: "auto",
    padding: "6px 14px",
    border: "none",
    borderRadius: 6,
    background: "var(--primary)",
    color: "#fff",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 600,
  },
  regenerateBtn: {
    marginLeft: "auto",
    padding: "6px 14px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 13,
  },
  loadingPanel: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    padding: 24,
    color: "var(--muted)",
    fontSize: 13,
  },
  miniSpinner: {
    width: 14,
    height: 14,
    border: "2px solid var(--border)",
    borderTopColor: "var(--primary)",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  errorPanel: {
    padding: 16,
    color: "#DC2626",
    fontSize: 13,
    textAlign: "center",
  },
  emptyPanel: {
    padding: 16,
    color: "var(--muted)",
    fontSize: 13,
    fontStyle: "italic",
    textAlign: "center",
  },
  sections: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  section: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: 600,
    color: "var(--muted)",
  },
  plainText: {
    fontSize: 14,
    lineHeight: 1.6,
    padding: 8,
    background: "var(--background)",
    borderRadius: 6,
    whiteSpace: "pre-wrap",
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
}
