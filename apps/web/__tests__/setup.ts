import "@testing-library/jest-dom/vitest"

class IntersectionObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// @ts-expect-error jsdom has no IntersectionObserver
global.IntersectionObserver = IntersectionObserverStub
