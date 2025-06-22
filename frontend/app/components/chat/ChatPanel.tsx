"use client"

import type React from "react"
import { useRef, useEffect } from "react"
import { Card } from "../ui/Card"
import { Button } from "../ui/Button"
import { Input } from "../ui/Input"
import { MessageCard } from "./MessageCard"
import styles from "./ChatPanel.module.css"

interface Message {
  id: string
  text: string
  sender: "user" | "bot"
  created_at: string
}

interface ChatPanelProps {
  messages: Message[]
  currentMessage: string
  onMessageChange: (message: string) => void
  onSendMessage: () => void
  onActionClick: (action: string) => void
  userName: string
  onSignOut: () => void
}

/**
 * Main chat panel component with message history and input
 * Handles user interactions and displays conversation flow
 */
export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  currentMessage,
  onMessageChange,
  onSendMessage,
  onActionClick,
  userName,
  onSignOut,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSendMessage()
    }
  }

  return (
    <div className={styles.chatPanel}>
      {/* Header with user info and sign out */}
      <Card variant="elevated" className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.userInfo}>
            <div className={styles.avatar}>
              <img src="/favicon.ico" alt="Logo" className={styles.logo} />
            </div>
            <div>
              <h2 className={styles.title}>Twinstack</h2>
              <p className={styles.subtitle}>{userName}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onSignOut}>
            Sign Out
          </Button>
        </div>
      </Card>


      {/* Messages area with scroll */}
      <div className={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>💬</div>
            <h3 className={styles.emptyTitle}>Ready to start</h3>
            <p className={styles.emptyDescription}>Describe what you want to build and I'll help you create it</p>
          </div>
        ) : (
          <div className={styles.messages}>
            {messages.map((msg) => (
              <MessageCard
                key={msg.id}
                message={msg.text}
                type={msg.sender === "user" ? "input" : "output"}
                timestamp={new Date(msg.created_at).toLocaleTimeString()}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <Card variant="elevated" className={styles.inputCard}>
        <div className={styles.inputContainer}>
          <Input
            value={currentMessage}
            onChange={onMessageChange}
            placeholder="Describe what you want to build..."
            multiline
            rows={1}
            className={styles.messageInput}
          />
          <Button
            variant="accent"
            onClick={onSendMessage}
            disabled={!currentMessage.trim()}
            className={styles.sendButton}
          >
            Generate
          </Button>
        </div>
      </Card>
    </div>
  )
}
