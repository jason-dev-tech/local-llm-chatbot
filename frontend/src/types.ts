export type SessionItem = {
  session_id: string;
  title: string | null;
};

export type MessageItem = {
  id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
};