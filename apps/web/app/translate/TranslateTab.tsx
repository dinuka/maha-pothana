"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { apiFetchBrowser } from "@/lib/apiClientBrowser"
import type { NextSectionResponse } from "@/lib/api/translations"
import { SourceTextPanel } from "./components/SourceTextPanel"
import { DraftSaveIndicator } from "./components/DraftSaveIndicator"
import { useTranslationDraft } from "@/hooks/useTranslationDraft"
import type { TranslationFilters } from "@/hooks/useTranslationFilters"

interface TranslateTabProps {
  filters: TranslationFilters
  isEditor?: boolean
}

interface TransliterationState {
  text: string
  source: "ai" | "manual" | null
  loading: boolean
  error: boolean
}

export const TranslateTab = ({ filters, isEditor = false }: TranslateTabProps) => {
  const [section, setSection] = useState<NextSectionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [myTranslation, setMyTranslation] = useState<{
    translatedText: string
    exactLetterTranslation: string | null
    isApproved: boolean
  } | null>(null)
  const [exactLetter, setExactLetter] = useState("")
  const [saving, setSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")
  const [zoom, setZoom] = useState(100)
  const [sourceTextZoom, setSourceTextZoom] = useState(100)
  const [isDragging, setIsDragging] = useState(false)
  const [extractionStatus, setExtractionStatus] = useState<"extracted" | "pending" | "failed" | null>(null)
  const [extractionConfidence, setExtractionConfidence] = useState<number | null>(null)
  const [sourceText, setSourceText] = useState<string | null>(null)
  const [aiText, setAiText] = useState<string | null>(null)
  const [transliteration, setTransliteration] = useState<TransliterationState>({
    text: "",
    source: null,
    loading: false,
    error: false,
  })
  const [extracting, setExtracting] = useState(false)
  const [transliterating, setTransliterating] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)
  const dragStart = useRef({ x: 0, y: 0, scrollLeft: 0, scrollTop: 0 })
  const scrollRef = useRef<HTMLDivElement>(null)

  const {
    translatedText,
    setTranslatedText,
    showSavedIndicator,
    updateText,
    resetDirty,
    clearDraft,
  } = useTranslationDraft(section?.id ?? null)

  const fetchMyTranslation = async (sectionId: string) => {
    try {
      const res = await apiFetchBrowser(`/api/sections/${sectionId}/my-translation`)
      if (res.ok) {
        const data = (await res.json()) as {
          translatedText: string
          exactLetterTranslation: string | null
          isApproved: boolean
        }
        setMyTranslation(data)
        setTranslatedText(data.translatedText)
        setExactLetter(data.exactLetterTranslation ?? "")
      }
    } catch {
      /* noop */
    }
  }

  const fetchExtraction = async (sectionId: string) => {
    try {
      const res = await apiFetchBrowser(`/api/sections/${sectionId}/extraction`)
      if (res.ok) {
        const data = (await res.json()) as {
          extractedText: string
          confidence: number
        }
        setAiText(data.extractedText)
        setExtractionStatus("extracted")
        setExtractionConfidence(data.confidence)
      } else {
        setExtractionStatus(null)
        setExtractionConfidence(null)
      }
    } catch {
      /* noop */
    }
  }

  const fetchTransliterations = async (sectionId: string) => {
    try {
      const res = await apiFetchBrowser(`/api/sections/${sectionId}/transliterations`)
      if (res.ok) {
        const data = (await res.json()) as {
          transliterations: Array<{ transliteratedText: string; targetScript: string }>
        }
        if (data.transliterations.length > 0) {
          const first = data.transliterations[0]
          if (first) {
            setTransliteration({
              text: first.transliteratedText,
              source: "ai",
              loading: false,
              error: false,
            })
          }
        }
      }
    } catch {
      /* noop */
    }
  }

  const fetchNextSection = async (currentFilters: TranslationFilters) => {
    setLoading(true)
    setError(null)
    setMyTranslation(null)
    setExactLetter("")
    setTranslatedText("")
    setTransliteration({ text: "", source: null, loading: false, error: false })
    setExtractionStatus(null)
    setExtractionConfidence(null)
    setAiText(null)
    setSourceText(null)
    resetDirty()
    try {
      const params = new URLSearchParams()
      if (currentFilters.bookId) params.set("bookId", currentFilters.bookId)
      if (currentFilters.language) params.set("language", currentFilters.language)
      if (currentFilters.page) params.set("page", String(currentFilters.page))
      if (currentFilters.status) params.set("status", currentFilters.status)
      const qs = params.toString()

      const res = await apiFetchBrowser(`/api/sections/next${qs ? `?${qs}` : ""}`)
      if (res.status === 404) {
        setSection(null)
        setError("No sections available")
        return
      }
      if (!res.ok) throw new Error("Failed to fetch section")
      const data = (await res.json()) as NextSectionResponse
      setSection(data)
      setSourceText(data.originalText)
      setAiText(data.aiExtractedText)
      setExtractionStatus(data.aiExtractedText ? "extracted" : null)
      setTranslatedText(data.autoTranslatedText ?? "")
      if (data.exactLetterTranslation) setExactLetter(data.exactLetterTranslation)
      fetchMyTranslation(data.id)
      fetchExtraction(data.id)
      fetchTransliterations(data.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading section")
    } finally {
      setLoading(false)
    }
  }

  const handleExtract = async () => {
    if (!section || extracting) return
    setExtracting(true)
    setExtractionStatus("pending")
    setAiError(null)
    try {
      await apiFetchBrowser(`/api/sections/${section.id}/extract`, {
        method: "POST",
      })
      let attempts = 0
      const poll = setInterval(async () => {
        attempts++
        if (attempts > 30) {
          clearInterval(poll)
          setExtractionStatus("failed")
          setExtracting(false)
          setAiError("Extraction timed out. Please try again.")
          return
        }
        try {
          const res = await apiFetchBrowser(`/api/sections/${section.id}/extraction`)
          if (res.ok) {
            const data = (await res.json()) as {
              extractedText: string
              confidence: number
            }
            clearInterval(poll)
            setAiText(data.extractedText)
            setExtractionStatus("extracted")
            setExtractionConfidence(data.confidence)
            setExtracting(false)
            setAiError(null)
          } else if (res.status === 404) {
            // Still processing, continue polling
          } else {
            clearInterval(poll)
            setExtractionStatus("failed")
            setExtracting(false)
            try {
              const errData = await res.json() as { detail?: string }
              setAiError(errData.detail || `Extraction failed (${res.status})`)
            } catch {
              setAiError(`Extraction failed (${res.status})`)
            }
          }
        } catch {
          /* continue polling */
        }
      }, 2000)
    } catch {
      setExtractionStatus("failed")
      setExtracting(false)
      setAiError("Network error. Please check your connection.")
    }
  }

  const handleTransliterate = async (force = false) => {
    if (!section || transliterating) return
    const sourceTextForTranslit = aiText || sourceText
    if (!sourceTextForTranslit) return

    setTransliterating(true)
    setTransliteration((prev) => ({ ...prev, loading: true, error: false }))
    try {
      const forceParam = force ? "&force=true" : ""
      const res = await apiFetchBrowser(
        `/api/sections/${section.id}/transliterate?target_script=sinhala${forceParam}`,
        { method: "POST" }
      )
      if (res.ok) {
        const data = (await res.json()) as {
          transliteratedText?: string
          cached?: boolean
          status?: string
        }
        if (data.transliteratedText) {
          setTransliteration({
            text: data.transliteratedText,
            source: "ai",
            loading: false,
            error: false,
          })
          setExactLetter(data.transliteratedText)
          saveExactLetter(data.transliteratedText)
        } else if (data.status === "queued") {
          let attempts = 0
          const maxAttempts = 8
          const schedulePoll = (delay: number) => {
            const timer = setTimeout(async () => {
              attempts++
              try {
                const tRes = await apiFetchBrowser(
                  `/api/sections/${section.id}/transliterations`
                )
                if (tRes.ok) {
                  const tData = (await tRes.json()) as {
                    transliterations: Array<{ transliteratedText: string }>
                  }
                  if (tData.transliterations.length > 0) {
                    const first = tData.transliterations[0]
                    if (first) {
                      clearTimeout(timer)
                      setTransliteration({
                        text: first.transliteratedText,
                        source: "ai",
                        loading: false,
                        error: false,
                      })
                      setExactLetter(first.transliteratedText)
                      saveExactLetter(first.transliteratedText)
                      setTransliterating(false)
                      return
                    }
                  }
                }
              } catch {
                /* continue polling */
              }
              if (attempts >= maxAttempts) {
                setTransliteration((prev) => ({ ...prev, loading: false, error: true }))
                setTransliterating(false)
                return
              }
              schedulePoll(10000)
            }, delay)
          }
          schedulePoll(10000)
        }
      } else {
        setTransliteration((prev) => ({ ...prev, loading: false, error: true }))
      }
    } catch {
      setTransliteration((prev) => ({ ...prev, loading: false, error: true }))
    } finally {
      setTransliterating(false)
    }
  }

  const handleSourceTextUpdate = useCallback(
    async (text: string, source: "ai" | "ocr") => {
      if (source === "ai") {
        setAiText(text)
      } else {
        setSourceText(text)
      }
      setTransliteration({ text: "", source: null, loading: false, error: false })
      setExactLetter("")

      if (section) {
        setTransliterating(true)
        setTransliteration((prev) => ({ ...prev, loading: true, error: false }))
        try {
          const res = await apiFetchBrowser(
            `/api/sections/${section.id}/transliterate?target_script=sinhala`,
            { method: "POST" }
          )
          if (res.ok) {
            const data = (await res.json()) as {
              transliteratedText?: string
              cached?: boolean
              status?: string
            }
            if (data.transliteratedText) {
              setTransliteration({
                text: data.transliteratedText,
                source: "ai",
                loading: false,
                error: false,
              })
              setExactLetter(data.transliteratedText)
              saveExactLetter(data.transliteratedText)
            } else if (data.status === "queued") {
              let attempts = 0
              const maxAttempts = 8
              const schedulePoll = (delay: number) => {
                const timer = setTimeout(async () => {
                  attempts++
                  try {
                    const tRes = await apiFetchBrowser(
                      `/api/sections/${section.id}/transliterations`
                    )
                    if (tRes.ok) {
                      const tData = (await tRes.json()) as {
                        transliterations: Array<{ transliteratedText: string }>
                      }
                      if (tData.transliterations.length > 0) {
                        const first = tData.transliterations[0]
                        if (first) {
                          clearTimeout(timer)
                          setTransliteration({
                            text: first.transliteratedText,
                            source: "ai",
                            loading: false,
                            error: false,
                          })
                        setExactLetter(first.transliteratedText)
                        saveExactLetter(first.transliteratedText)
                        setTransliterating(false)
                          return
                        }
                      }
                    }
                  } catch {
                    /* continue polling */
                  }
                  if (attempts >= maxAttempts) {
                    setTransliteration((prev) => ({ ...prev, loading: false, error: true }))
                    setTransliterating(false)
                    return
                  }
                    schedulePoll(10000)
                  }, delay)
                }
                schedulePoll(10000)
              }
            } else {
            setTransliteration((prev) => ({ ...prev, loading: false, error: true }))
          }
        } catch {
          setTransliteration((prev) => ({ ...prev, loading: false, error: true }))
        } finally {
          setTransliterating(false)
        }
      }
    },
    [section]
  )

  const saveExactLetter = useCallback(async (value: string) => {
    if (!section) return
    try {
      await apiFetchBrowser(`/api/sections/${section.id}/exact-letter`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exactLetter: value }),
      })
    } catch {
      /* silent */
    }
  }, [section])

  const exactLetterTimer = useRef<ReturnType<typeof setTimeout>>()
  const reverseTimer = useRef<ReturnType<typeof setTimeout>>()
  const prevSourceTextRef = useRef<string | null>(null)

  const handleExactLetterChange = useCallback(
    (value: string) => {
      setExactLetter(value)
      if (value !== transliteration.text) {
        setTransliteration((prev) => ({ ...prev, source: "manual" }))
      }
      if (exactLetterTimer.current) clearTimeout(exactLetterTimer.current)
      exactLetterTimer.current = setTimeout(() => saveExactLetter(value), 2000)
      if (reverseTimer.current) clearTimeout(reverseTimer.current)
      reverseTimer.current = setTimeout(async () => {
        if (!section || !value.trim()) return
        prevSourceTextRef.current = aiText || sourceText || null
        try {
          const res = await apiFetchBrowser(
            `/api/sections/${section.id}/reverse-transliterate`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                transliteratedText: value.trim(),
                sourceScript: "sinhala",
                targetScript: section.book?.sourceLanguage || "unknown",
              }),
            }
          )
          if (res.ok) {
            const data = (await res.json()) as { sourceText: string }
            setAiText(data.sourceText)
            setSourceText(data.sourceText)
          }
        } catch {
          /* silent */
        }
      }, 3000)
    },
    [transliteration.text, saveExactLetter, section, aiText, sourceText]
  )

  const handleExactLetterKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.ctrlKey && e.key === "z") {
        e.preventDefault()
        if (reverseTimer.current) clearTimeout(reverseTimer.current)
        if (prevSourceTextRef.current !== null) {
          setAiText(prevSourceTextRef.current)
          setSourceText(prevSourceTextRef.current)
          prevSourceTextRef.current = null
        }
      }
    },
    []
  )

  const handleExactLetterBlur = useCallback(async () => {
    if (!section || !exactLetter.trim() || exactLetter === transliteration.text) return
    saveExactLetter(exactLetter.trim())
    prevSourceTextRef.current = aiText || sourceText || null
    try {
      const res = await apiFetchBrowser(
        `/api/sections/${section.id}/reverse-transliterate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            transliteratedText: exactLetter.trim(),
            sourceScript: "sinhala",
            targetScript: section.book?.sourceLanguage || "unknown",
          }),
        }
      )
      if (res.ok) {
        const data = (await res.json()) as { sourceText: string }
        setAiText(data.sourceText)
        setSourceText(data.sourceText)
      }
    } catch {
      /* noop */
    }
  }, [section, exactLetter, transliteration.text])

  const handleSave = async () => {
    if (!section || !translatedText.trim()) return
    setSaving(true)
    try {
      const res = await apiFetchBrowser(`/api/sections/${section.id}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          translatedText: translatedText.trim(),
          exactLetterTranslation: exactLetter.trim() || null,
        }),
      })
      if (!res.ok) throw new Error("Failed to save translation")
      setSuccessMessage("Translation saved!")
      resetDirty()
      await clearDraft()
      setTimeout(() => {
        setSuccessMessage("")
        fetchNextSection(filters)
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error saving translation")
    } finally {
      setSaving(false)
    }
  }

  const [autoTranslating, setAutoTranslating] = useState(false)

  const handleAutoTranslate = async () => {
    if (!section || autoTranslating) return
    setAutoTranslating(true)
    try {
      const res = await apiFetchBrowser(
        `/api/sections/${section.id}/auto-translate`,
        { method: "POST" }
      )
      if (res.ok) {
        const data = (await res.json()) as { translatedText: string }
        setTranslatedText(data.translatedText)
      }
    } catch {
      /* silent */
    } finally {
      setAutoTranslating(false)
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchNextSection(filters)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.bookId, filters.language, filters.page, filters.status])

  const handleZoomIn = () => setZoom((z) => Math.min(z + 10, 300))
  const handleZoomOut = () => setZoom((z) => Math.max(z - 10, 50))
  const handleZoomReset = () => setZoom(100)

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return
      const el = scrollRef.current
      if (!el) return
      setIsDragging(true)
      dragStart.current = { x: e.clientX, y: e.clientY, scrollLeft: el.scrollLeft, scrollTop: el.scrollTop }
      e.preventDefault()
    },
    []
  )

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging) return
      const el = scrollRef.current
      if (!el) return
      const dx = e.clientX - dragStart.current.x
      const dy = e.clientY - dragStart.current.y
      el.scrollLeft = dragStart.current.scrollLeft - dx
      el.scrollTop = dragStart.current.scrollTop - dy
    },
    [isDragging]
  )

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  useEffect(() => {
    if (isDragging) {
      const handleGlobalUp = () => setIsDragging(false)
      window.addEventListener("mouseup", handleGlobalUp)
      return () => window.removeEventListener("mouseup", handleGlobalUp)
    }
  }, [isDragging])

  const activeSourceText = aiText || sourceText

  return (
    <div style={styles.container}>
      {loading && (
        <div style={styles.loading}>
          <div style={styles.spinner} />
          <span>Loading section...</span>
        </div>
      )}

      {error && !section && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>🔍</div>
          <div style={styles.emptyTitle}>{error}</div>
          <div style={styles.emptyDesc}>
            {error === "No sections available"
              ? "All sections translated! Great work!"
              : "Try adjusting the language, page, or status filters."}
          </div>
          <button onClick={() => fetchNextSection(filters)} style={styles.retryBtn}>
            {error === "No sections available" ? "View History" : "Retry"}
          </button>
        </div>
      )}

      {section && (
        <>
          <div style={styles.header}>
            <div>
              <strong>{section.bookTitle}</strong>
              <span style={styles.pageIndicator}> — Page {section.pageNumber}</span>
            </div>
            <div style={styles.actions}>
              <button onClick={() => fetchNextSection(filters)} style={styles.skipBtn}>Skip</button>
              <button onClick={handleSave} disabled={saving} style={styles.saveBtn}>
                {saving ? "Saving..." : "Submit Translation"}
              </button>
            </div>
          </div>

          <div style={styles.topRow}>
            <div style={styles.imageColumn}>
              <div
                ref={scrollRef}
                style={{
                  ...styles.sectionImageScroll,
                  cursor: isDragging ? "grabbing" : "grab",
                }}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
              >
                <div style={styles.sectionImageInner}>
                  {section.croppedImageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={section.croppedImageUrl}
                      alt="Section"
                      draggable={false}
                      style={{
                        width: `${zoom}%`,
                        display: "block",
                        pointerEvents: "none",
                      }}
                    />
                  ) : (
                    <div style={styles.imagePlaceholder}>
                      <p>Section Image</p>
                      <p style={{ fontSize: 12, color: "var(--muted)" }}>(cropped from page)</p>
                    </div>
                  )}
                </div>
              </div>
              <div style={styles.zoomControls}>
                <button onClick={handleZoomOut} style={styles.zoomBtn} aria-label="Zoom out">−</button>
                <span style={{ fontSize: 13, color: "var(--foreground)" }}>{zoom}%</span>
                <button onClick={handleZoomIn} style={styles.zoomBtn} aria-label="Zoom in">+</button>
                <button onClick={handleZoomReset} style={styles.zoomBtn} aria-label="Reset zoom">⟳</button>
              </div>
            </div>

            <div style={styles.sourceTextColumn}>
              <SourceTextPanel
                originalText={sourceText}
                aiExtractedText={aiText}
                extractionStatus={extractionStatus}
                confidence={extractionConfidence}
                isEditor={isEditor}
                bookId={section.book.id}
                pageNumber={section.pageNumber}
                zoom={sourceTextZoom}
                onZoomIn={() => setSourceTextZoom((z) => Math.min(z + 10, 300))}
                onZoomOut={() => setSourceTextZoom((z) => Math.max(z - 10, 50))}
                onZoomReset={() => setSourceTextZoom(100)}
                onExtract={handleExtract}
                sectionId={section.id}
                onSourceTextUpdate={handleSourceTextUpdate}
                aiError={aiError}
              />
            </div>
          </div>

          <div style={styles.bottomRow}>
            <div style={styles.transliterationColumn}>
              <div style={styles.panel}>
                <div style={styles.panelHeader}>
                  <span>✏️</span>
                  <span style={styles.panelTitle}>Exact Letter Transliteration</span>
                  {transliteration.source === "ai" && transliteration.text && (
                    <span style={{ ...styles.badge, background: "#16A34A", color: "#fff" }}>
                      AI Generated
                    </span>
                  )}
                  {transliteration.source === "manual" && (
                    <span style={{ ...styles.badge, background: "#6366F1", color: "#fff" }}>
                      Manual
                    </span>
                  )}
                  {transliteration.loading && (
                    <span style={{ ...styles.badge, background: "#3B82F6", color: "#fff" }}>
                      Generating...
                    </span>
                  )}
                  {transliteration.error && (
                    <span style={{ ...styles.badge, background: "#DC2626", color: "#fff" }}>
                      Unavailable
                    </span>
                  )}
                </div>

                {transliteration.loading ? (
                  <div style={styles.loadingPanel}>
                    <div style={styles.miniSpinner} />
                    <span>Generating transliteration...</span>
                  </div>
                ) : transliteration.error ? (
                  <div style={styles.errorPanel}>
                    <span>Transliteration unavailable — enter manually</span>
                  </div>
                ) : (
                  <textarea
                    value={exactLetter}
                    onChange={(e) => handleExactLetterChange(e.target.value)}
                    onKeyDown={handleExactLetterKeyDown}
                    onBlur={handleExactLetterBlur}
                    style={styles.transliterationArea}
                    placeholder="e.g. මාතා → मාතා (letter-for-letter)"
                    aria-label="Exact letter transliteration"
                  />
                )}

                <div style={styles.panelActions}>
                  {activeSourceText && !transliteration.text && !transliteration.loading && (
                    <button onClick={() => handleTransliterate()} style={styles.generateBtn} disabled={transliterating}>
                      Generate with AI
                    </button>
                  )}
                  {transliteration.text && !transliteration.loading && (
                    <button onClick={() => handleTransliterate(true)} style={styles.regenerateBtn} disabled={transliterating}>
                      Regenerate
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div style={styles.translationColumn}>
              <div style={styles.panel}>
                <div style={styles.panelHeader}>
                  <span>📝</span>
                  <span style={styles.panelTitle}>Your Translation *</span>
                  <button onClick={handleAutoTranslate} disabled={autoTranslating} style={styles.autoTranslateBtn}>
                    {autoTranslating ? "Translating..." : "Auto Translate"}
                  </button>
                </div>
                <textarea
                  value={translatedText}
                  onChange={(e) => updateText(e.target.value)}
                  style={styles.translationArea}
                  placeholder="Enter your translation here..."
                  aria-label="Your translation"
                />
              </div>

              <DraftSaveIndicator visible={showSavedIndicator} />

              {successMessage && (
                <div style={styles.successBox}>{successMessage}</div>
              )}
            </div>
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

          <div style={styles.pageContext}>
            <span style={{ fontSize: 13, color: "var(--muted)" }}>
              Page {section.pageNumber}
            </span>
          </div>
        </>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 64,
    color: "var(--muted)",
  },
  spinner: {
    width: 20,
    height: 20,
    border: "2px solid var(--border)",
    borderTopColor: "var(--primary)",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  emptyState: {
    textAlign: "center",
    padding: 64,
    color: "var(--muted)",
  },
  emptyIcon: {
    fontSize: 32,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 600,
    marginBottom: 8,
    color: "var(--foreground)",
  },
  emptyDesc: {
    fontSize: 14,
    lineHeight: 1.5,
    marginBottom: 16,
  },
  retryBtn: {
    padding: "8px 24px",
    background: "var(--primary)",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 16px",
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
    fontSize: 14,
  },
  pageIndicator: {
    color: "var(--muted)",
  },
  actions: {
    display: "flex",
    gap: 8,
  },
  skipBtn: {
    padding: "6px 16px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
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
  topRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 16,
  },
  imageColumn: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  sourceTextColumn: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  sectionImageScroll: {
    border: "1px solid var(--border)",
    borderRadius: 8,
    overflow: "hidden",
    maxHeight: 400,
    background: "var(--surface)",
    userSelect: "none",
    touchAction: "none",
  },
  sectionImageInner: {
    padding: 8,
    minWidth: 0,
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
    border: "1px solid var(--border)",
    borderRadius: 8,
  },
  zoomBtn: {
    width: 28,
    height: 28,
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 16,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  bottomRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 16,
  },
  transliterationColumn: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  translationColumn: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  panel: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    padding: 12,
    border: "1px solid var(--border)",
    borderRadius: 8,
    background: "var(--surface)",
  },
  panelHeader: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 13,
    fontWeight: 600,
    color: "var(--muted)",
  },
  panelTitle: {
    fontSize: 13,
    fontWeight: 600,
  },
  badge: {
    marginLeft: 8,
    padding: "2px 8px",
    borderRadius: 12,
    fontSize: 11,
    fontWeight: 600,
  },
  panelActions: {
    display: "flex",
    gap: 8,
  },
  generateBtn: {
    padding: "6px 14px",
    border: "none",
    borderRadius: 6,
    background: "var(--primary)",
    color: "#fff",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 600,
  },
  regenerateBtn: {
    padding: "6px 14px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--background)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 13,
  },
  autoTranslateBtn: {
    marginLeft: "auto",
    padding: "4px 12px",
    border: "1px solid var(--border)",
    borderRadius: 6,
    background: "var(--surface)",
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 12,
  },
  transliterationArea: {
    padding: 12,
    border: "1px solid var(--border)",
    borderRadius: 8,
    fontSize: 14,
    lineHeight: 1.6,
    minHeight: 100,
    resize: "vertical",
    background: "var(--background)",
    color: "var(--foreground)",
    fontFamily: "monospace",
  },
  translationArea: {
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
  loadingPanel: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    padding: 24,
    color: "var(--muted)",
    fontSize: 13,
  },
  errorPanel: {
    padding: 16,
    color: "#DC2626",
    fontSize: 13,
    textAlign: "center",
  },
  miniSpinner: {
    width: 14,
    height: 14,
    border: "2px solid var(--border)",
    borderTopColor: "var(--primary)",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  fieldLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--muted)",
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
  successBox: {
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
}
