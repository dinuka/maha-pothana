FROM node:20-alpine AS base
RUN corepack enable
WORKDIR /app
COPY pnpm-lock.yaml ./
RUN pnpm fetch

FROM base AS builder
COPY . .
RUN pnpm install --frozen-lockfile --offline
ARG APP=web
RUN pnpm --filter=$APP build

FROM base AS runner
COPY --from=builder /app/apps/$APP/.next .next
COPY --from=builder /app/apps/$APP/public public
COPY --from=builder /app/apps/$APP/package.json .
EXPOSE 3000
CMD ["pnpm", "start"]
