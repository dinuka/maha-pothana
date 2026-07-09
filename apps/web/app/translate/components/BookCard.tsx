import Link from "next/link"
import type { BookListItem } from "@/lib/api/books"
import { SectionProgressBar } from "@/components/SectionProgressBar"

interface BookCardProps {
  book: BookListItem
}

const languageLabel = (lang: string): string =>
  lang === "si" ? "Sinhala" : lang === "sa" ? "Sanskrit" : lang === "ta" ? "Tamil" : lang

export const BookCard = ({ book }: BookCardProps) => {
  const { stats } = book

  return (
    <Link href={`/translate/${book.id}`} style={styles.card}>
      <div style={styles.thumbnail}>
        {book.thumbnailKey ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={book.thumbnailKey} alt="" style={styles.thumbImg} />
        ) : (
          <div style={styles.placeholder}>{book.title[0] ?? "?"}</div>
        )}
      </div>
      <div style={styles.body}>
        <h3 style={styles.title}>{book.title}</h3>
        <p style={styles.author}>{book.author}</p>
        <p style={styles.languages}>
          {languageLabel(book.sourceLanguage)} →{" "}
          {book.translateLanguages.map(languageLabel).join(", ")}
        </p>
        <p style={styles.pageCount}>{book.pageCount} pages</p>

        <SectionProgressBar
          approved={stats.translatedSections}
          inProgress={stats.inProgressSections}
          pending={stats.pendingSections}
          total={stats.totalSections}
          size="sm"
          showLabel
        />
      </div>
    </Link>
  )
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    display: "block",
    border: "1px solid var(--border)",
    borderRadius: 12,
    overflow: "hidden",
    background: "var(--surface)",
    cursor: "pointer",
  },
  thumbnail: {
    width: "100%",
    height: 160,
    background: "var(--background)",
    overflow: "hidden",
  },
  thumbImg: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },
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
  body: {
    padding: 16,
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: 600,
    color: "var(--foreground)",
  },
  author: {
    fontSize: 13,
    color: "var(--muted)",
  },
  languages: {
    fontSize: 12,
    color: "var(--muted)",
  },
  pageCount: {
    fontSize: 12,
    color: "var(--muted)",
    marginBottom: 4,
  },
}
