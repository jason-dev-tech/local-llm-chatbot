import type { FormEvent } from "react";

type ChatInputProps = {
  input: string;
  isSending: boolean;
  disabled: boolean;
  onInputChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
};

function ChatInput({
  input,
  isSending,
  disabled,
  onInputChange,
  onSubmit,
}: ChatInputProps) {
  return (
    <form className="chat-input-area" onSubmit={onSubmit}>
      <textarea
        value={input}
        onChange={(event) => onInputChange(event.target.value)}
        placeholder="Type your message..."
        rows={3}
        disabled={disabled || isSending}
      />
      <button type="submit" disabled={disabled || isSending}>
        {isSending ? "Thinking..." : "Send"}
      </button>
    </form>
  );
}

export default ChatInput;