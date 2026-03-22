import { FormEvent, useEffect, useRef, useState } from "react";
import "./App.css";

type Session = {
  session_id: string;
  title: string | null;
};

type Message = {
  id?: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string;
};

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
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
      const response = await fetch(`${API_BASE_URL}/sessions`);
      if (!response.ok) {
        throw new Error("Failed to load sessions");
      }

      const data = await response.json();
      const sessionList: Session[] = data.sessions ?? [];
      setSessions(sessionList);

      if (sessionList.length > 0 && !currentSessionId) {
        const firstSessionId = sessionList[0].session_id;
        setCurrentSessionId(firstSessionId);
        await loadSessionMessages(firstSessionId);
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function loadSessionMessages(sessionId: string) {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
      if (!response.ok) {
        throw new Error("Failed to load session messages");
      }

      const data = await response.json();
      setMessages(data.messages ?? []);
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error(error);
    }
  }

  async function createSession() {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to create session");
      }

      const data = await response.json();
      const newSession: Session = {
        session_id: data.session_id,
        title: data.title,
      };

      setSessions((prev) => [...prev, newSession]);
      setCurrentSessionId(newSession.session_id);
      setMessages([]);
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

    const userMessage: Message = {
      role: "user",
      content: trimmedInput,
    };

    const assistantPlaceholderIndex = messages.length + 1;

    setMessages((prev) => [
      ...prev,
      userMessage,
      { role: "assistant", content: "" },
    ]);

    setInput("");
    setIsSending(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          message: trimmedInput,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Failed to stream response");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;

        setMessages((prev) => {
          const updated = [...prev];
          if (updated[assistantPlaceholderIndex]) {
            updated[assistantPlaceholderIndex] = {
              ...updated[assistantPlaceholderIndex],
              role: "assistant",
              content: fullText,
            };
          }
          return updated;
        });
      }

      await refreshSessionsPreserveSelection(currentSessionId);
    } catch (error) {
      console.error(error);

      setMessages((prev) => {
        const updated = [...prev];
        if (updated[assistantPlaceholderIndex]) {
          updated[assistantPlaceholderIndex] = {
            ...updated[assistantPlaceholderIndex],
            role: "assistant",
            content: "Error: failed to get response.",
          };
        }
        return updated;
      });
    } finally {
      setIsSending(false);
    }
  }

  async function refreshSessionsPreserveSelection(sessionId: string) {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`);
      if (!response.ok) {
        return;
      }

      const data = await response.json();
      const sessionList: Session[] = data.sessions ?? [];
      setSessions(sessionList);

      const exists = sessionList.some(
        (session) => session.session_id === sessionId
      );

      if (exists) {
        setCurrentSessionId(sessionId);
      }
    } catch (error) {
      console.error(error);
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
          <button onClick={createSession}>+ New Chat</button>
        </div>

        <div className="session-list">
          {sessions.map((session) => (
            <button
              key={session.session_id}
              className={`session-item ${
                session.session_id === currentSessionId ? "active" : ""
              }`}
              onClick={() => loadSessionMessages(session.session_id)}
            >
              <span className="session-title">
                {session.title || session.session_id}
              </span>
              <span className="session-id">{session.session_id}</span>
            </button>
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
            {isSending ? "Sending..." : "Send"}
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;