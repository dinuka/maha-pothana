"use client"

import type { TranslationFilters } from "@/hooks/useTranslationFilters"

interface TranslateFiltersProps {
  filters: TranslationFilters
  onFilterChange: (updates: Partial<TranslationFilters>) => void
  onClearFilters: () => void
  translateLanguages?: string[]
}

export const TranslateFilters = ({
  filters,
  onFilterChange,
  onClearFilters,
  translateLanguages = [],
}: TranslateFiltersProps) => {
  const hasActiveFilters =
    filters.language !== null || filters.page !== null || filters.status !== null

  return (
    <div style={styles.container}>
      <div style={styles.filters}>
        {translateLanguages.length > 1 && (
          <div style={styles.filterGroup}>
            <label htmlFor="lang-filter" style={styles.label}>Language</label>
            <select
              id="lang-filter"
              value={filters.language ?? ""}
              onChange={(e) => onFilterChange({ language: e.target.value || null })}
              style={styles.select}
            >
              <option value="">All</option>
              {translateLanguages.map((lang) => (
                <option key={lang} value={lang}>
                  {lang === "si" ? "Sinhala" : lang === "ta" ? "Tamil" : lang}
                </option>
              ))}
            </select>
          </div>
        )}

        <div style={styles.filterGroup}>
          <label htmlFor="page-filter" style={styles.label}>Page</label>
          <select
            id="page-filter"
            value={filters.page ?? ""}
            onChange={(e) => onFilterChange({ page: e.target.value ? Number(e.target.value) : null })}
            style={styles.select}
          >
            <option value="">All pages</option>
          </select>
        </div>

        <div style={styles.filterGroup}>
          <label htmlFor="status-filter" style={styles.label}>Status</label>
          <select
            id="status-filter"
            value={filters.status ?? ""}
            onChange={(e) => onFilterChange({ status: e.target.value || null })}
            style={styles.select}
          >
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="translated">Translated</option>
            <option value="approved">Approved</option>
          </select>
        </div>

        {hasActiveFilters && (
          <button onClick={onClearFilters} style={styles.clearBtn}>
            Clear
          </button>
        )}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "12px 0",
    borderBottom: "1px solid var(--border)",
  },
  filters: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    flexWrap: "wrap",
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
  clearBtn: {
    padding: "6px 12px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--muted)",
    fontSize: 13,
    cursor: "pointer",
  },
}
