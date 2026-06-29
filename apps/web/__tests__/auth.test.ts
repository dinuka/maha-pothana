import { describe, it, expect } from "vitest"
import { ROLES } from "@/lib/auth"
import type { Role } from "@/lib/auth"

describe("ROLES", () => {
  it("defines SUPER_ADMIN role", () => {
    expect(ROLES.SUPER_ADMIN).toBe("SUPER_ADMIN")
  })

  it("defines EDITOR role", () => {
    expect(ROLES.EDITOR).toBe("EDITOR")
  })

  it("defines TRANSLATOR role", () => {
    expect(ROLES.TRANSLATOR).toBe("TRANSLATOR")
  })

  it("is a const object with readonly values", () => {
    const keys = Object.keys(ROLES) as (keyof typeof ROLES)[]
    const values = keys.map((k) => ROLES[k])
    expect(values).toEqual(["SUPER_ADMIN", "EDITOR", "TRANSLATOR"])
  })
})

describe("Role type", () => {
  it("accepts valid role strings", () => {
    const validRoles: Role[] = ["SUPER_ADMIN", "EDITOR", "TRANSLATOR"]
    expect(validRoles).toHaveLength(3)
  })
})
