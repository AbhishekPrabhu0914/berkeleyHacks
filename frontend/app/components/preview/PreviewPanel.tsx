"use client"

import type React from "react"
import { Card } from "../ui/Card"
import { Button } from "../ui/Button"
import styles from "./PreviewPanel.module.css"
import { Dispatch, SetStateAction } from "react"

export interface PreviewPanelProps {
  generatedCode: string | null;
  currentView: "chat" | "code";
  onViewChange: Dispatch<SetStateAction<"chat" | "code">>;
  onGenerateCode: () => void;
  pmFeedback: string | null; // Added pmFeedback property
  onDownloadClick: () => Promise<void>;
}

/**
 * Preview panel component for displaying generated code
 * Includes view switching and code display with syntax highlighting
 */
export const PreviewPanel: React.FC<PreviewPanelProps> = ({
  generatedCode,
  currentView,
  onViewChange,
  onGenerateCode,
}) => {
  return (
    <div className={styles.previewPanel}>
      {/* Header with view toggle */}
    

      {/* Content area */}
      <div className={styles.content}>
        {currentView === "code" && generatedCode ? (
          <Card variant="bordered" className={styles.codeCard}>
            <div className={styles.codeHeader}>
              <div className={styles.windowControls}>
                         <div className={styles.control} style={{ background: "#ef4444" }} />
                <div className={styles.control} style={{ background: "#f59e0b" }} />
                <div className={styles.control} style={{ background: "#10b981" }} />
              </div>
              <span className={styles.codeTitle}>Generated Code</span>
            </div>
            <div className={styles.codeContent}>
              <pre className={styles.codeBlock}>
                <code>{generatedCode}</code>
              </pre>
            </div>
          </Card>
        ) : (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>📄</div>
            <h3 className={styles.emptyTitle}>Ready for Preview</h3>
            <p className={styles.emptyDescription}>
              {generatedCode ? "Switch to Code view to see generated content" : "Generate code to see preview"}
            </p>
            <div className={styles.emptyActions}>
              <Button variant="accent" onClick={onGenerateCode}>
                Generate Code
              </Button>
              {generatedCode && (
                <Button variant="ghost" onClick={() => onViewChange("code")}>
                  View Code
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
