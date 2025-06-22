import type React from "react"
import { Card } from "../ui/Card"
import styles from "./MessageCard.module.css"

interface MessageCardProps {
  message: string
  type: "input" | "output"
  timestamp?: string
}

/**
 * Message card component for displaying chat messages
 * Differentiates between user input and AI output with visual styling
 */
export const MessageCard: React.FC<MessageCardProps> = ({ message, type, timestamp }) => {
  return (
    <div className={styles.messageContainer}>
      <div className={styles.messageHeader}>
        <div className={`${styles.indicator} ${styles[type]}`} />
        <span className={styles.label}>{type === "input" ? "Input" : "Output"}</span>
        {timestamp && <span className={styles.timestamp}>{timestamp}</span>}
      </div>
      <Card variant="bordered" className={styles.messageCard}>
        <p className={styles.messageText}>{message}</p>
      </Card>
    </div>
  )
}
