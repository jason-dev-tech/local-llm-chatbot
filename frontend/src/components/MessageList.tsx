import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState } from "react";
import type { MessageItem } from "../types";

type MessageListProps = {
  messages: MessageItem[];
  isLoadingMessages: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
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

          return (
            <div
              key={`${message.role}-${index}`}
              className={`message ${message.role}`}
            >
              <div className="message-role">
                {message.role === "user" ? "You" : "AI"}
              </div>

              <div className="message-content markdown-body">
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
                    <div className="sources-title">Sources</div>
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
