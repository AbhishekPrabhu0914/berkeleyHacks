"use client"

import { useState, useEffect } from "react"
import { createClient } from "@supabase/supabase-js"
import { Button } from "./components/ui/Button"
import { Card } from "./components/ui/Card"
import { ChatPanel } from "./components/chat/ChatPanel"
import { PreviewPanel } from "./components/preview/PreviewPanel"
import type { User } from "./types/User"
import styles from "./page.module.css"

interface Message {
  id: string
  text: string
  sender: "user" | "bot"
  created_at: string
}

const supabase = createClient(
  'https://suqfupehkzxtpqqghpaq.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN1cWZ1cGVoa3p4dHBxcWdocGFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA1MzY3NjcsImV4cCI6MjA2NjExMjc2N30.Vt3iK170uwYfI7PwlA17S8lvhrcSCiuXpQVEo2XE2Z4'
);

export default function Home() {
  const [user, setUser] = useState<User | null>(null)
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [generatedCode, setGeneratedCode] = useState<string | null>(null)
  const [pmReply, setPmReply] = useState<string | null>(null)
  const [view, setView] = useState<"chat" | "code">("chat")
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const init = async () => {
      const { data } = await supabase.auth.getUser()
      if (data.user) {
        const { id, email, user_metadata } = data.user
        setUser({
          id,
          email: email!,
          full_name: user_metadata.full_name,
          avatar_url: user_metadata.avatar_url,
        })
      }

      const { data: initialMessages } = await supabase
        .from("messages")
        .select("*")
        .order("created_at", { ascending: true })

      setMessages(initialMessages || [])
    }

    init()
  }, [])

  const handleSignIn = async () => {
    await supabase.auth.signInWithOAuth({ provider: "google" })
  }

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    setUser(null)
  }

  const handleSendMessage = async () => {
    const trimmed = message.trim()
    if (!trimmed || isLoading) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      text: trimmed,
      sender: "user",
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMsg])
    setMessage("")
    setIsLoading(true)

    try {
      const res = await fetch("http://localhost:5001/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      })

      const data = await res.json()

      if (data.reply && data.missing_sections) {
        const botMsg: Message = {
          id: crypto.randomUUID(),
          text: data.reply,
          sender: "bot",
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, botMsg])
        await supabase.from("messages").insert([
          { text: trimmed, sender: "user" },
          { text: data.reply, sender: "bot" },
        ])
      } else {
        setPmReply(data.pm_reply)
        setGeneratedCode(data.generated_code)
        setView("code")
      }
    } catch (err) {
      console.error("Send failed:", err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownloadZip = async () => {
    if (!generatedCode) return
    try {
      const res = await fetch("http://localhost:5001/download-zip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: generatedCode }),
      })

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = "project.zip"
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error("Download failed:", err)
    }
  }

  if (!user) {
    return (
      <div className={styles.authContainer}>
        <Card variant="elevated" className={styles.authCard}>
          <div className={styles.authContent}>
            <img src="/favicon.ico" alt="Logo" className={styles.authLogo} />
            <h1 className={styles.authTitle}>TwinStack</h1>
            <p className={styles.authDescription}>
              Start building your AI-powered app ideas
            </p>
            <Button onClick={handleSignIn}>Continue with Google</Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className={styles.appContainer}>
      {isLoading && (
        <div className={styles.loadingOverlay}>
          <div className={styles.loadingSpinner}></div>
          <p className={styles.loadingText}>Generating code...</p>
        </div>
      )}
      <div className={styles.chatSection}>
        <ChatPanel
          messages={messages}
          currentMessage={message}
          onMessageChange={setMessage}
          onSendMessage={handleSendMessage}
          onActionClick={() => {}}
          userName={user.full_name}
          onSignOut={handleSignOut}
        />
      </div>
      <div className={styles.previewSection}>
        <PreviewPanel
          generatedCode={generatedCode}
          currentView={view}
          onViewChange={setView}
          onGenerateCode={() => {}}
          pmFeedback={pmReply}
          onDownloadClick={handleDownloadZip}
        />
      </div>
    </div>
  )
}
