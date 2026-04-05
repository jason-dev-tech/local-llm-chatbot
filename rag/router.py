from dataclasses import dataclass


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


@dataclass(frozen=True)
class RoutingDecision:
    route: str
    reason: str
    confidence: float


def get_routing_decision(user_input: str) -> RoutingDecision:
    normalized = user_input.strip().lower()

    if not normalized:
        return RoutingDecision(
            route="chat",
            reason="empty_input",
            confidence=1.0,
        )

    if normalized in SMALL_TALK_INPUTS:
        return RoutingDecision(
            route="chat",
            reason="small_talk_match",
            confidence=0.95,
        )

    if any(keyword in normalized for keyword in RAG_TRIGGER_KEYWORDS):
        return RoutingDecision(
            route="rag",
            reason="keyword_match",
            confidence=0.9,
        )

    return RoutingDecision(
        route="chat",
        reason="no_rag_trigger",
        confidence=0.7,
    )


def should_use_rag(user_input: str) -> bool:
    return get_routing_decision(user_input).route == "rag"
