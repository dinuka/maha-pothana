import type { Metadata } from "next"
import { SessionProvider } from "next-auth/react"
import { auth } from "@/lib/auth"
import Header from "@/components/Header"
import "./globals.css"

export const metadata: Metadata = {
  title: "Maha Pothana",
  description: "Community-driven book translation platform",
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const session = await auth()

  return (
    <html lang="en">
      <body>
        <SessionProvider session={session}>
          <Header user={session?.user} />
          <main>{children}</main>
        </SessionProvider>
      </body>
    </html>
  )
}
