"use client"

interface DraftSaveIndicatorProps {
  visible: boolean
}

export const DraftSaveIndicator = ({ visible }: DraftSaveIndicatorProps) => {
  if (!visible) return null

  return (
    <div style={styles.container} aria-live="polite" aria-atomic="true">
      <span style={styles.icon}>💾</span>
      <span style={styles.text}>Draft saved ✓</span>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    padding: "6px 12px",
    background: "#F0FDF4",
    border: "1px solid #BBF7D0",
    borderRadius: 6,
    fontSize: 13,
    color: "#166534",
  },
  icon: {
    fontSize: 12,
  },
  text: {
    fontSize: 13,
  },
}
