import { redirect } from "next/navigation"

export default async function SectionTranslatePage({
  params,
}: {
  params: Promise<{ sectionId: string }>
}) {
  const { sectionId } = await params
  redirect(`/translate?section=${sectionId}`)
}
