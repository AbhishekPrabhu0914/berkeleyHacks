import type React from "react"
import styles from "./Card.module.css"

interface CardProps {
  children: React.ReactNode
  className?: string
  variant?: "default" | "elevated" | "bordered"
}

/**
 * Card component with soft shadows and rounded corners
 * Provides consistent container styling throughout the app
 */
export const Card: React.FC<CardProps> = ({ children, className = "", variant = "default" }) => {
  return <div className={`${styles.card} ${styles[variant]} ${className}`}>{children}</div>
}
