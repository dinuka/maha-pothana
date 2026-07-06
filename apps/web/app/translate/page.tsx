"use client"

import { Suspense } from "react"
import { TranslateTab } from "./TranslateTab"
import { HistoryTab } from "./HistoryTab"
import { StatsTab } from "./StatsTab"
import { TranslateFilters } from "./TranslateFilters"
import { useTranslationFilters } from "@/hooks/useTranslationFilters"

const TABS = ["translate", "history", "stats"] as const
type Tab = (typeof TABS)[number]

const TranslatePageInner = () => {
  const { filters, setFilters, clearFilters } = useTranslationFilters()
  const activeTab = (TABS.includes(filters.tab as Tab) ? filters.tab : "translate") as Tab

  const handleTabChange = (tab: Tab) => {
    setFilters({ tab })
  }

  const handleSectionClick = (sectionId: string) => {
    window.location.href = `/translate?section=${sectionId}`
  }

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Translate</h1>

      <TranslateFilters
        filters={filters}
        onFilterChange={setFilters}
        onClearFilters={clearFilters}
      />

      {/* Tab Bar */}
      <div style={styles.tabBar} role="tablist" aria-label="Translation console tabs">
        <button
          role="tab"
          aria-selected={activeTab === "translate"}
          aria-controls="panel-translate"
          id="tab-translate"
          onClick={() => handleTabChange("translate")}
          style={{
            ...styles.tab,
            ...(activeTab === "translate" ? styles.tabActive : {}),
          }}
        >
          Translate
        </button>
        <button
          role="tab"
          aria-selected={activeTab === "history"}
          aria-controls="panel-history"
          id="tab-history"
          onClick={() => handleTabChange("history")}
          style={{
            ...styles.tab,
            ...(activeTab === "history" ? styles.tabActive : {}),
          }}
        >
          History
        </button>
        <button
          role="tab"
          aria-selected={activeTab === "stats"}
          aria-controls="panel-stats"
          id="tab-stats"
          onClick={() => handleTabChange("stats")}
          style={{
            ...styles.tab,
            ...(activeTab === "stats" ? styles.tabActive : {}),
          }}
        >
          Stats
        </button>
      </div>

      {/* Tab Content */}
      <div style={styles.content}>
        {activeTab === "translate" && (
          <div role="tabpanel" id="panel-translate" aria-labelledby="tab-translate">
            <TranslateTab filters={filters} isEditor={true} />
          </div>
        )}
        {activeTab === "history" && (
          <div role="tabpanel" id="panel-history" aria-labelledby="tab-history">
            <HistoryTab filters={filters} onSectionClick={handleSectionClick} />
          </div>
        )}
        {activeTab === "stats" && (
          <div role="tabpanel" id="panel-stats" aria-labelledby="tab-stats">
            <StatsTab bookId={filters.bookId} />
          </div>
        )}
      </div>
    </div>
  )
}

const TranslatePage = () => {
  return (
    <Suspense fallback={<div style={{ padding: 32, textAlign: "center", color: "var(--muted)" }}>Loading...</div>}>
      <TranslatePageInner />
    </Suspense>
  )
}

export default TranslatePage

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: 32,
    maxWidth: 1200,
    margin: "0 auto",
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 24,
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
    borderBottom: "2px solid transparent",
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
}
