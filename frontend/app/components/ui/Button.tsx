"use client"

import type React from "react"
import styles from "./Button.module.css"

interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: "primary" | "secondary" | "accent" | "ghost"
  size?: "sm" | "md" | "lg"
  className?: string
}

/**
 * Reusable Button component with multiple variants and smooth animations
 * Supports different sizes and states with consistent styling
 */
export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  disabled = false,
  variant = "primary",
  size = "md",
  className = "",
}) => {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  )
}
