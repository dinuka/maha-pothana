import { useCallback, useEffect, useRef, useState } from "react"
import { saveDraft as saveDraftApi, deleteDraft as deleteDraftApi } from "@/lib/api/translations"

export const useTranslationDraft = (sectionId: string | null) => {
  const [translatedText, setTranslatedText] = useState("")
  const [isDirty, setIsDirty] = useState(false)
  const [lastSavedText, setLastSavedText] = useState("")
  const [showSavedIndicator, setShowSavedIndicator] = useState(false)
  const [draftId, setDraftId] = useState<string | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const doSave = useCallback(async (text: string, currentSectionId: string) => {
    if (!text.trim()) return
    try {
      const result = await saveDraftApi({ sectionId: currentSectionId, translatedText: text })
      setDraftId(result.draftId)
      setLastSavedText(text)
      setShowSavedIndicator(true)
      setTimeout(() => setShowSavedIndicator(false), 2000)
    } catch {
      // Silent fail - localStorage fallback handled elsewhere
    }
  }, [])

  const debouncedSave = useCallback(
    (text: string) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      timeoutRef.current = setTimeout(() => {
        if (sectionId && text.trim()) {
          doSave(text, sectionId)
        }
      }, 5000)
    },
    [sectionId, doSave]
  )

  const updateText = useCallback(
    (text: string) => {
      setTranslatedText(text)
      setIsDirty(text !== lastSavedText)
      debouncedSave(text)
    },
    [lastSavedText, debouncedSave]
  )

  const resetDirty = useCallback(() => {
    setIsDirty(false)
  }, [])

  const clearDraft = useCallback(async () => {
    if (draftId) {
      try {
        await deleteDraftApi(draftId)
      } catch {
        // ignore
      }
      setDraftId(null)
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setTranslatedText("")
    setIsDirty(false)
    setLastSavedText("")
  }, [draftId])

  // beforeunload warning
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault()
        e.returnValue = ""
      }
    }
    window.addEventListener("beforeunload", handler)
    return () => window.removeEventListener("beforeunload", handler)
  }, [isDirty])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return {
    translatedText,
    setTranslatedText,
    isDirty,
    showSavedIndicator,
    updateText,
    resetDirty,
    clearDraft,
  }
}
