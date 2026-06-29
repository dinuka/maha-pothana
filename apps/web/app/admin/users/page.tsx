interface User {
  id: string
  name: string
  email: string
  roles: string[]
}

async function getUsers(): Promise<User[]> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users`, {
      cache: "no-store",
    })
    if (res.ok) return res.json()
  } catch {
    /* noop */
  }
  return []
}

export default async function AdminUsersPage() {
  const users = await getUsers()

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>User Management</h1>
      <p style={styles.subtitle}>Manage user roles and permissions</p>

      <div style={styles.table}>
        <div style={styles.tableHeader}>
          <span style={{ ...styles.col, flex: 2 }}>Name</span>
          <span style={{ ...styles.col, flex: 2 }}>Email</span>
          <span style={{ ...styles.col, flex: 1 }}>Roles</span>
          <span style={{ ...styles.col, flex: 1 }}>Actions</span>
        </div>
        {users.map((user) => (
          <div key={user.id} style={styles.tableRow}>
            <span style={{ ...styles.col, flex: 2 }}>{user.name}</span>
            <span style={{ ...styles.col, flex: 2, color: "var(--muted)" }}>{user.email}</span>
            <span style={{ ...styles.col, flex: 1 }}>
              {user.roles.map((role) => (
                <span key={role} style={styles.roleBadge(role)}>{role}</span>
              ))}
            </span>
            <span style={{ ...styles.col, flex: 1 }}>
              <button style={styles.editBtn}>Edit Roles</button>
            </span>
          </div>
        ))}
        {users.length === 0 && (
          <div style={{ padding: 48, textAlign: "center", color: "var(--muted)" }}>
            No users found
          </div>
        )}
      </div>
    </div>
  )
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const styles: Record<string, any> = {
  page: { padding: 48, maxWidth: 800, margin: "0 auto" },
  title: { fontSize: 28, fontWeight: 700, marginBottom: 8 },
  subtitle: { fontSize: 14, color: "var(--muted)", marginBottom: 32 },
  table: {
    border: "1px solid var(--border)",
    borderRadius: 12,
    overflow: "hidden",
  },
  tableHeader: {
    display: "flex",
    padding: "12px 16px",
    background: "var(--surface)",
    borderBottom: "1px solid var(--border)",
    fontWeight: 600,
    fontSize: 13,
    color: "var(--muted)",
  },
  tableRow: {
    display: "flex",
    padding: "12px 16px",
    borderBottom: "1px solid var(--border)",
    fontSize: 14,
    alignItems: "center",
  },
  col: { flex: 1 },
  roleBadge: (role: string) => ({
    display: "inline-block",
    padding: "2px 6px",
    borderRadius: 4,
    background: role === "SUPER_ADMIN" ? "#FEF3C7" : "#DBEAFE",
    color: role === "SUPER_ADMIN" ? "#92400E" : "#1E40AF",
    fontSize: 11,
    fontWeight: 600,
    marginRight: 4,
  }),
  editBtn: {
    padding: "4px 12px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--surface)",
    cursor: "pointer",
    fontSize: 12,
  },
}
