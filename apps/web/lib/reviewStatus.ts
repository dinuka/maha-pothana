import { ReviewStatus } from "@/lib/types"

export const REVIEW_STATUS_ORDER: ReviewStatus[] = [
  ReviewStatus.REJECTED,
  ReviewStatus.NOT_STARTED,
  ReviewStatus.NO_TRANSLATIONS,
  ReviewStatus.PARTIALLY_TRANSLATED,
  ReviewStatus.FULLY_TRANSLATED,
  ReviewStatus.PARTIALLY_APPROVED,
  ReviewStatus.FULLY_APPROVED,
]

export const REVIEW_STATUS_TITLES: Record<ReviewStatus, string> = {
  [ReviewStatus.REJECTED]: "Needs Retranslation (Rejected)",
  [ReviewStatus.NOT_STARTED]: "Not Started",
  [ReviewStatus.NO_TRANSLATIONS]: "No Translations Yet",
  [ReviewStatus.PARTIALLY_TRANSLATED]: "Partially Translated",
  [ReviewStatus.FULLY_TRANSLATED]: "Fully Translated (Awaiting Review)",
  [ReviewStatus.PARTIALLY_APPROVED]: "Partially Approved",
  [ReviewStatus.FULLY_APPROVED]: "Fully Approved",
}
