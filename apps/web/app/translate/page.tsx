"use client"

import { useState } from "react"

interface Section {
  id: string
  type: string
  originalText: string
  autoTranslatedText: string
  pageNumber: number
  bookTitle: string
  bookId: string
}

interface MyTranslation {
  translatedText: string
  exactLetterTranslation: string | null
  isApproved: boolean
}

export default function TranslatePage() {
  const [section, setSection] = useState<Section | null>(null)
  const [loading, setLoading] = useState(false)
  const [translatedText, setTranslatedText] = useState("")
  const [exactLetter, setExactLetter] = useState("")
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState("")
  const [myTranslation, setMyTranslation] = useState<MyTranslation | null>(null)

  const fetchNextSection = async () => {
    setLoading(true)
    setMessage("")
    setMyTranslation(null)
    setExactLetter("")
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/sections/next`)
      if (res.status === 404) {
        setMessage("All sections translated!")
        setSection(null)
        return
      }
      if (!res.ok) throw new Error("Failed to fetch section")
      const data = (await res.json()) as Section
      setSection(data)
      setTranslatedText(data.autoTranslatedText ?? "")
      fetchMyTranslation(data.id)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Error loading section")
    } finally {
      setLoading(false)
    }
  }

  const fetchMyTranslation = async (sectionId: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/sections/${sectionId}/my-translation`)
      if (res.ok) {
        const data = (await res.json()) as MyTranslation
        setMyTranslation(data)
        setTranslatedText(data.translatedText)
        setExactLetter(data.exactLetterTranslation ?? "")
      }
    } catch {
      /* noop */
    }
  }

  const handleSave = async () => {
    if (!section || !translatedText.trim()) return
    setSaving(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/sections/${section.id}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          translatedText: translatedText.trim(),
          exactLetterTranslation: exactLetter.trim() || null,
        }),
      })
      if (!res.ok) throw new Error("Failed to save translation")
      setMessage("Translation saved!")
      setMyTranslation({
        translatedText: translatedText.trim(),
        exactLetterTranslation: exactLetter.trim() || null,
        isApproved: false,
      })
      setTimeout(() => setMessage(""), 1500)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Error saving translation")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Translate</h1>

      {!section && !loading && message && (
        <div style={styles.messageBox}>{message}</div>
      )}

      {!section && !loading && !message && (
        <div style={styles.empty}>
          <p style={{ marginBottom: 16 }}>Click below to get started with a random section.</p>
          <button onClick={fetchNextSection} style={styles.nextButton}>
            Next Section
          </button>
        </div>
      )}

      {loading && <div style={styles.loading}>Loading section...</div>}

      {section && (
        <div style={styles.editor}>
          <div style={styles.editorHeader}>
            <div>
              <strong>{section.bookTitle}</strong>
              <span style={styles.pageIndicator}> — Page {section.pageNumber}</span>
            </div>
            <div style={styles.editorActions}>
              <button onClick={fetchNextSection} style={styles.skipBtn}>Skip</button>
              <button onClick={handleSave} disabled={saving} style={styles.saveBtn}>
                {saving ? "Saving..." : "Save Translation"}
              </button>
            </div>
          </div>

          <div style={styles.editorBody}>
            <div style={styles.sectionImage}>
              <div style={styles.imagePlaceholder}>
                <p>Section Image</p>
                <p style={{ fontSize: 12, color: "var(--muted)" }}>(cropped from page)</p>
              </div>
              <div style={styles.zoomControls}>
                <button style={styles.zoomBtn}>−</button>
                <span style={{ fontSize: 13 }}>100%</span>
                <button style={styles.zoomBtn}>+</button>
              </div>
            </div>

            <div style={styles.translationPanel}>
              <div style={styles.field}>
                <label style={styles.fieldLabel}>Auto-translated text</label>
                <div style={styles.autoText}>{section.autoTranslatedText}</div>
              </div>
              <div style={styles.field}>
                <label style={styles.fieldLabel}>Your translation *</label>
                <textarea
                  value={translatedText}
                  onChange={(e) => setTranslatedText(e.target.value)}
                  style={styles.textarea}
                  placeholder="Enter your translation here..."
                />
              </div>
              <div style={styles.field}>
                <label style={styles.fieldLabel}>
                  Exact letter transliteration
                  <span style={{ fontWeight: 400, color: "var(--muted)" }}> (optional)</span>
                </label>
                <input
                  value={exactLetter}
                  onChange={(e) => setExactLetter(e.target.value)}
                  style={styles.exactLetterInput}
                  placeholder="e.g. माता → මාතා (letter-for-letter)"
                />
              </div>

              {myTranslation && !myTranslation.isApproved && (
                <div style={styles.mySubmission}>
                  <label style={styles.fieldLabel}>My previous submission (pending review)</label>
                  <div style={styles.pendingText}>{myTranslation.translatedText}</div>
                  {myTranslation.exactLetterTranslation && (
                    <div style={styles.pendingTextSmall}>
                      Exact: {myTranslation.exactLetterTranslation}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {message && <div style={styles.messageBox}>{message}</div>}

          <div style={styles.pageContext}>
            <button style={styles.contextBtn}>← Previous Page</button>
            <span style={{ fontSize: 13, color: "var(--muted)" }}>Page {section.pageNumber}</span>
            <button style={styles.contextBtn}>Next Page →</button>
          </div>
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 32, maxWidth: 960, margin: "0 auto" },
  title: { fontSize: 28, fontWeight: 700, marginBottom: 24 },
  empty: { textAlign: "center", padding: 64, color: "var(--muted)" },
  nextButton: {
    padding: "12px 32px",
    background: "var(--primary)",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 16,
    fontWeight: 600,
    cursor: "pointer",
  },
  loading: { textAlign: "center", padding: 64, color: "var(--muted)" },
  editor: { display: "flex", flexDirection: "column", gap: 16 },
  editorHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 16px",
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
    fontSize: 14,
  },
  pageIndicator: { color: "var(--muted)" },
  editorActions: { display: "flex", gap: 8 },
  skipBtn: {
    padding: "6px 16px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    cursor: "pointer",
    fontSize: 13,
  },
  saveBtn: {
    padding: "6px 16px",
    border: "none",
    borderRadius: 6,
    background: "var(--primary)",
    color: "#fff",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
  },
  editorBody: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 },
  sectionImage: {
    border: "1px solid var(--border)",
    borderRadius: 8,
    overflow: "hidden",
  },
  imagePlaceholder: {
    height: 300,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    background: "var(--surface)",
    color: "var(--muted)",
    gap: 8,
  },
  zoomControls: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 8,
    borderTop: "1px solid var(--border)",
  },
  zoomBtn: {
    width: 28,
    height: 28,
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    cursor: "pointer",
    fontSize: 16,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  translationPanel: { display: "flex", flexDirection: "column", gap: 16 },
  field: { display: "flex", flexDirection: "column", gap: 6 },
  fieldLabel: { fontSize: 13, fontWeight: 600, color: "var(--muted)" },
  autoText: {
    padding: 12,
    border: "1px solid var(--border)",
    borderRadius: 8,
    fontSize: 14,
    lineHeight: 1.6,
    color: "var(--muted)",
    fontStyle: "italic",
  },
  textarea: {
    padding: 12,
    border: "1px solid var(--border)",
    borderRadius: 8,
    fontSize: 14,
    lineHeight: 1.6,
    minHeight: 140,
    resize: "vertical",
    background: "var(--background)",
    color: "var(--foreground)",
    fontFamily: "inherit",
  },
  exactLetterInput: {
    padding: "10px 12px",
    border: "1px solid var(--border)",
    borderRadius: 8,
    fontSize: 14,
    background: "var(--background)",
    color: "var(--foreground)",
    fontFamily: "monospace",
  },
  mySubmission: {
    padding: 12,
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
  },
  pendingText: {
    fontSize: 14,
    lineHeight: 1.6,
    marginTop: 6,
    padding: 8,
    background: "var(--background)",
    borderRadius: 6,
  },
  pendingTextSmall: {
    fontSize: 13,
    lineHeight: 1.5,
    marginTop: 4,
    padding: "6px 8px",
    background: "var(--background)",
    borderRadius: 6,
    fontFamily: "monospace",
    color: "var(--muted)",
  },
  messageBox: {
    padding: "12px 16px",
    border: "1px solid var(--success)",
    borderRadius: 8,
    background: "#F0FDF4",
    color: "var(--success)",
    fontSize: 14,
    textAlign: "center",
  },
  pageContext: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 16,
    padding: 12,
  },
  contextBtn: {
    padding: "8px 16px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--surface)",
    cursor: "pointer",
    fontSize: 13,
  },
}
