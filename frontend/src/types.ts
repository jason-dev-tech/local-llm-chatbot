export type SessionItem = {
  session_id: string;
  title: string | null;
};

export type MessageItem = {
  id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
  responseTimeSeconds?: number;
};

export type AssistantTransparencyStatus =
  | "Answer based on sources"
  | "Using retrieved information"
  | "Limited supporting information";
