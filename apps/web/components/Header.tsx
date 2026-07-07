"use client"

import type { Session } from "next-auth"
import { signOut } from "next-auth/react"
import Link from "next/link"
import type { Role } from "@/lib/auth"

interface HeaderProps {
  user?: Session["user"]
}

export default function Header({ user }: HeaderProps) {
  const roles = ((user as unknown as { roles: Role[] })?.roles ?? []) as Role[]
  const isEditor = roles.includes("EDITOR")
  const isTranslator = roles.includes("TRANSLATOR")
  const isSuperAdmin = roles.includes("SUPER_ADMIN")

  if (!user) return null

  return (
    <header style={styles.header}>
      <div style={styles.left}>
        <Link href="/dashboard" style={styles.logo}>
          Maha Pothana
        </Link>
        <nav style={styles.nav}>
          <Link href="/dashboard" style={styles.link}>
            Dashboard
          </Link>
          {isEditor && (
            <Link href="/books" style={styles.link}>
              Books
            </Link>
          )}
          {isTranslator && (
            <Link href="/translate" style={styles.link}>
              Translate
            </Link>
          )}
          {isSuperAdmin && (
            <Link href="/admin/users" style={styles.link}>
              Admin
            </Link>
          )}
        </nav>
      </div>
      <div style={styles.right}>
        <span style={styles.userInfo}>
          {user.image && (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img src={user.image} alt="" width={24} height={24} style={styles.avatar} />
          )}
          {user.name}
        </span>
        <button onClick={() => signOut()} style={styles.signOut}>
          Sign out
        </button>
      </div>
    </header>
  )
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 24px",
    height: 56,
    borderBottom: "1px solid var(--border)",
    background: "var(--surface)",
    position: "sticky",
    top: 0,
    zIndex: 20,
  },
  left: {
    display: "flex",
    alignItems: "center",
    gap: 32,
  },
  logo: {
    fontWeight: 700,
    fontSize: 18,
    color: "var(--primary)",
  },
  nav: {
    display: "flex",
    gap: 16,
  },
  link: {
    fontSize: 14,
    color: "var(--muted)",
    transition: "color 0.2s",
  },
  right: {
    display: "flex",
    alignItems: "center",
    gap: 16,
  },
  userInfo: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 14,
  },
  avatar: {
    borderRadius: "50%",
  },
  signOut: {
    fontSize: 13,
    padding: "4px 12px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "transparent",
    color: "var(--muted)",
  },
}
