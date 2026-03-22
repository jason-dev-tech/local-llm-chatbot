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
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>Local AI Chatbot</h1>
        <button onClick={onCreateSession} disabled={isLoadingSessions}>
          {isLoadingSessions ? "Loading..." : "+ New Chat"}
        </button>
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