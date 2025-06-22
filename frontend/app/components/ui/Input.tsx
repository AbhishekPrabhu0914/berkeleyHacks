import type React from "react"
import styles from "./Input.module.css"

interface InputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  multiline?: boolean
  rows?: number
  className?: string
}

/**
 * Input component with smooth focus states and modern styling
 * Supports both single-line and multiline text input
 */
export const Input: React.FC<InputProps> = ({
  value,
  onChange,
  placeholder,
  disabled = false,
  multiline = false,
  rows = 1,
  className = "",
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    onChange(e.target.value)
  }

  const commonProps = {
    value,
    onChange: handleChange,
    placeholder,
    disabled,
    className: `${styles.input} ${className}`,
  }

  if (multiline) {
    return <textarea {...commonProps} rows={rows} style={{ resize: "none", minHeight: "44px", maxHeight: "120px" }} />
  }

  return <input type="text" {...commonProps} />
}
