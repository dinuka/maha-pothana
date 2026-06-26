# maha-pothana

## Repo structure

```
apps/web      — Next.js App Router, port 3000
apps/docs     — Next.js App Router, port 3001
packages/ui   — @repo/ui (shared React components, named exports via "./*" → "./src/*.tsx")
packages/eslint-config — @repo/eslint-config (flat config, ESLint 9)
packages/typescript-config — @repo/typescript-config
```

## Commands (run from root)

| Command | Effect |
|---------|--------|
| `pnpm dev` | Start all dev servers (web:3000, docs:3001) |
| `pnpm build` | Build all packages & apps |
| `pnpm lint` | Turbo lint (strict: `--max-warnings 0`) |
| `pnpm check-types` | Turbo typecheck (`next typegen && tsc --noEmit`) |
| `pnpm format` | Prettier across `**/*.{ts,tsx,md}` |
| `pnpm --filter=web <script>` | Run script for a single app/package |

## Key facts

- **Package manager**: pnpm (not npm/yarn). Use `pnpm add` / `pnpm remove`.
- **Internal deps**: use `workspace:*` protocol (e.g. `"@repo/ui": "workspace:*"`).
- **No test framework** is configured anywhere. Do not look for or expect tests.
- **ESLint 9 flat config** — `eslint.config.js`/`.mjs`, not `.eslintrc.*`.
- **ESLint pinned to 9.x** because `eslint-plugin-react` doesn't support ESLint 10 yet.
- **CSS Modules**: page-level styles use `*.module.css`.
- **Environment files** (`.env*`) are gitignored and not committed.
- **No CI** workflows exist (no `.github/`).

## Component conventions (packages/ui)

- Use `turbo gen react-component` to scaffold new components.
- Components use **named exports** (`export const Button = ...`), not `export default`.
- Internal package exports: `@repo/ui/button` (not `@repo/ui` barrel).

## Coding style

Follow `~/.claude/CLAUDE.md` conventions (in user home, not repo). Key rules from there:
- Arrow functions, no `function` keyword.
- `const`/`let`, no `var`.
- `import`, no `require`.
- PascalCase for components, camelCase for utils/variables.
- Named exports unless file name matches export name (then default export).
- Avoid `any`, use destructuring, minimize optional chaining on mandatory fields.
- Folder names: camelCase for generic, kebab-case for page routes.
