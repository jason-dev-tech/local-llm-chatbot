from dataclasses import dataclass
import re


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

KNOWLEDGE_QUERY_PREFIXES = (
    "what is ",
    "who is ",
    "when is ",
    "where is ",
    "why does ",
    "how does ",
    "explain ",
    "define ",
    "describe ",
    "tell me about ",
)

TECHNICAL_QUERY_TERMS = {
    "api",
    "endpoint",
    "protocol",
    "architecture",
    "design",
    "implementation",
    "workflow",
    "specification",
    "documentation",
    "config",
    "schema",
    "model",
    "algorithm",
    "policy",
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

ENTITY_LOOKUP_TERMS = {
    "status",
    "company",
    "customer",
    "person",
    "vendor",
    "employee",
    "account",
    "record",
}

FACT_LOOKUP_PREFIXES = (
    "which ",
    "what is the status of ",
    "what is the name of ",
    "what is the location of ",
    "what is the address of ",
    "who is ",
    "where is ",
)

SHORT_ENTITY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9 .&'_-]{1,59}$")


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


def _looks_like_knowledge_query(normalized: str) -> bool:
    if not normalized.startswith(KNOWLEDGE_QUERY_PREFIXES):
        return False

    if normalized in SMALL_TALK_INPUTS:
        return False

    return True


def _looks_like_entity_lookup_query(normalized: str) -> bool:
    if normalized in SMALL_TALK_INPUTS or len(normalized) < 3:
        return False

    if normalized.endswith("?"):
        if normalized.startswith(FACT_LOOKUP_PREFIXES):
            return True
        if any(term in normalized for term in ENTITY_LOOKUP_TERMS):
            return True

    if SHORT_ENTITY_PATTERN.fullmatch(normalized):
        token_count = len(normalized.split())
        if 1 <= token_count <= 4 and any(character.isalpha() for character in normalized):
            return True

    return False


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

    if _looks_like_knowledge_query(normalized):
        return RoutingDecision(
            route="rag",
            reason="knowledge_query_match",
            confidence=0.85,
        )

    if _looks_like_entity_lookup_query(normalized):
        return RoutingDecision(
            route="rag",
            reason="entity_lookup_match",
            confidence=0.82,
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
