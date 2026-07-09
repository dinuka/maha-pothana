import { useCallback, useMemo } from "react"
import { useRouter, useSearchParams } from "next/navigation"

export interface TranslationFilters {
  tab: string
  bookId: string | null
  language: string | null
  page: number | null
  status: string | null
  sectionId?: string
}

export const useTranslationFilters = () => {
  const router = useRouter()
  const searchParams = useSearchParams()

  const filters: TranslationFilters = useMemo(
    () => ({
      tab: searchParams.get("tab") ?? "translate",
      bookId: searchParams.get("bookId"),
      language: searchParams.get("language"),
      page: searchParams.get("page") ? Number(searchParams.get("page")) : null,
      status: searchParams.get("status"),
    }),
    [searchParams],
  )

  const setFilters = useCallback(
    (updates: Partial<TranslationFilters>) => {
      const params = new URLSearchParams(searchParams.toString())
      Object.entries(updates).forEach(([key, value]) => {
        if (value === null || value === "" || value === undefined) {
          params.delete(key)
        } else {
          params.set(key, String(value))
        }
      })
      router.push(`?${params.toString()}`, { scroll: false })
    },
    [router, searchParams],
  )

  const clearFilters = useCallback(() => {
    const tab = searchParams.get("tab")
    const params = new URLSearchParams()
    if (tab) params.set("tab", tab)
    router.push(`?${params.toString()}`, { scroll: false })
  }, [router, searchParams])

  return { filters, setFilters, clearFilters }
}
