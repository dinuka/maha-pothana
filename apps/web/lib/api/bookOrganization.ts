import { apiFetchBrowser } from "@/lib/apiClientBrowser"
import { BuildStatus, VersionStatus } from "@/lib/types"

// ── Translation Review ────────────────────────────────────────────────────────

export const approveTranslation = async (
  translationId: string,
): Promise<{ success: boolean; translation: Record<string, unknown> }> => {
  const res = await apiFetchBrowser(`/api/translations/${translationId}/approve`, {
    method: "PUT",
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Failed to approve translation (${res.status})`)
  }
  return res.json()
}

export const rejectTranslation = async (
  translationId: string,
  reason?: string,
): Promise<{ success: boolean; translation: Record<string, unknown> }> => {
  const body = reason ? { reason } : undefined
  const res = await apiFetchBrowser(`/api/translations/${translationId}/reject`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Failed to reject translation (${res.status})`)
  }
  return res.json()
}

export const editorOverrideTranslation = async (
  sectionId: string,
  body: { translatedText: string; sourceTranslationId?: string },
): Promise<{
  id: string
  sectionId: string
  translatorId: string
  translatorName: string | null
  isApproved: boolean
  isEditorOverride: boolean
  translatedText: string
  createdAt: string
}> => {
  const res = await apiFetchBrowser(`/api/sections/${sectionId}/translations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Failed to submit editor override (${res.status})`)
  }
  return res.json()
}

// ── Page Organization ─────────────────────────────────────────────────────

export interface ReorderPageItem {
  pageId: string
  order: number
}

export interface ReorderPagesResponse {
  success: boolean
  reorderedCount: number
  pages: Array<{ id: string; order: number; pageNumber: number }>
}

export const reorderPages = async (
  bookId: string,
  orders: ReorderPageItem[],
): Promise<ReorderPagesResponse> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}/pages/reorder`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ orders }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Failed to reorder pages (${res.status})`)
  }
  return res.json()
}

export interface AddPageResponse {
  id: string
  bookId: string
  pageNumber: number
  originalPageNumber: string
  order: number
  status: string
  createdAt: string
}

export const addBlankPage = async (
  bookId: string,
  insertAfterOrder: number,
): Promise<AddPageResponse> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}/pages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ insertAfterOrder }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Failed to add page (${res.status})`)
  }
  return res.json()
}

export interface DeletePageResponse {
  success: boolean
  deleted: Record<string, number>
}

export const deletePage = async (pageId: string): Promise<DeletePageResponse> => {
  const res = await apiFetchBrowser(`/api/pages/${pageId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Failed to delete page (${res.status})`)
  }
  return res.json()
}

export interface PageHistoryEntry {
  id: string
  editorId: string
  editorName: string
  action: string
  snapshot: { sections: Array<Record<string, unknown>> }
  timestamp: string
}

export interface PageHistoryResponse {
  pageId: string
  history: PageHistoryEntry[]
}

export const getPageHistory = async (pageId: string): Promise<PageHistoryResponse> => {
  const res = await apiFetchBrowser(`/api/pages/${pageId}/history`)
  if (!res.ok) {
    throw new Error(`Failed to fetch page history (${res.status})`)
  }
  return res.json()
}

// ── Build & Versioning ────────────────────────────────────────────────────────

export interface TriggerBuildResponse {
  status: BuildStatus
  versionNumber: number
  buildId: string
}

export const triggerBuild = async (bookId: string): Promise<TriggerBuildResponse> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}/build`, {
    method: "POST",
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Failed to trigger build (${res.status})`)
  }
  return res.json()
}

export interface BuildProgress {
  id?: string
  bookId?: string
  status: BuildStatus
  versionNumber?: number
  currentPage?: number
  totalPages?: number
  estimatedRemainingMs?: number
  startedAt?: string
  totalSections?: number
  approvedSections?: number
  buildDurationMs?: number
  fileKey?: string
  completedAt?: string
  errorMessage?: string
  failedAt?: string
  message?: string
}

export const getLatestBuild = async (bookId: string): Promise<BuildProgress> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}/builds/latest`)
  if (!res.ok) {
    throw new Error(`Failed to fetch build status (${res.status})`)
  }
  return res.json()
}

export const cancelBuild = async (
  bookId: string,
): Promise<{ success: boolean; message: string }> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}/builds/latest`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Failed to cancel build (${res.status})`)
  }
  return res.json()
}

export interface BuildListItem {
  id: string
  versionNumber: number
  status: BuildStatus
  totalSections?: number
  approvedSections?: number
  buildDurationMs?: number
  createdBy?: { id: string; name: string } | null
  createdAt?: string
  completedAt?: string
}

export interface BuildListResponse {
  builds: BuildListItem[]
  pagination: { page: number; limit: number; total: number; totalPages: number }
}

export const getBuilds = async (
  bookId: string,
  page?: number,
  limit?: number,
): Promise<BuildListResponse> => {
  const params = new URLSearchParams()
  if (page) params.set("page", String(page))
  if (limit) params.set("limit", String(limit))
  const qs = params.toString()
  const res = await apiFetchBrowser(`/api/books/${bookId}/builds${qs ? `?${qs}` : ""}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch builds (${res.status})`)
  }
  return res.json()
}

export interface VersionListItem {
  versionNumber: number
  label?: string
  status: VersionStatus
  buildId?: string
  changelog?: string
  createdBy?: { id: string; name: string } | null
  totalSections?: number
  approvedSections?: number
  createdAt?: string
  hasMarkdown: boolean
  hasHtml: boolean
}

export interface VersionListResponse {
  versions: VersionListItem[]
}

export const getVersions = async (bookId: string): Promise<VersionListResponse> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}/versions`)
  if (!res.ok) {
    throw new Error(`Failed to fetch versions (${res.status})`)
  }
  return res.json()
}

export interface DownloadResponse {
  downloadUrl: string
  filename: string
  expiresAt: string
  versionNumber: number
}

export const getDownloadUrl = async (
  bookId: string,
  versionNumber: number,
): Promise<DownloadResponse> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}/versions/${versionNumber}/download`)
  if (!res.ok) {
    throw new Error(`Failed to fetch download URL (${res.status})`)
  }
  return res.json()
}

export const getMarkdownDownloadUrl = async (
  bookId: string,
  versionNumber: number,
): Promise<DownloadResponse> => {
  const res = await apiFetchBrowser(
    `/api/books/${bookId}/versions/${versionNumber}/download-markdown`,
  )
  if (!res.ok) {
    throw new Error(`Failed to fetch markdown download URL (${res.status})`)
  }
  return res.json()
}

export const getHtmlDownloadUrl = async (
  bookId: string,
  versionNumber: number,
): Promise<DownloadResponse> => {
  const res = await apiFetchBrowser(`/api/books/${bookId}/versions/${versionNumber}/download-html`)
  if (!res.ok) {
    throw new Error(`Failed to fetch HTML download URL (${res.status})`)
  }
  return res.json()
}
