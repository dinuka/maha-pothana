import { apiFetchBrowser } from "@/lib/apiClientBrowser"

export interface TranslationHistoryItem {
  translationId: string
  sectionId: string
  pageNumber: number
  sectionOrder: number
  translatorId: string
  translatorName: string
  translatedText: string
  action: "SUBMITTED" | "APPROVED" | "REJECTED"
  performedBy: string | null
  performedByName: string | null
  createdAt: string
}

export interface TranslationHistoryResponse {
  items: TranslationHistoryItem[]
  nextCursor: string | null
  hasMore: boolean
}

export interface LanguageStats {
  total: number
  translated: number
  percent: number
}

export interface PageStats {
  pageNumber: number
  total: number
  translated: number
  percent: number
}

export interface TranslationStatsResponse {
  totalSections: number
  translatedSections: number
  pendingSections: number
  inProgressSections: number
  translationPercent: number
  byLanguage: Record<string, LanguageStats>
  byPage: PageStats[]
}

export interface TranslatorStatsResponse {
  userId: string
  userName: string
  totalAssigned: number
  approvedCount: number
  rejectedCount: number
  pendingCount: number
  approvalRate: number | null
  avgTurnaroundHours: number | null
  lastActiveAt: string | null
}

export interface DraftResponse {
  draftId: string
  translatedText: string
  updatedAt: string
}

export interface NextSectionResponse {
  id: string
  type: string
  originalText: string | null
  aiExtractedText: string | null
  exactLetterTranslation: string | null
  autoTranslatedText: string | null
  wordByWordMeaning: string | null
  fullMeaning: string | null
  simplifiedMeaning: string | null
  pageNumber: number
  bookTitle: string
  book: { id: string; sourceLanguage: string | null }
  croppedImageUrl: string | null
}

export interface VerseAnalysisResponse {
  wordByWordMeaning: string
  fullMeaning: string
  simplifiedMeaning: string
}

const fetchApi = async <T>(path: string, options?: RequestInit): Promise<T> => {
  const res = await apiFetchBrowser(path, options)
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}

export const getNextSection = (params: {
  bookId?: string
  language?: string
  page?: number
  status?: string
}) => {
  const searchParams = new URLSearchParams()
  if (params.bookId) searchParams.set("bookId", params.bookId)
  if (params.language) searchParams.set("language", params.language)
  if (params.page) searchParams.set("page", String(params.page))
  if (params.status) searchParams.set("status", params.status)
  const qs = searchParams.toString()
  return fetchApi<NextSectionResponse>(`/api/sections/next${qs ? `?${qs}` : ""}`)
}

export const analyzeSection = (sectionId: string) =>
  fetchApi<VerseAnalysisResponse>(`/api/sections/${sectionId}/analyze`, {
    method: "POST",
  })

export const getMyTranslation = (sectionId: string) =>
  fetchApi<{ translatedText: string; exactLetterTranslation: string | null; isApproved: boolean }>(
    `/api/sections/${sectionId}/my-translation`,
  )

export const submitTranslation = (
  sectionId: string,
  body: { translatedText: string; exactLetterTranslation?: string | null },
) =>
  fetchApi<{ status: string }>(`/api/sections/${sectionId}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

export const getTranslationHistory = (params: {
  bookId: string
  translatorId?: string
  language?: string
  page?: number
  status?: string
  cursor?: string
  limit?: number
}) => {
  const searchParams = new URLSearchParams()
  searchParams.set("bookId", params.bookId)
  if (params.translatorId) searchParams.set("translatorId", params.translatorId)
  if (params.language) searchParams.set("language", params.language)
  if (params.page) searchParams.set("page", String(params.page))
  if (params.status) searchParams.set("status", params.status)
  if (params.cursor) searchParams.set("cursor", params.cursor)
  if (params.limit) searchParams.set("limit", String(params.limit))
  return fetchApi<TranslationHistoryResponse>(
    `/api/translations/history?${searchParams.toString()}`,
  )
}

export const getBookStats = (bookId: string) =>
  fetchApi<TranslationStatsResponse>(`/api/books/${bookId}/stats`)

export const getTranslatorStats = (bookId: string) =>
  fetchApi<TranslatorStatsResponse[]>(`/api/books/${bookId}/translators/stats`)

export const getDraft = (sectionId: string) =>
  fetchApi<DraftResponse>(`/api/translations/draft?sectionId=${sectionId}`)

export const saveDraft = (body: { sectionId: string; translatedText: string }) =>
  fetchApi<DraftResponse>("/api/translations/draft", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

export const deleteDraft = (draftId: string) =>
  fetchApi<{ status: string }>(`/api/translations/draft/${draftId}`, {
    method: "DELETE",
  })
