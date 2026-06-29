import { auth } from "@/lib/auth"
import type { Role } from "@/lib/auth"
import { NextResponse } from "next/server"

const publicRoutes = ["/auth/signin", "/api/auth"]

export default auth((req) => {
  const { pathname } = req.nextUrl
  const isPublic = publicRoutes.some((route) => pathname.startsWith(route))

  if (!isPublic && !req.auth) {
    return NextResponse.redirect(new URL("/auth/signin", req.url))
  }

  const userRoles = (req.auth?.user as unknown as { roles: Role[] })?.roles ?? []
  if (pathname.startsWith("/admin") && !userRoles.includes("SUPER_ADMIN")) {
    return NextResponse.redirect(new URL("/dashboard", req.url))
  }

  return NextResponse.next()
})

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}
