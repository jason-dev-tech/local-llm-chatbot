from dataclasses import dataclass


RAG_STRONG_TRIGGERS = {
    "rag",
    "retrieval",
    "retrieval-augmented",
    "knowledge base",
    "semantic search",
    "context",
}

RAG_CONTEXT_TERMS = {
    "knowledge",
    "document",
    "documents",
    "citation",
    "citations",
    "metadata",
    "grounding",
    "chunking",
    "source",
    "sources",
}

RAG_INTENT_TERMS = {
    "explain",
    "what is",
    "what are",
    "what does",
    "define",
    "how does",
    "how do",
    "why does",
    "why do",
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

    if any(keyword in normalized for keyword in RAG_STRONG_TRIGGERS):
        return RoutingDecision(
            route="rag",
            reason="strong_keyword_match",
            confidence=0.9,
        )

    if any(term in normalized for term in RAG_CONTEXT_TERMS) and normalized.endswith("?"):
        return RoutingDecision(
            route="rag",
            reason="factual_question_match",
            confidence=0.8,
        )

    if any(term in normalized for term in RAG_CONTEXT_TERMS) and any(
        term in normalized for term in RAG_INTENT_TERMS
    ):
        return RoutingDecision(
            route="rag",
            reason="contextual_keyword_match",
            confidence=0.8,
        )

    return RoutingDecision(
        route="chat",
        reason="no_rag_trigger",
        confidence=0.7,
    )


def should_use_rag(user_input: str) -> bool:
    return get_routing_decision(user_input).route == "rag"
