import type { MessageItem } from "../types";

type MessageListProps = {
  messages: MessageItem[];
  isLoadingMessages: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
};

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
  );
}

export default MessageList;