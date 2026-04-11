import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";
import type { RefObject } from "react";
import type { AssistantTransparencyStatus, MessageItem } from "../types";
import "./MessageList.css";

type MessageListProps = {
  messages: MessageItem[];
  isLoadingMessages: boolean;
  messagesEndRef: RefObject<HTMLDivElement | null>;
};

function CodeBlock({ children }: { children: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error("Copy failed", err);
    }
  }

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={handleCopy}
        style={{
          position: "absolute",
          top: 8,
          right: 8,
          fontSize: 12,
          padding: "4px 8px",
          borderRadius: 6,
          border: "none",
          background: "#334155",
          color: "#e5e7eb",
          cursor: "pointer",
        }}
      >
        {copied ? "Copied" : "Copy"}
      </button>

      <pre>
        <code>{children}</code>
      </pre>
    </div>
  );
}

function splitMessageContent(content: string) {
  const marker = "\n\nSources:\n";
  const index = content.indexOf(marker);

  if (index === -1) {
    return {
      mainContent: content,
      sourceSections: [] as Array<{ title: string; items: string[] }>,
    };
  }

  const mainContent = content.slice(0, index);
  const sourceBlock = content.slice(index + marker.length);
  const sourceSections = [];

  let currentSection: { title: string; items: string[] } | null = null;

  for (const rawLine of sourceBlock.split("\n")) {
    const line = rawLine.trim();

    if (!line) {
      continue;
    }

    if (line.endsWith(":")) {
      if (currentSection && currentSection.items.length > 0) {
        sourceSections.push(currentSection);
      }

      currentSection = {
        title: line.slice(0, -1),
        items: [],
      };
      continue;
    }

    if (!currentSection) {
      currentSection = {
        title: "Sources",
        items: [],
      };
    }

    currentSection.items.push(line.replace(/^- /, "").trim());
  }

  if (currentSection && currentSection.items.length > 0) {
    sourceSections.push(currentSection);
  }

  return {
    mainContent,
    sourceSections,
  };
}

function getAssistantTransparencyStatus(
  content: string,
  sourceSections: Array<{ title: string; items: string[] }>,
): AssistantTransparencyStatus | null {
  const normalized = content.trim();
  if (!normalized || normalized === "Thinking...") {
    return null;
  }

  const lower = normalized.toLowerCase();
  const mainContent = normalized.split("\n\nSources:\n", 1)[0] || normalized;
  const hasInlineCitations = /\[\d+\]/.test(mainContent);
  const hasSourcesUsedSection = sourceSections.some(
    (section) => section.title.toLowerCase() === "sources used",
  );
  const hasRetrievedContextSection = sourceSections.some(
    (section) => section.title.toLowerCase() === "retrieved context",
  );
  const clearlyLimitedEvidence =
    lower === "i couldn't find enough relevant evidence in the knowledge base to answer that confidently."
    || lower.includes("do not have enough information from the provided context");

  if (
    clearlyLimitedEvidence
  ) {
    return "Limited supporting information";
  }

  if (hasSourcesUsedSection && hasInlineCitations) {
    return "Answer based on sources";
  }

  if (lower.startsWith("error:")) {
    return null;
  }

  if (hasSourcesUsedSection || hasRetrievedContextSection || sourceSections.length > 0) {
    return "Using retrieved information";
  }

  return null;
}

function MessageList({
  messages,
  isLoadingMessages,
  messagesEndRef,
}: MessageListProps) {
  return (
    <div className="message-list">
      {isLoadingMessages ? (
        <div className="empty-state">Loading messages...</div>
      ) : messages.length === 0 ? (
        <div className="empty-state">
          Start a new conversation with your local AI chatbot.
        </div>
      ) : (
        messages.map((message, index) => {
          const isAssistant = message.role === "assistant";
          const { mainContent, sourceSections } = isAssistant
            ? splitMessageContent(message.content)
            : {
                mainContent: message.content,
                sourceSections: [] as Array<{ title: string; items: string[] }>,
              };
          const transparencyStatus = isAssistant
            ? getAssistantTransparencyStatus(message.content, sourceSections)
            : null;

          return (
            <div
              key={`${message.role}-${index}`}
              className={`message ${message.role}`}
            >
              <div className="message-role">
                {message.role === "user" ? "You" : "AI"}
              </div>

              <div className="message-content markdown-body">
                {transparencyStatus && (
                  <div className="message-status-badge">
                    {transparencyStatus}
                  </div>
                )}

                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ inline, children }: any) {
                      if (inline) {
                        return <code>{children}</code>;
                      }

                      return <CodeBlock>{String(children)}</CodeBlock>;
                    },
                  }}
                >
                  {mainContent}
                </ReactMarkdown>

                {isAssistant && sourceSections.length > 0 && (
                  <div className="sources-block">
                    {sourceSections.map((section) => (
                      <div key={section.title}>
                        <div className="sources-title">{section.title}</div>
                        <ul className="sources-list">
                          {section.items.map((source) => (
                            <li key={`${section.title}-${source}`}>{source}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default MessageList;
