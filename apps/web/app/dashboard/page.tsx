import { auth } from "@/lib/auth"
import type { Role } from "@/lib/auth"
import Link from "next/link"

export default async function DashboardPage() {
  const session = await auth()
  const roles = ((session?.user as unknown as { roles: Role[] })?.roles ?? []) as Role[]
  const isEditor = roles.includes("EDITOR")
  const isTranslator = roles.includes("TRANSLATOR")

  return (
    <div style={styles.page}>
      <h1 style={styles.greeting}>
        Welcome, {(session?.user as unknown as { name?: string })?.name ?? "User"}
      </h1>
      <div style={styles.grid}>
        {isEditor && (
          <Link href="/books" style={styles.card}>
            <h2 style={styles.cardTitle}>My Books</h2>
            <p style={styles.cardDesc}>Manage your books, pages, and translations</p>
          </Link>
        )}
        {isEditor && (
          <Link href="/books/new" style={styles.card}>
            <h2 style={styles.cardTitle}>Upload Book</h2>
            <p style={styles.cardDesc}>Add a new book for translation</p>
          </Link>
        )}
        {isTranslator && (
          <Link href="/translate" style={styles.card}>
            <h2 style={styles.cardTitle}>Translate</h2>
            <p style={styles.cardDesc}>Contribute translations to available sections</p>
          </Link>
        )}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: 48,
    maxWidth: 800,
    margin: "0 auto",
  },
  greeting: {
    fontSize: 32,
    fontWeight: 700,
    marginBottom: 32,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
    gap: 16,
  },
  card: {
    padding: 24,
    border: "1px solid var(--border)",
    borderRadius: 12,
    transition: "box-shadow 0.2s",
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 600,
    marginBottom: 8,
  },
  cardDesc: {
    fontSize: 14,
    color: "var(--muted)",
    lineHeight: 1.5,
  },
}
