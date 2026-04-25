import type { FormEvent } from "react";
import type { ReactNode } from "react";

type ChatInputProps = {
  input: string;
  isSending: boolean;
  disabled: boolean;
  attachmentControls?: ReactNode;
  onInputChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
};

function ChatInput({
  input,
  isSending,
  disabled,
  attachmentControls,
  onInputChange,
  onSubmit,
}: ChatInputProps) {
  return (
    <form className="chat-input-area" onSubmit={onSubmit}>
      <div className="chat-input-field">
        {attachmentControls}
        <textarea
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          placeholder="Type your message..."
          rows={1}
          disabled={disabled || isSending}
        />
      </div>
      <button className="send-button" type="submit" disabled={disabled || isSending}>
        {isSending ? "Thinking..." : "Send"}
      </button>
    </form>
  );
}

export default ChatInput;
