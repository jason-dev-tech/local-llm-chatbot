export type SessionItem = {
  session_id: string;
  title: string | null;
};

export type MessageItem = {
  id?: number;
  role: "user" | "assistant" | "attachment";
  content: string;
  created_at?: string;
  responseTimeSeconds?: number;
  retrievalScope?: "global" | "session";
  responseExplanation?: string;
  routeMetadata?: RouteMetadata;
};

export type RouteMetadata = {
  route: "chat" | "rag" | "tool";
  response_mode: string;
  retrieval_scope: "global" | "session" | null;
  tool_steps: string[];
  route_reason: string | null;
  route_confidence: number | null;
  source_count: number | null;
};

export type AssistantTransparencyStatus =
  | "Answer based on sources"
  | "Using retrieved information"
  | "Limited supporting information";
