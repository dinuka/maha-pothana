import Link from "next/link"

export default function Home() {
  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Maha Pothana</h1>
      <p style={styles.subtitle}>Community-driven book translation platform</p>
      <div style={styles.actions}>
        <Link href="/auth/signin" style={styles.primaryButton}>
          Sign in to get started
        </Link>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "calc(100vh - 56px)",
    gap: 16,
    padding: 24,
  },
  title: {
    fontSize: 48,
    fontWeight: 700,
  },
  subtitle: {
    fontSize: 18,
    color: "var(--muted)",
  },
  actions: {
    marginTop: 24,
  },
  primaryButton: {
    display: "inline-block",
    padding: "12px 24px",
    background: "var(--primary)",
    color: "#fff",
    borderRadius: 8,
    fontSize: 16,
    fontWeight: 600,
  },
}
