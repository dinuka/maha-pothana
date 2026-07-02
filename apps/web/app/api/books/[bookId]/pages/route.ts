import { apiFetch } from "@/lib/apiClient"

export const GET = async (req: Request, { params }: { params: Promise<{ bookId: string }> }) => {
  const { bookId } = await params
  const { search } = new URL(req.url)
  const res = await apiFetch(`/api/books/${bookId}/pages${search}`, { cache: "no-store" })
  const data = await res.json()
  return Response.json(data, { status: res.status })
}
