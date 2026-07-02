import { getToken } from "next-auth/jwt"
import { headers } from "next/headers"
import { publicEnv } from "./env/publicEnv"
import { serverEnv } from "./env/serverEnv"

const buildAuthHeaders = async (init?: RequestInit): Promise<RequestInit> => {
  const headerStore = await headers()
  const requestHeaders = new Headers(init?.headers)

  const token = await getToken({
    req: { headers: headerStore },
    secret: serverEnv.authSecret,
  })

  if (token?.sub) {
    requestHeaders.set("X-User-Id", token.sub)
  }
  requestHeaders.set("X-Internal-Api-Key", serverEnv.internalApiKey)

  return { ...init, headers: requestHeaders }
}

export const apiFetch = async (path: string, init?: RequestInit): Promise<Response> => {
  const requestInit = await buildAuthHeaders(init)
  return fetch(`${publicEnv.apiUrl}${path}`, requestInit)
}
