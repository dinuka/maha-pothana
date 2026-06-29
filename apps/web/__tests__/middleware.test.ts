import { describe, it, expect } from "vitest"
import { config } from "@/proxy"

describe("middleware config", () => {
  it("has a matcher that excludes static assets", () => {
    expect(config.matcher).toHaveLength(1)
    expect(config.matcher[0]).toContain("_next/static")
    expect(config.matcher[0]).toContain("favicon.ico")
  })

  it("negatively matches Next.js static routes", () => {
    const matcher = config.matcher[0]
    expect(matcher).toContain("_next/static")
    expect(matcher).toContain("_next/image")
    expect(matcher).toContain("favicon.ico")
  })
})
