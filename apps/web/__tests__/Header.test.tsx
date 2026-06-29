import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import React from "react"

vi.mock("next-auth/react", () => ({
  signOut: vi.fn(),
}))

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) =>
    React.createElement("a", { href }, children),
}))

// Must import after mocks
import Header from "@/components/Header"

describe("Header", () => {
  it("returns null when no user is provided", () => {
    const { container } = render(React.createElement(Header))
    expect(container.innerHTML).toBe("")
  })

  it("renders dashboard link always", () => {
    render(React.createElement(Header, { user: { name: "Test User", email: "test@test.com", image: null } }))
    expect(screen.getByText("Dashboard")).toBeInTheDocument()
  })

  it("shows Books link for editor", () => {
    const user = { name: "Editor", email: "editor@test.com", image: null, roles: ["EDITOR"] } as never
    render(React.createElement(Header, { user }))
    expect(screen.getByText("Books")).toBeInTheDocument()
  })

  it("shows Translate link for translator", () => {
    const user = { name: "Translator", email: "translator@test.com", image: null, roles: ["TRANSLATOR"] } as never
    render(React.createElement(Header, { user }))
    expect(screen.getByText("Translate")).toBeInTheDocument()
  })

  it("shows Admin link for super admin", () => {
    const user = { name: "Root", email: "admin@test.com", image: null, roles: ["SUPER_ADMIN"] } as never
    render(React.createElement(Header, { user }))
    expect(screen.getByRole("link", { name: "Admin" })).toBeInTheDocument()
  })

  it("hides Books link from translator-only user", () => {
    const user = { name: "Translator", email: "translator@test.com", image: null, roles: ["TRANSLATOR"] } as never
    render(React.createElement(Header, { user }))
    expect(screen.queryByText("Books")).not.toBeInTheDocument()
  })

  it("displays user name", () => {
    render(React.createElement(Header, { user: { name: "Jane Doe", email: "jane@test.com", image: null } }))
    expect(screen.getByText("Jane Doe")).toBeInTheDocument()
  })

  it("shows sign out button", () => {
    render(React.createElement(Header, { user: { name: "User", email: "user@test.com", image: null } }))
    expect(screen.getByText("Sign out")).toBeInTheDocument()
  })
})
