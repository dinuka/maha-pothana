"use client"

import { useEffect, useState } from "react"
import type { BookListItem } from "@/lib/api/books"
import { getAvailableBooks } from "@/lib/api/books"
import { BookCard } from "./components/BookCard"

const TranslatePage = () => {
  const [books, setBooks] = useState<BookListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getAvailableBooks()
      .then((data) => setBooks(data))
      .catch(() => setError("Failed to load books"))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Translate</h1>
      <p style={styles.subtitle}>
        Pick a book to translate, review its history, or check its progress.
      </p>

      {loading && (
        <div style={styles.loading}>
          <div style={styles.spinner} />
          <span>Loading books...</span>
        </div>
      )}

      {!loading && error && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>⚠️</div>
          <div style={styles.emptyTitle}>{error}</div>
        </div>
      )}

      {!loading && !error && books.length === 0 && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>📚</div>
          <div style={styles.emptyTitle}>No books ready for translation yet</div>
        </div>
      )}

      {!loading && !error && books.length > 0 && (
        <div style={styles.grid}>
          {books.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}
    </div>
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
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: "var(--muted)",
    marginBottom: 24,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
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
    color: "var(--foreground)",
  },
}
