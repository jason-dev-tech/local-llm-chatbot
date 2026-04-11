import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import "./App.css";

import type { SessionItem, MessageItem } from "./types";
import {
  fetchSessions,
  createSession,
  fetchMessages,
  fetchReadiness,
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
  const [retryingAssistantIndex, setRetryingAssistantIndex] = useState<number | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isSystemReady, setIsSystemReady] = useState<boolean | null>(null);

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
    checkSystemReadiness();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  function classifyErrorMessage(rawMessage: string | null | undefined): string {
    const normalized = (rawMessage || "").toLowerCase();

    if (
      normalized.includes("relevant evidence")
      || normalized.includes("knowledge base")
      || normalized.includes("provided context")
    ) {
      return "No relevant information found in the knowledge base.";
    }

    if (
      normalized.includes("failed to fetch")
      || normalized.includes("network")
    ) {
      return "Network issue. Please try again.";
    }

    return "Model is currently unavailable.";
  }

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

  async function checkSystemReadiness() {
    try {
      const ready = await fetchReadiness();
      setIsSystemReady(ready);
    } catch (error) {
      console.error(error);
      setIsSystemReady(false);
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

  async function sendMessageWithStreaming(
    messageText: string,
    options?: {
      assistantIndex?: number;
      appendUserMessage?: boolean;
      clearInput?: boolean;
      refreshMessagesOnDone?: boolean;
    },
  ) {
    const trimmedInput = messageText.trim();
    if (!trimmedInput || !currentSessionId || isSending) {
      return;
    }

    setErrorMessage("");

    const activeSessionId = currentSessionId;
    const appendUserMessage = options?.appendUserMessage ?? true;
    const clearInput = options?.clearInput ?? true;
    const refreshMessagesOnDone = options?.refreshMessagesOnDone ?? true;

    const userMessage: MessageItem = {
      role: "user",
      content: trimmedInput,
    };

    const assistantPlaceholder: MessageItem = {
      role: "assistant",
      content: "Thinking...",
    };

    let targetAssistantIndex = options?.assistantIndex ?? -1;

    setMessages((prev) => {
      if (appendUserMessage) {
        targetAssistantIndex = prev.length + 1;
        return [...prev, userMessage, assistantPlaceholder];
      }

      if (
        targetAssistantIndex >= 0
        && targetAssistantIndex < prev.length
        && prev[targetAssistantIndex]?.role === "assistant"
      ) {
        const updated = [...prev];
        updated[targetAssistantIndex] = {
          ...updated[targetAssistantIndex],
          content: "Thinking...",
        };
        return updated;
      }

      return prev;
    });

    if (clearInput) {
      setInput("");
    }
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

            if (updated[targetAssistantIndex]?.role === "assistant") {
              const currentContent = updated[targetAssistantIndex].content;
              const nextContent =
                currentContent === "Thinking..."
                  ? token
                  : currentContent + token;

              updated[targetAssistantIndex] = {
                ...updated[targetAssistantIndex],
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

              if (updated[targetAssistantIndex]?.role === "assistant") {
                updated[targetAssistantIndex] = {
                  ...updated[targetAssistantIndex],
                  content: "No response received.",
                };
              }

              return updated;
            });
          }

          if (refreshMessagesOnDone) {
            const [updatedSessions, updatedMessages] = await Promise.all([
              fetchSessions(),
              fetchMessages(activeSessionId),
            ]);

            setSessions(updatedSessions);

            if (currentSessionId === activeSessionId) {
              setMessages(updatedMessages);
            }
          } else {
            const updatedSessions = await fetchSessions();
            setSessions(updatedSessions);
          }
        },
        (streamErrorMessage) => {
          console.error(streamErrorMessage);
          setErrorMessage(classifyErrorMessage(streamErrorMessage || "Streaming failed."));

          setMessages((prev) => {
            const updated = [...prev];

            if (updated[targetAssistantIndex]?.role === "assistant") {
              updated[targetAssistantIndex] = {
                ...updated[targetAssistantIndex],
                content: "Error: failed to get response.",
              };
            }

            return updated;
          });
        },
      );
    } catch (error) {
      console.error(error);
      const rawMessage = error instanceof Error ? error.message : "Failed to send the message.";
      setErrorMessage(
        rawMessage.toLowerCase().includes("relevant evidence")
          || rawMessage.toLowerCase().includes("knowledge base")
          || rawMessage.toLowerCase().includes("provided context")
          ? classifyErrorMessage(rawMessage)
          : "Network issue. Please try again.",
      );

      setMessages((prev) => {
        const updated = [...prev];

        if (updated[targetAssistantIndex]?.role === "assistant") {
          updated[targetAssistantIndex] = {
            ...updated[targetAssistantIndex],
            content: "Error: failed to get response.",
          };
        }

        return updated;
      });
    } finally {
      setIsSending(false);
    }
  }

  async function handleSendMessage(event: FormEvent) {
    event.preventDefault();
    await sendMessageWithStreaming(input);
  }

  async function handleRetryMessage(assistantIndex: number) {
    if (isSending || assistantIndex <= 0 || assistantIndex >= messages.length) {
      return;
    }

    let previousUserMessage: MessageItem | null = null;
    for (let index = assistantIndex - 1; index >= 0; index -= 1) {
      if (messages[index]?.role === "user") {
        previousUserMessage = messages[index];
        break;
      }
    }

    if (!previousUserMessage?.content) {
      return;
    }

    setRetryingAssistantIndex(assistantIndex);

    try {
      await sendMessageWithStreaming(previousUserMessage.content, {
        assistantIndex,
        appendUserMessage: false,
        clearInput: false,
        refreshMessagesOnDone: true,
      });
    } finally {
      setRetryingAssistantIndex(null);
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
          {isSystemReady !== null && (
            <div className="system-status-row">
              <div
                className={`system-status-indicator ${
                  isSystemReady ? "ready" : "not-ready"
                }`}
              >
                {isSystemReady ? "System ready" : "System not ready"}
              </div>
              {!isSystemReady && (
                <div className="system-status-detail">
                  Some AI features may be unavailable.
                </div>
              )}
            </div>
          )}
        </div>

        {errorMessage ? (
          <div className="app-error-banner">
            {errorMessage}
          </div>
        ) : null}

        <MessageList
          messages={messages}
          isLoadingMessages={isLoadingMessages}
          messagesEndRef={messagesEndRef}
          onRetryMessage={handleRetryMessage}
          retryingAssistantIndex={retryingAssistantIndex}
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
