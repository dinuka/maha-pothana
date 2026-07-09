import { apiFetchBrowser } from "@/lib/apiClientBrowser"

export interface BookStatsSummary {
  totalSections: number
  translatedSections: number
  inProgressSections: number
  pendingSections: number
  translationPercent: number
}

export interface BookListItem {
  id: string
  title: string
  author: string
  sourceLanguage: string
  translateLanguages: string[]
  status: string
  thumbnailKey: string | null
  pageCount: number
  stats: BookStatsSummary
}

export interface BookDetail {
  id: string
  title: string
  author: string
  sourceLanguage: string
  translateLanguages: string[]
  description: string | null
  status: string
}

export const getAvailableBooks = async (): Promise<BookListItem[]> => {
  const res = await apiFetchBrowser("/api/books/available")
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}

export const getBook = async (bookId: string): Promise<BookDetail> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}`)
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}
