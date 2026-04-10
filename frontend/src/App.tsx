import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
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
import SessionSidebar from "./components/SessionSidebar";
import ChatInput from "./components/ChatInput";
import MessageList from "./components/MessageList";

function App() {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const currentSession = useMemo(() => {
    return (
      sessions.find((session) => session.session_id === currentSessionId) ||
      null
    );
  }, [sessions, currentSessionId]);

  const currentSessionDisplayTitle =
    currentSession?.title || currentSessionId || "No session selected";

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  async function loadSessions() {
    setIsLoadingSessions(true);
    setErrorMessage("");

    try {
      const sessionList = await fetchSessions();
      setSessions(sessionList);

      if (sessionList.length > 0 && !currentSessionId) {
        const firstSessionId = sessionList[0].session_id;
        setCurrentSessionId(firstSessionId);
        await loadSessionMessages(firstSessionId);
      }
    } catch (error) {
      console.error(error);
      setErrorMessage("Failed to load sessions.");
    } finally {
      setIsLoadingSessions(false);
    }
  }

  async function loadSessionMessages(sessionId: string) {
    setIsLoadingMessages(true);
    setErrorMessage("");

    try {
      const msgs = await fetchMessages(sessionId);
      setMessages(msgs);
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error(error);
      setErrorMessage("Failed to load messages.");
    } finally {
      setIsLoadingMessages(false);
    }
  }

  async function handleCreateSession() {
    setErrorMessage("");

    try {
      const newSession = await createSession();
      const updated = await fetchSessions();

      setSessions(updated);
      setCurrentSessionId(newSession.session_id);
      setMessages([]);
    } catch (error) {
      console.error(error);
      setErrorMessage("Failed to create a new session.");
    }
  }

  async function handleRenameSession(
    sessionId: string,
    currentTitle: string | null,
  ) {
    const nextTitle = window.prompt(
      "Enter a new session title:",
      currentTitle || sessionId,
    );

    if (!nextTitle) {
      return;
    }

    const trimmedTitle = nextTitle.trim();
    if (!trimmedTitle) {
      return;
    }

    setErrorMessage("");

    try {
      await renameSession(sessionId, trimmedTitle);
      const updated = await fetchSessions();
      setSessions(updated);
    } catch (error) {
      console.error(error);
      setErrorMessage("Failed to rename the session.");
    }
  }

  async function handleDeleteSession(sessionId: string) {
    const confirmed = window.confirm("Delete this session?");
    if (!confirmed) {
      return;
    }

    setErrorMessage("");

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
      setErrorMessage("Failed to delete the session.");
    }
  }

  async function handleSendMessage(event: FormEvent) {
    event.preventDefault();

    const trimmedInput = input.trim();
    if (!trimmedInput || !currentSessionId || isSending) {
      return;
    }

    setErrorMessage("");

    const activeSessionId = currentSessionId;

    const userMessage: MessageItem = {
      role: "user",
      content: trimmedInput,
    };

    const assistantPlaceholder: MessageItem = {
      role: "assistant",
      content: "Thinking...",
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setInput("");
    setIsSending(true);

    try {
      let hasReceivedToken = false;

      await streamChat(
        activeSessionId,
        trimmedInput,
        (token) => {
          hasReceivedToken = true;

          setMessages((prev) => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;

            if (updated[lastIndex]?.role === "assistant") {
              const currentContent = updated[lastIndex].content;
              const nextContent =
                currentContent === "Thinking..."
                  ? token
                  : currentContent + token;

              updated[lastIndex] = {
                ...updated[lastIndex],
                content: nextContent,
              };
            }

            return updated;
          });
        },
        async () => {
          if (!hasReceivedToken) {
            setMessages((prev) => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;

              if (updated[lastIndex]?.role === "assistant") {
                updated[lastIndex] = {
                  ...updated[lastIndex],
                  content: "No response received.",
                };
              }

              return updated;
            });
          }

          const [updatedSessions, updatedMessages] = await Promise.all([
            fetchSessions(),
            fetchMessages(activeSessionId),
          ]);

          setSessions(updatedSessions);

          if (currentSessionId === activeSessionId) {
            setMessages(updatedMessages);
          }
        },
        (streamErrorMessage) => {
          console.error(streamErrorMessage);
          setErrorMessage(streamErrorMessage || "Streaming failed.");

          setMessages((prev) => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;

            if (updated[lastIndex]?.role === "assistant") {
              updated[lastIndex] = {
                ...updated[lastIndex],
                content: "Error: failed to get response.",
              };
            }

            return updated;
          });
        },
      );
    } catch (error) {
      console.error(error);
      setErrorMessage("Failed to send the message.");

      setMessages((prev) => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;

        if (updated[lastIndex]?.role === "assistant") {
          updated[lastIndex] = {
            ...updated[lastIndex],
            content: "Error: failed to get response.",
          };
        }

        return updated;
      });
    } finally {
      setIsSending(false);
    }
  }

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <div className="app">
      <SessionSidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        isLoadingSessions={isLoadingSessions}
        onCreateSession={handleCreateSession}
        onSelectSession={loadSessionMessages}
        onRenameSession={handleRenameSession}
        onDeleteSession={handleDeleteSession}
      />

      <main className="chat-panel">
        <div className="chat-header">
          <h2>{currentSessionDisplayTitle}</h2>
        </div>

        {errorMessage ? (
          <div
            style={{
              margin: "12px 20px 0",
              padding: "10px 12px",
              borderRadius: "8px",
              background: "#fee2e2",
              color: "#991b1b",
              fontSize: "14px",
            }}
          >
            {errorMessage}
          </div>
        ) : null}

        <MessageList
          messages={messages}
          isLoadingMessages={isLoadingMessages}
          messagesEndRef={messagesEndRef}
        />

        <ChatInput
          input={input}
          isSending={isSending}
          disabled={!currentSessionId}
          onInputChange={setInput}
          onSubmit={handleSendMessage}
        />
      </main>
    </div>
  );
}

export default App;
