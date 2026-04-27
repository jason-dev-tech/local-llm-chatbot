import type { SessionItem, MessageItem, RouteMetadata } from "../types";

declare global {
  interface Window {
    __APP_CONFIG__?: {
      apiBaseUrl?: string;
    };
  }
}

export type ReadinessResult = {
  isReady: boolean;
  notReadyReason: string | null;
};

export type KnowledgeUploadResult = {
  filename: string;
  status: string;
};

export type ChatStreamDoneMetadata = {
  retrieval_scope?: "global" | "session";
  response_explanation?: string;
  route_metadata?: RouteMetadata;
};

const API_BASE =
  window.__APP_CONFIG__?.apiBaseUrl?.trim() ||
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  "http://127.0.0.1:8000";

function parseRouteMetadata(value: unknown): RouteMetadata | undefined {
  if (!value || typeof value !== "object") {
    return undefined;
  }

  const metadata = value as Record<string, unknown>;
  const route = metadata.route;
  const toolSteps = metadata.tool_steps;

  if (route !== "chat" && route !== "rag" && route !== "tool") {
    return undefined;
  }

  if (typeof metadata.response_mode !== "string") {
    return undefined;
  }

  return {
    route,
    response_mode: metadata.response_mode,
    retrieval_scope:
      metadata.retrieval_scope === "global" || metadata.retrieval_scope === "session"
        ? metadata.retrieval_scope
        : null,
    tool_steps: Array.isArray(toolSteps)
      ? toolSteps.filter((step): step is string => typeof step === "string")
      : [],
    route_reason:
      typeof metadata.route_reason === "string" ? metadata.route_reason : null,
    route_confidence:
      typeof metadata.route_confidence === "number" ? metadata.route_confidence : null,
    source_count:
      typeof metadata.source_count === "number" ? metadata.source_count : null,
  };
}

/**
 * Get all sessions
 */
export async function fetchSessions(): Promise<SessionItem[]> {
  const res = await fetch(`${API_BASE}/sessions`);

  if (!res.ok) {
    throw new Error("Failed to fetch sessions");
  }

  return res.json();
}

/**
 * Create a new session
 */
export async function createSession(): Promise<SessionItem> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
  });

  if (!res.ok) {
    throw new Error("Failed to create session");
  }

  return res.json();
}

/**
 * Get messages of a session
 */
export async function fetchMessages(sessionId: string): Promise<MessageItem[]> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);

  if (!res.ok) {
    throw new Error("Failed to fetch messages");
  }

  return res.json();
}

/**
 * Backend readiness check
 */
export async function fetchReadiness(): Promise<ReadinessResult> {
  try {
    const res = await fetch(`${API_BASE}/ready`);
    let payload: unknown = null;

    try {
      payload = await res.json();
    } catch {
      payload = null;
    }

    const checks =
      payload && typeof payload === "object" && "checks" in payload
        ? (payload as { checks?: Record<string, unknown> }).checks
        : undefined;
    const status =
      payload && typeof payload === "object" && "status" in payload
        ? (payload as { status?: unknown }).status
        : undefined;
    const payloadReady =
      status === "ready"
      || (
        checks !== undefined
        && checks !== null
        && Object.values(checks).every((value) => value === true)
      );

    if (payloadReady) {
      return {
        isReady: true,
        notReadyReason: null,
      };
    }

    if (checks?.chat_endpoint_ready === false) {
      return {
        isReady: false,
        notReadyReason: "Model service is unavailable.",
      };
    }

    if (checks?.embedding_endpoint_ready === false) {
      return {
        isReady: false,
        notReadyReason: "Knowledge features are unavailable.",
      };
    }

    return {
      isReady: false,
      notReadyReason: "Some AI features are unavailable.",
    };
  } catch {
    return {
      isReady: false,
      notReadyReason: "Backend service is unavailable.",
    };
  }
}

/**
 * Upload a document to the knowledge base
 */
export async function uploadKnowledgeDocument(file: File): Promise<KnowledgeUploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/knowledge/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let message = "Failed to upload document";

    try {
      const payload = await res.json();
      if (payload && typeof payload === "object" && "detail" in payload) {
        const detail = (payload as { detail?: unknown }).detail;
        if (typeof detail === "string" && detail.trim()) {
          message = detail;
        }
      }
    } catch {
      // Keep the default message when the response is not JSON.
    }

    throw new Error(message);
  }

  return res.json();
}

/**
 * Upload a document for the current chat session
 */
export async function uploadSessionDocument(
  sessionId: string,
  file: File,
): Promise<KnowledgeUploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/sessions/${sessionId}/attachments`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let message = "Failed to attach document";

    try {
      const payload = await res.json();
      if (payload && typeof payload === "object" && "detail" in payload) {
        const detail = (payload as { detail?: unknown }).detail;
        if (typeof detail === "string" && detail.trim()) {
          message = detail;
        }
      }
    } catch {
      // Keep the default message when the response is not JSON.
    }

    throw new Error(message);
  }

  return res.json();
}

/**
 * Rename session
 */
export async function renameSession(sessionId: string, title: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });

  if (!res.ok) {
    throw new Error("Failed to rename session");
  }
}

/**
 * Delete session
 */
export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    throw new Error("Failed to delete session");
  }
}

/**
 * Streaming chat (NDJSON)
 */
export async function streamChat(
  sessionId: string,
  message: string,
  onToken: (token: string) => void,
  onDone?: (metadata: ChatStreamDoneMetadata) => void,
  onError?: (errorMessage: string) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
    }),
  });

  if (!res.ok || !res.body) {
    throw new Error("Failed to start stream");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const data = JSON.parse(line);

        if (data.type === "token") {
          onToken(data.content);
        } else if (data.type === "done") {
          onDone?.({
            retrieval_scope:
              data.retrieval_scope === "global" || data.retrieval_scope === "session"
                ? data.retrieval_scope
                : undefined,
            response_explanation:
              typeof data.response_explanation === "string"
                ? data.response_explanation
                : undefined,
            route_metadata: parseRouteMetadata(data.route_metadata),
          });
        } else if (data.type === "error") {
          onError?.(data.message);
        }
      } catch (err) {
        console.error("Failed to parse stream chunk:", line);
      }
    }
  }
}
