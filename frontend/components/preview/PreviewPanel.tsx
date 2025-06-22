import React from "react"
import styles from "./PreviewPanel.module.css"
import { Button } from "../ui/Button"

interface PreviewPanelProps {
  generatedCode: string | null
  pmFeedback: string | null
  onDownloadClick: () => void
}

export const PreviewPanel: React.FC<PreviewPanelProps> = ({
  generatedCode,
  pmFeedback,
  onDownloadClick,
}) => {
  return (
    <div className={styles.previewContainer}>
      {pmFeedback && (
        <div className={styles.section}>
          <h3>🧠 PM Technical Spec</h3>
          <pre className={styles.specBlock}>{pmFeedback}</pre>
        </div>
      )}

      {generatedCode && (
        <div className={styles.section}>
          <div className={styles.generatedHeader}>
            <h3>💻 Generated Code</h3>
            <Button variant="accent" onClick={onDownloadClick}>
              ⬇️ Download ZIP
            </Button>
          </div>
          <pre className={styles.codeBlock}>{generatedCode}</pre>
        </div>
      )}
    </div>
  )
}
