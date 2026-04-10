import type { SessionItem, MessageItem } from "../types";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

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
  onDone?: () => void,
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
          onDone?.();
        } else if (data.type === "error") {
          onError?.(data.message);
        }
      } catch (err) {
        console.error("Failed to parse stream chunk:", line);
      }
    }
  }
}
