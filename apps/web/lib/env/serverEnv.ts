import "server-only"

const required = (name: string, value: string | undefined): string => {
  if (!value) throw new Error(`Missing required env var: ${name}`)
  return value
}

export const serverEnv = {
  authSecret: required("AUTH_SECRET", process.env.AUTH_SECRET),
  authGoogleId: required("AUTH_GOOGLE_ID", process.env.AUTH_GOOGLE_ID),
  authGoogleSecret: required("AUTH_GOOGLE_SECRET", process.env.AUTH_GOOGLE_SECRET),
  internalApiKey: required("INTERNAL_API_KEY", process.env.INTERNAL_API_KEY),
}
