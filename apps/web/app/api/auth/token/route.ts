import { SignJWT } from "jose"
import { getToken } from "next-auth/jwt"
import { headers } from "next/headers"
import { serverEnv } from "@/lib/env/serverEnv"

export const GET = async () => {
  const headerStore = await headers()
  const token = await getToken({
    req: { headers: headerStore },
    secret: serverEnv.authSecret,
  })

  if (!token?.sub) {
    return Response.json({ error: "Unauthenticated" }, { status: 401 })
  }

  const secret = new TextEncoder().encode(serverEnv.authSecret)
  const uploadToken = await new SignJWT({ sub: token.sub })
    .setProtectedHeader({ alg: "HS256" })
    .setExpirationTime("15m")
    .sign(secret)

  return Response.json({ token: uploadToken })
}
