import { apiFetchBrowser } from "@/lib/apiClientBrowser"

export interface PageImageResponse {
  pageNumber: number
  imageUrl: string | null
  totalPages: number
}

export const getPageImage = async (
  bookId: string,
  pageNumber: number,
): Promise<PageImageResponse> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}/pages/${pageNumber}/image`)
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  return res.json()
}
