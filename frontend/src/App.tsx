import { FormEvent, useEffect, useRef, useState } from "react";
import "./App.css";

import type { SessionItem, MessageItem } from "./types";
import {
  fetchSessions,
  createSession,
  fetchMessages,
  streamChat,
  renameSession,
  deleteSession,
} from "./api/chat";

function App() {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function loadSessions() {
    try {
      const sessionList = await fetchSessions();
      setSessions(sessionList);

      if (sessionList.length > 0 && !currentSessionId) {
        const firstSessionId = sessionList[0].session_id;
        setCurrentSessionId(firstSessionId);

        const msgs = await fetchMessages(firstSessionId);
        setMessages(msgs);
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function loadSessionMessages(sessionId: string) {
    try {
      const msgs = await fetchMessages(sessionId);
      setMessages(msgs);
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error(error);
    }
  }

  async function handleCreateSession() {
    try {
      const newSession = await createSession();
      const updated = await fetchSessions();

      setSessions(updated);
      setCurrentSessionId(newSession.session_id);
      setMessages([]);
    } catch (error) {
      console.error(error);
    }
  }

  async function handleRenameSession(
    event: React.MouseEvent,
    sessionId: string,
    currentTitle: string | null
  ) {
    event.stopPropagation();

    const nextTitle = window.prompt(
      "Enter a new session title:",
      currentTitle || sessionId
    );

    if (!nextTitle) {
      return;
    }

    const trimmedTitle = nextTitle.trim();
    if (!trimmedTitle) {
      return;
    }

    try {
      await renameSession(sessionId, trimmedTitle);
      const updated = await fetchSessions();
      setSessions(updated);
    } catch (error) {
      console.error(error);
    }
  }

  async function handleDeleteSession(
    event: React.MouseEvent,
    sessionId: string
  ) {
    event.stopPropagation();

    const confirmed = window.confirm("Delete this session?");
    if (!confirmed) {
      return;
    }

    try {
      await deleteSession(sessionId);

      const updated = await fetchSessions();
      setSessions(updated);

      if (currentSessionId === sessionId) {
        if (updated.length > 0) {
          const firstSessionId = updated[0].session_id;
          setCurrentSessionId(firstSessionId);

          const msgs = await fetchMessages(firstSessionId);
          setMessages(msgs);
        } else {
          setCurrentSessionId("");
          setMessages([]);
        }
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function handleSendMessage(event: FormEvent) {
    event.preventDefault();

    const trimmedInput = input.trim();
    if (!trimmedInput || !currentSessionId || isSending) {
      return;
    }

    const userMessage: MessageItem = {
      role: "user",
      content: trimmedInput,
    };

    const assistantPlaceholder: MessageItem = {
      role: "assistant",
      content: "",
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);

    setInput("");
    setIsSending(true);

    try {
      await streamChat(
        currentSessionId,
        trimmedInput,
        (token) => {
          setMessages((prev) => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;

            if (updated[lastIndex].role === "assistant") {
              updated[lastIndex] = {
                ...updated[lastIndex],
                content: updated[lastIndex].content + token,
              };
            }

            return updated;
          });
        },
        async () => {
          const updatedSessions = await fetchSessions();
          setSessions(updatedSessions);
        },
        (errorMessage) => {
          console.error(errorMessage);
        }
      );
    } catch (error) {
      console.error(error);
    } finally {
      setIsSending(false);
    }
  }

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>Local AI Chatbot</h1>
          <button onClick={handleCreateSession}>+ New Chat</button>
        </div>

        <div className="session-list">
          {sessions.map((session) => (
            <div
              key={session.session_id}
              className={`session-item ${
                session.session_id === currentSessionId ? "active" : ""
              }`}
              onClick={() => loadSessionMessages(session.session_id)}
            >
              <div className="session-main">
                <span className="session-title">
                  {session.title || session.session_id}
                </span>
              </div>

              <div className="session-actions">
                <button
                  type="button"
                  onClick={(event) =>
                    handleRenameSession(
                      event,
                      session.session_id,
                      session.title
                    )
                  }
                >
                  Rename
                </button>
                <button
                  type="button"
                  onClick={(event) =>
                    handleDeleteSession(event, session.session_id)
                  }
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </aside>

      <main className="chat-panel">
        <div className="chat-header">
          <h2>{currentSessionId || "No session selected"}</h2>
        </div>

        <div className="message-list">
          {messages.length === 0 ? (
            <div className="empty-state">
              Start a new conversation with your local AI chatbot.
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`message ${message.role}`}
              >
                <div className="message-role">
                  {message.role === "user" ? "You" : "AI"}
                </div>
                <div className="message-content">{message.content}</div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-area" onSubmit={handleSendMessage}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Type your message..."
            rows={3}
            disabled={!currentSessionId || isSending}
          />
          <button type="submit" disabled={!currentSessionId || isSending}>
            {isSending ? "Streaming..." : "Send"}
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;