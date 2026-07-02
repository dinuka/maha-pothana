import { apiFetch } from "@/lib/apiClient"

export const GET = async () => {
  const res = await apiFetch("/api/books", { cache: "no-store" })
  const data = await res.json()
  return Response.json(data, { status: res.status })
}
