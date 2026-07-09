import { publicEnv } from "./env/publicEnv"

let cachedToken: string | null = null
let tokenPromise: Promise<string> | null = null

const fetchToken = async (): Promise<string> => {
  const res = await fetch("/api/auth/token")
  if (!res.ok) throw new Error("Not authenticated")
  const { token } = (await res.json()) as { token: string }
  return token
}

const getToken = async (): Promise<string> => {
  if (cachedToken) return cachedToken
  if (!tokenPromise) {
    tokenPromise = fetchToken().then((t) => {
      cachedToken = t
      setTimeout(
        () => {
          cachedToken = null
          tokenPromise = null
        },
        14 * 60 * 1000,
      ) // refresh before 15min expiry
      return t
    })
  }
  return tokenPromise
}

export const apiFetchBrowser = async (path: string, init?: RequestInit): Promise<Response> => {
  const token = await getToken()
  const headers = new Headers(init?.headers)
  headers.set("Authorization", `Bearer ${token}`)
  return fetch(`${publicEnv.apiUrl}${path}`, { ...init, headers })
}
