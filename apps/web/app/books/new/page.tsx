"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

const LANGUAGES = [
  { value: "si", label: "Sinhala" },
  { value: "ta", label: "Tamil" },
  { value: "en", label: "English" },
  { value: "sa", label: "Sanskrit" },
  { value: "pi", label: "Pali" },
  { value: "bn", label: "Bengali" },
  { value: "mr", label: "Marathi" },
  { value: "hi", label: "Hindi" },
] as const

export default function UploadBookPage() {
  const router = useRouter()
  const [title, setTitle] = useState("")
  const [author, setAuthor] = useState("")
  const [sourceLanguage, setSourceLanguage] = useState("")
  const [targetLanguages, setTargetLanguages] = useState<string[]>([])
  const [description, setDescription] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState("")
  const [dragOver, setDragOver] = useState(false)

  const toggleTargetLanguage = (lang: string) => {
    setTargetLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title || !author || !sourceLanguage || targetLanguages.length === 0 || !file) {
      setError("Please fill all required fields")
      return
    }
    setUploading(true)
    setError("")

    const formData = new FormData()
    formData.append("title", title)
    formData.append("author", author)
    formData.append("sourceLanguage", sourceLanguage)
    targetLanguages.forEach((lang) => formData.append("translateLanguages", lang))
    formData.append("description", description)
    formData.append("file", file)

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/books`, {
        method: "POST",
        body: formData,
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.message || "Upload failed")
      }
      const book = await res.json()
      router.push(`/books/${book.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed")
      setUploading(false)
    }
  }

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Upload New Book</h1>
      <form onSubmit={handleSubmit} style={styles.form}>
        <label style={styles.label}>
          Book Title *
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={styles.input}
            placeholder="Enter book title"
          />
        </label>
        <label style={styles.label}>
          Author *
          <input
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            style={styles.input}
            placeholder="Enter author name"
          />
        </label>
        <label style={styles.label}>
          Source Language *
          <select value={sourceLanguage} onChange={(e) => setSourceLanguage(e.target.value)} style={styles.input}>
            <option value="">Select source language</option>
            {LANGUAGES.map((lang) => (
              <option key={lang.value} value={lang.value}>{lang.label}</option>
            ))}
          </select>
        </label>
        <label style={styles.label}>
          Target Languages * (select one or more)
          <div style={styles.chipGroup}>
            {LANGUAGES.filter((l) => l.value !== sourceLanguage).map((lang) => (
              <button
                key={lang.value}
                type="button"
                onClick={() => toggleTargetLanguage(lang.value)}
                style={{
                  ...styles.chip,
                  background: targetLanguages.includes(lang.value) ? "var(--primary)" : "var(--surface)",
                  color: targetLanguages.includes(lang.value) ? "#fff" : "var(--foreground)",
                  borderColor: targetLanguages.includes(lang.value) ? "var(--primary)" : "var(--border)",
                }}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </label>
        <label style={styles.label}>
          Description
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={{ ...styles.input, minHeight: 80, resize: "vertical" as const }}
            placeholder="Brief description of the book"
          />
        </label>
        <div
          style={{
            ...styles.dropZone,
            borderColor: dragOver ? "var(--primary)" : "var(--border)",
            background: dragOver ? "var(--surface)" : "transparent",
          }}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragOver(false)
            const f = e.dataTransfer.files[0]
            if (f?.type === "application/pdf") setFile(f)
            else setError("Please upload a PDF file")
          }}
        >
          {file ? (
            <p>{file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)</p>
          ) : (
            <p>Drag & drop a PDF here, or click to select</p>
          )}
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            style={{ display: "none" }}
            id="file-input"
          />
          <button type="button" onClick={() => document.getElementById("file-input")?.click()} style={styles.fileButton}>
            Select PDF
          </button>
        </div>

        {error && <p style={styles.error}>{error}</p>}

        <button type="submit" disabled={uploading} style={styles.submitButton}>
          {uploading ? "Uploading..." : "Upload Book"}
        </button>
      </form>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { padding: 48, maxWidth: 600, margin: "0 auto" },
  title: { fontSize: 28, fontWeight: 700, marginBottom: 32 },
  form: { display: "flex", flexDirection: "column", gap: 20 },
  label: { display: "flex", flexDirection: "column", gap: 6, fontSize: 14, fontWeight: 500 },
  input: {
    padding: "10px 12px",
    border: "1px solid var(--border)",
    borderRadius: 8,
    fontSize: 14,
    background: "var(--background)",
    color: "var(--foreground)",
  },
  chipGroup: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    padding: "6px 14px",
    border: "1px solid var(--border)",
    borderRadius: 20,
    fontSize: 13,
    cursor: "pointer",
    transition: "all 0.2s",
  },
  dropZone: {
    border: "2px dashed var(--border)",
    borderRadius: 12,
    padding: 32,
    textAlign: "center",
    cursor: "pointer",
    transition: "all 0.2s",
  },
  fileButton: {
    marginTop: 12,
    padding: "8px 16px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--surface)",
    fontSize: 13,
  },
  error: { color: "var(--error)", fontSize: 14 },
  submitButton: {
    padding: "12px 24px",
    background: "var(--primary)",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 16,
    fontWeight: 600,
  },
}
