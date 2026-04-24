import { useRef, useState } from "react";
import type { ChangeEvent } from "react";

import { uploadKnowledgeDocument } from "../api/chat";
import type { SessionItem } from "../types";

type SessionSidebarProps = {
  sessions: SessionItem[];
  currentSessionId: string;
  isLoadingSessions: boolean;
  onCreateSession: () => void;
  onSelectSession: (sessionId: string) => void;
  onRenameSession: (sessionId: string, currentTitle: string | null) => void;
  onDeleteSession: (sessionId: string) => void;
};

function SessionSidebar({
  sessions,
  currentSessionId,
  isLoadingSessions,
  onCreateSession,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
}: SessionSidebarProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
    setUploadStatus("");
  }

  async function handleUploadClick() {
    if (!selectedFile || isUploading) {
      return;
    }

    setIsUploading(true);
    setUploadStatus("Uploading...");

    try {
      await uploadKnowledgeDocument(selectedFile);
      setSelectedFile(null);
      setUploadStatus("Upload complete.");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setUploadStatus(message);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>Local AI Chatbot</h1>
        <button onClick={onCreateSession} disabled={isLoadingSessions}>
          {isLoadingSessions ? "Loading..." : "+ New Chat"}
        </button>
      </div>

      <div className="knowledge-upload-section">
        <label htmlFor="knowledge-file-upload">Upload knowledge document</label>
        <input
          id="knowledge-file-upload"
          ref={fileInputRef}
          type="file"
          accept=".txt,.md,.json,.pdf"
          onChange={handleFileChange}
          disabled={isUploading}
        />
        {selectedFile ? (
          <span className="knowledge-upload-filename">{selectedFile.name}</span>
        ) : null}
        <button
          type="button"
          onClick={handleUploadClick}
          disabled={isUploading || !selectedFile}
        >
          Add to knowledge base
        </button>
        {uploadStatus ? (
          <span className="knowledge-upload-status">{uploadStatus}</span>
        ) : null}
      </div>

      <div className="session-list">
        {isLoadingSessions && sessions.length === 0 ? (
          <div className="empty-state">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="empty-state">No sessions yet.</div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              className={`session-item ${
                session.session_id === currentSessionId ? "active" : ""
              }`}
              onClick={() => onSelectSession(session.session_id)}
            >
              <div className="session-main">
                <span className="session-title">
                  {session.title || session.session_id}
                </span>
              </div>

              <div className="session-actions">
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onRenameSession(session.session_id, session.title);
                  }}
                >
                  Rename
                </button>

                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onDeleteSession(session.session_id);
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}

export default SessionSidebar;
