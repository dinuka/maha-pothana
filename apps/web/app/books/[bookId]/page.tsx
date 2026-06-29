import Link from "next/link"

interface Page {
  id: string
  pageNumber: number
  originalPageNumber?: string
  status: string
}

interface BookDetail {
  id: string
  title: string
  author: string
  sourceLanguage: string
  translateLanguages: string[]
  status: string
  pages: Page[]
}

async function getBook(bookId: string): Promise<BookDetail | null> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/books/${bookId}`, {
      cache: "no-store",
    })
    if (res.ok) return res.json()
  } catch {
    /* noop */
  }
  return null
}

export default async function BookConsolePage({
  params,
}: {
  params: Promise<{ bookId: string }>
}) {
  const { bookId } = await params
  const book = await getBook(bookId)

  if (!book) {
    return (
      <div style={styles.page}>
        <p>Book not found</p>
        <Link href="/books" style={{ color: "var(--primary)" }}>← Back to books</Link>
      </div>
    )
  }

  return (
    <div style={styles.page}>
      <Link href="/books" style={styles.backLink}>← Back to books</Link>
      <div style={styles.header}>
        <h1 style={styles.title}>{book.title}</h1>
        <div style={styles.meta}>
          <span>{book.author}</span>
          <span style={styles.dot}>·</span>
          <span>{book.sourceLanguage} → {book.translateLanguages.join(", ")}</span>
          <span style={styles.dot}>·</span>
          <span style={styles.badge}>{book.status}</span>
        </div>
      </div>

      <div style={styles.controls}>
        <select style={styles.filter}>
          <option>All Pages</option>
          <option>Completed</option>
          <option>In Progress</option>
          <option>Not Started</option>
        </select>
        <select style={styles.filter}>
          <option>Sort by Page Number</option>
          <option>Sort by Progress</option>
        </select>
      </div>

      <div style={styles.pageGrid}>
        {book.pages.map((page) => (
          <Link
            key={page.id}
            href={`/books/${bookId}/pages/${page.pageNumber}`}
            style={styles.pageCard}
          >
            <div style={styles.pageNum}>{page.pageNumber}</div>
            {page.originalPageNumber && (
              <div style={styles.originalLabel}>{page.originalPageNumber}</div>
            )}
            <span style={styles.statusBadge}>
              {page.status === "SECTIONS_CONFIRMED" ? "✅" : page.status === "PROCESSING" ? "⏳" : "❌"}
            </span>
          </Link>
        ))}
        {book.pages.length === 0 && (
          <p style={{ color: "var(--muted)", gridColumn: "1 / -1", textAlign: "center", padding: 48 }}>
            No pages yet. Book is still processing.
          </p>
        )}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties | Record<string, React.CSSProperties>> = {
  page: { padding: 48, maxWidth: 960, margin: "0 auto" },
  backLink: { color: "var(--muted)", fontSize: 14, display: "inline-block", marginBottom: 16 },
  header: { marginBottom: 32 },
  title: { fontSize: 28, fontWeight: 700, marginBottom: 8 },
  meta: { display: "flex", alignItems: "center", gap: 8, fontSize: 14, color: "var(--muted)" },
  dot: { color: "var(--border)" },
  badge: {
    padding: "2px 8px",
    borderRadius: 4,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    textTransform: "capitalize",
    fontSize: 12,
  },
  controls: { display: "flex", gap: 12, marginBottom: 24 },
  filter: {
    padding: "8px 12px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    fontSize: 13,
    background: "var(--background)",
    color: "var(--foreground)",
  },
  pageGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))",
    gap: 12,
  },
  pageCard: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 8,
    padding: 16,
    border: "1px solid var(--border)",
    borderRadius: 8,
    cursor: "pointer",
    transition: "box-shadow 0.2s",
  },
  pageNum: { fontSize: 18, fontWeight: 600 },
  originalLabel: { fontSize: 11, color: "var(--muted)", fontStyle: "italic" },
  statusBadge: {
    fontSize: 20,
  },
}
