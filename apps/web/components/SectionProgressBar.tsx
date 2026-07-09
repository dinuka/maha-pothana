import styles from "./SectionProgressBar.module.css"

interface SectionProgressBarProps {
  approved: number
  inProgress: number
  pending: number
  total: number
  size?: "sm" | "md"
  showLabel?: boolean
}

export const SectionProgressBar = ({
  approved,
  inProgress,
  pending,
  total,
  size = "sm",
  showLabel = false,
}: SectionProgressBarProps) => {
  if (total === 0) {
    return <div className={styles.empty}>Not started</div>
  }

  const percent = Math.round((approved / total) * 100)
  const trackClass = size === "md" ? styles.trackMd : styles.trackSm
  const labelClass = size === "md" ? styles.labelMd : styles.labelSm

  return (
    <div className={styles.wrapper}>
      <div
        className={`${styles.track} ${trackClass}`}
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Translation progress: ${percent}% approved. ${approved} approved, ${inProgress} in progress, ${pending} pending, ${total} total`}
      >
        <div
          className={`${styles.segment} ${styles.approved}`}
          style={{ width: `${(approved / total) * 100}%` }}
        />
        <div
          className={`${styles.segment} ${styles.inProgress}`}
          style={{ width: `${(inProgress / total) * 100}%` }}
        />
      </div>
      {showLabel && <span className={labelClass}>{percent}%</span>}
    </div>
  )
}
