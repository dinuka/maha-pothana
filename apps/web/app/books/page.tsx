import { apiFetch } from "@/lib/apiClient"
import Link from "next/link"
import { SectionProgressBar } from "@/components/SectionProgressBar"
import type { BookStatsSummary } from "@/lib/api/books"

interface Book {
  id: string
  title: string
  author: string
  language: string
  status: string
  thumbnailKey?: string
  stats: BookStatsSummary
}

async function getBooks(): Promise<Book[]> {
  try {
    const res = await apiFetch("/api/books", { cache: "no-store" })
    if (res.ok) return (await res.json()) as Book[]
  } catch {
    /* noop */
  }
  return []
}

export default async function BooksPage() {
  const books = await getBooks()

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h1 style={styles.title}>My Books</h1>
        <Link href="/books/new" style={styles.uploadButton}>
          Upload New Book
        </Link>
      </div>

      {books.length === 0 ? (
        <div style={styles.empty}>
          <p>No books yet.</p>
          <Link href="/books/new" style={styles.link}>
            Upload your first book
          </Link>
        </div>
      ) : (
        <div style={styles.grid}>
          {books.map((book) => (
            <Link key={book.id} href={`/books/${book.id}`} style={styles.card}>
              <div style={styles.thumbnail}>
                {book.thumbnailKey ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img src={book.thumbnailKey} alt="" style={styles.thumbImg} />
                ) : (
                  <div style={styles.placeholder}>{book.title[0] ?? "?"}</div>
                )}
              </div>
              <div style={styles.cardBody}>
                <h3 style={styles.bookTitle}>{book.title}</h3>
                <p style={styles.bookAuthor}>{book.author}</p>
                <span style={styles.badge}>{book.status}</span>
                <div style={styles.progress}>
                  <SectionProgressBar
                    approved={book.stats.translatedSections}
                    inProgress={book.stats.inProgressSections}
                    pending={book.stats.pendingSections}
                    total={book.stats.totalSections}
                    size="sm"
                    showLabel
                  />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 48, maxWidth: 960, margin: "0 auto" },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 32,
  },
  title: { fontSize: 28, fontWeight: 700 },
  uploadButton: {
    padding: "10px 20px",
    background: "var(--primary)",
    color: "#fff",
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
  },
  empty: { textAlign: "center", padding: 64, color: "var(--muted)" },
  link: {
    color: "var(--primary)",
    textDecoration: "underline",
    marginTop: 8,
    display: "inline-block",
  },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 },
  card: {
    border: "1px solid var(--border)",
    borderRadius: 12,
    overflow: "hidden",
    transition: "box-shadow 0.2s",
    cursor: "pointer",
  },
  thumbnail: {
    width: "100%",
    height: 160,
    background: "var(--surface)",
    overflow: "hidden",
  },
  thumbImg: { width: "100%", height: "100%", objectFit: "cover" },
  placeholder: {
    width: "100%",
    height: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 48,
    fontWeight: 700,
    color: "var(--muted)",
  },
  cardBody: { padding: 16 },
  bookTitle: { fontSize: 16, fontWeight: 600, marginBottom: 4 },
  bookAuthor: { fontSize: 13, color: "var(--muted)", marginBottom: 8 },
  badge: {
    fontSize: 12,
    padding: "2px 8px",
    borderRadius: 4,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    textTransform: "capitalize",
  },
  progress: { marginTop: 12 },
}
