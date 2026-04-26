import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
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
  uploadSessionDocument,
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
  const [systemNotReadyReason, setSystemNotReadyReason] = useState<string | null>(null);
  const [selectedSessionFile, setSelectedSessionFile] = useState<File | null>(null);
  const [sessionUploadStatus, setSessionUploadStatus] = useState("");
  const [sessionUploadStatusType, setSessionUploadStatusType] = useState<"uploading" | "success" | "error" | "">("");
  const [isUploadingSessionFile, setIsUploadingSessionFile] = useState(false);
  const [isSessionAttachmentOpen, setIsSessionAttachmentOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const sessionFileInputRef = useRef<HTMLInputElement | null>(null);
  const sessionAttachmentRef = useRef<HTMLDivElement | null>(null);

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

  useEffect(() => {
    if (!isSessionAttachmentOpen) {
      return;
    }

    function handleDocumentMouseDown(event: MouseEvent) {
      const target = event.target;

      if (
        target instanceof Node
        && sessionAttachmentRef.current
        && !sessionAttachmentRef.current.contains(target)
      ) {
        setIsSessionAttachmentOpen(false);
      }
    }

    document.addEventListener("mousedown", handleDocumentMouseDown);

    return () => {
      document.removeEventListener("mousedown", handleDocumentMouseDown);
    };
  }, [isSessionAttachmentOpen]);

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

  async function checkSystemReadiness(): Promise<boolean> {
    try {
      const readiness = await fetchReadiness();
      setIsSystemReady(readiness.isReady);
      setSystemNotReadyReason(readiness.notReadyReason);
      return readiness.isReady;
    } catch (error) {
      console.error(error);
      setIsSystemReady(false);
      setSystemNotReadyReason("Backend service is unavailable.");
      return false;
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

  function findLastAssistantMessageIndex(messageItems: MessageItem[]) {
    for (let index = messageItems.length - 1; index >= 0; index -= 1) {
      if (messageItems[index]?.role === "assistant") {
        return index;
      }
    }

    return -1;
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

    const isReady = await checkSystemReadiness();
    if (!isReady) {
      return;
    }
    setErrorMessage("");

    const activeSessionId = currentSessionId;
    const appendUserMessage = options?.appendUserMessage ?? true;
    const clearInput = options?.clearInput ?? true;
    const refreshMessagesOnDone = options?.refreshMessagesOnDone ?? true;
    const isRetry = appendUserMessage === false;

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
      const responseStartedAt = performance.now();

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
        async (streamMetadata) => {
          const responseTimeSeconds = (performance.now() - responseStartedAt) / 1000;
          const retrievalScope = streamMetadata.retrieval_scope;
          const responseExplanation = streamMetadata.response_explanation;

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

          if (refreshMessagesOnDone && isRetry) {
            const [updatedSessions, updatedMessages] = await Promise.all([
              fetchSessions(),
              fetchMessages(activeSessionId),
            ]);
            const messagesWithResponseTime = [...updatedMessages];
            const responseTimeIndex = isRetry
              ? findLastAssistantMessageIndex(messagesWithResponseTime)
              : targetAssistantIndex;

            if (messagesWithResponseTime[responseTimeIndex]?.role === "assistant") {
              messagesWithResponseTime[responseTimeIndex] = {
                ...messagesWithResponseTime[responseTimeIndex],
                responseTimeSeconds,
                retrievalScope,
                responseExplanation,
              };
            }

            setSessions(updatedSessions);

            if (currentSessionId === activeSessionId) {
              setMessages(messagesWithResponseTime);
            }
          } else {
            const updatedSessions = await fetchSessions();
            setSessions(updatedSessions);

            setMessages((prev) => {
              const updated = [...prev];

              if (updated[targetAssistantIndex]?.role === "assistant") {
                updated[targetAssistantIndex] = {
                  ...updated[targetAssistantIndex],
                  responseTimeSeconds,
                  retrievalScope,
                  responseExplanation,
                };
              }

              return updated;
            });
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

  function handleSessionFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedSessionFile(event.target.files?.[0] ?? null);
    setSessionUploadStatus("");
    setSessionUploadStatusType("");
  }

  async function handleSessionUploadClick() {
    if (!currentSessionId || !selectedSessionFile || isUploadingSessionFile) {
      return;
    }

    setIsUploadingSessionFile(true);
    setSessionUploadStatus("Uploading...");
    setSessionUploadStatusType("uploading");

    try {
      const attachedFilename = selectedSessionFile.name;
      await uploadSessionDocument(currentSessionId, selectedSessionFile);
      setMessages((prev) => [
        ...prev,
        {
          role: "attachment",
          content: attachedFilename,
          created_at: new Date().toISOString(),
        },
      ]);
      setSelectedSessionFile(null);
      setSessionUploadStatus("Attached to this session.");
      setSessionUploadStatusType("success");
      if (sessionFileInputRef.current) {
        sessionFileInputRef.current.value = "";
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setSessionUploadStatus(message);
      setSessionUploadStatusType("error");
    } finally {
      setIsUploadingSessionFile(false);
    }
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
                  {systemNotReadyReason || "Some AI features are unavailable."}
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
          attachmentControls={
            <div className="session-attachment-control" ref={sessionAttachmentRef}>
              <button
                type="button"
                className="session-attachment-toggle"
                onClick={() => setIsSessionAttachmentOpen((isOpen) => !isOpen)}
                disabled={!currentSessionId}
              >
                +
              </button>
              {isSessionAttachmentOpen ? (
                <div className="session-attachment-menu">
                  <div className="session-attachment-copy">
                    <div className="session-attachment-title">Session document</div>
                    <div className="session-attachment-help">
                      Available only in this chat session. TXT, MD, JSON, PDF.
                    </div>
                  </div>
                  <div className="session-attachment-picker">
                    <input
                      ref={sessionFileInputRef}
                      type="file"
                      accept=".txt,.md,.json,.pdf"
                      onChange={handleSessionFileChange}
                      disabled={!currentSessionId || isUploadingSessionFile}
                    />
                    <div className="session-attachment-filename">
                      {selectedSessionFile ? selectedSessionFile.name : "No file selected"}
                    </div>
                  </div>
                  <div className="session-attachment-footer">
                    <button
                      type="button"
                      onClick={handleSessionUploadClick}
                      disabled={!currentSessionId || isUploadingSessionFile || !selectedSessionFile}
                    >
                      Attach
                    </button>
                    {sessionUploadStatus ? (
                      <div className={`session-attachment-status ${sessionUploadStatusType}`}>
                        {sessionUploadStatus}
                      </div>
                    ) : null}
                  </div>
                </div>
              ) : null}
            </div>
          }
          onInputChange={setInput}
          onSubmit={handleSendMessage}
        />
      </main>
    </div>
  );
}

export default App;
