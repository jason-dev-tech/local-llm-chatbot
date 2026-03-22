RAG_TRIGGER_KEYWORDS = {
    "rag",
    "retrieval",
    "retrieval-augmented",
    "knowledge base",
    "knowledge",
    "document",
    "documents",
    "context",
    "explain",
    "what is",
    "how does",
    "how do",
    "why does",
    "summarize",
}


SMALL_TALK_INPUTS = {
    "hi",
    "hello",
    "hey",
    "thanks",
    "thank you",
    "bye",
    "goodbye",
    "how are you",
    "what can you do",
    "tell me a joke",
}


def should_use_rag(user_input: str) -> bool:
    normalized = user_input.strip().lower()

    if not normalized:
        return False

    if normalized in SMALL_TALK_INPUTS:
        return False

    return any(keyword in normalized for keyword in RAG_TRIGGER_KEYWORDS)