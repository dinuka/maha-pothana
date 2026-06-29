import NextAuth from "next-auth"
import type { NextAuthResult } from "next-auth"
import Google from "next-auth/providers/google"

export const ROLES = {
  SUPER_ADMIN: "SUPER_ADMIN",
  EDITOR: "EDITOR",
  TRANSLATOR: "TRANSLATOR",
} as const

export type Role = (typeof ROLES)[keyof typeof ROLES]

interface AuthUser {
  id: string
  name?: string | null
  email?: string | null
  image?: string | null
  roles: Role[]
}

const result: NextAuthResult = NextAuth({
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID!,
      clientSecret: process.env.AUTH_GOOGLE_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google") {
        const authUser = user as unknown as AuthUser
        try {
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              googleId: account.providerAccountId,
              email: user.email,
              name: user.name,
              avatarUrl: user.image,
            }),
          })
          if (res.ok) {
            const data = (await res.json()) as { user: AuthUser }
            authUser.id = data.user.id
            authUser.roles = data.user.roles
          }
        } catch {
          authUser.roles = [ROLES.EDITOR, ROLES.TRANSLATOR]
        }
      }
      return true
    },
    async jwt({ token, user }) {
      if (user) {
        const authUser = user as unknown as AuthUser
        Object.assign(token, { roles: authUser.roles ?? [ROLES.EDITOR, ROLES.TRANSLATOR], id: authUser.id })
      }
      return token
    },
    async session({ session, token }) {
      const tokenData = token as unknown as { roles: Role[]; id: string }
      Object.assign(session.user, { roles: tokenData.roles ?? [ROLES.EDITOR, ROLES.TRANSLATOR], id: tokenData.id ?? "" })
      return session
    },
  },
  pages: {
    signIn: "/auth/signin",
  },
})

export const { handlers, auth, signIn, signOut } = result
