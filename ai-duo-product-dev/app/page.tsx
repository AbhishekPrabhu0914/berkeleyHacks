"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, User, Bot, CheckCircle, Zap } from "lucide-react"

interface AgentMessage {
  id: string
  agent: "swe" | "pm"
  content: string
  timestamp: Date
  approved?: boolean
}

interface ConversationSession {
  id: string
  requirement: string
  messages: AgentMessage[]
  status: "pending" | "in-progress" | "completed"
  finalResult?: string
}

export default function AIProductDevelopmentDuo() {
  const [requirement, setRequirement] = useState("")
  const [currentSession, setCurrentSession] = useState<ConversationSession | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleSubmitRequirement = async () => {
    if (!requirement.trim()) return

    setIsProcessing(true)

    const newSession: ConversationSession = {
      id: Date.now().toString(),
      requirement: requirement.trim(),
      messages: [],
      status: "in-progress",
    }

    setCurrentSession(newSession)

    try {
      const response = await fetch("/api/agents/process", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          requirement: requirement.trim(),
          sessionId: newSession.id,
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to process requirement")
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error("No response stream")

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split("\n").filter((line) => line.trim())

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.type === "message") {
                setCurrentSession((prev) =>
                  prev
                    ? {
                        ...prev,
                        messages: [...prev.messages, data.message],
                      }
                    : null,
                )
              } else if (data.type === "complete") {
                setCurrentSession((prev) =>
                  prev
                    ? {
                        ...prev,
                        status: "completed",
                        finalResult: data.result,
                      }
                    : null,
                )
              }
            } catch (e) {
              console.error("Error parsing SSE data:", e)
            }
          }
        }
      }
    } catch (error) {
      console.error("Error processing requirement:", error)
    } finally {
      setIsProcessing(false)
    }
  }

  const resetSession = () => {
    setCurrentSession(null)
    setRequirement("")
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">AI Product Development Duo</h1>
          <p className="text-lg text-gray-600 mb-4">
            Watch two AI agents collaborate to refine your product requirements
          </p>
          <div className="flex justify-center gap-4 mb-6">
            <Badge variant="outline" className="bg-blue-100 text-blue-800 border-blue-300">
              <Bot className="w-4 h-4 mr-1" />
              SWE Agent
            </Badge>
            <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300">
              <CheckCircle className="w-4 h-4 mr-1" />
              PM Agent
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Section */}
          <Card className="h-fit">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Product Requirement Input
              </CardTitle>
              <CardDescription>
                Describe your product feature or user story. The AI agents will collaborate to refine it.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Example: Create a user authentication system with social login options that ensures security while maintaining a smooth user experience..."
                value={requirement}
                onChange={(e) => setRequirement(e.target.value)}
                className="min-h-[120px]"
                disabled={isProcessing}
              />
              <div className="flex gap-2">
                <Button
                  onClick={handleSubmitRequirement}
                  disabled={!requirement.trim() || isProcessing}
                  className="flex-1"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      Start AI Collaboration
                    </>
                  )}
                </Button>
                {currentSession && (
                  <Button variant="outline" onClick={resetSession}>
                    Reset
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Results Section */}
          <Card className="h-fit">
            <CardHeader>
              <CardTitle>Agent Collaboration</CardTitle>
              <CardDescription>Real-time dialogue between SWE and PM agents</CardDescription>
            </CardHeader>
            <CardContent>
              {!currentSession ? (
                <div className="text-center py-8 text-gray-500">
                  <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Submit a requirement to start the AI collaboration</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Requirement Display */}
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <h4 className="font-medium text-sm text-gray-700 mb-1">Original Requirement:</h4>
                    <p className="text-sm text-gray-900">{currentSession.requirement}</p>
                  </div>

                  {/* Messages */}
                  <ScrollArea className="h-[400px] w-full">
                    <div className="space-y-3">
                      {currentSession.messages.map((message, index) => (
                        <div key={message.id} className="space-y-2">
                          <div
                            className={`flex items-start gap-3 ${
                              message.agent === "swe" ? "justify-start" : "justify-end"
                            }`}
                          >
                            <div
                              className={`max-w-[80%] p-3 rounded-lg ${
                                message.agent === "swe" ? "bg-blue-100 text-blue-900" : "bg-green-100 text-green-900"
                              }`}
                            >
                              <div className="flex items-center gap-2 mb-1">
                                {message.agent === "swe" ? (
                                  <Bot className="w-4 h-4" />
                                ) : (
                                  <CheckCircle className="w-4 h-4" />
                                )}
                                <span className="font-medium text-xs">
                                  {message.agent === "swe" ? "SWE Agent" : "PM Agent"}
                                </span>
                                {message.approved && (
                                  <Badge
                                    variant="outline"
                                    className="text-xs bg-green-50 text-green-700 border-green-300"
                                  >
                                    Approved
                                  </Badge>
                                )}
                              </div>
                              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            </div>
                          </div>
                          {index < currentSession.messages.length - 1 && <Separator className="my-2" />}
                        </div>
                      ))}

                      {isProcessing && currentSession.messages.length > 0 && (
                        <div className="flex justify-center py-4">
                          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                        </div>
                      )}
                    </div>
                  </ScrollArea>

                  {/* Final Result */}
                  {currentSession.status === "completed" && currentSession.finalResult && (
                    <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <h4 className="font-medium text-green-800">Final Approved Solution</h4>
                      </div>
                      <p className="text-sm text-green-700 whitespace-pre-wrap">{currentSession.finalResult}</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* How it Works Section */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>How the AI Duo Works</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Bot className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="font-medium mb-2">SWE Agent</h3>
                <p className="text-sm text-gray-600">
                  Generates technical proposals, implementation strategies, and code solutions based on requirements.
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="font-medium mb-2">PM Agent</h3>
                <p className="text-sm text-gray-600">
                  Reviews proposals for usability, scope alignment, and product goals. Provides iterative feedback.
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Zap className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-medium mb-2">Iterative Loop</h3>
                <p className="text-sm text-gray-600">
                  Agents collaborate until the PM approves the solution, ensuring quality and alignment.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
