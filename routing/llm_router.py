import re
from dataclasses import dataclass

from llm_langchain import generate_langchain_response
from tools.router import normalize_summarize_input


ROUTE_PATTERN = re.compile(r"^ROUTE:\s*(.+)$", re.MULTILINE)
TOOL_INPUT_PATTERN = re.compile(r"^TOOL_INPUT:\s*(.*)$", re.MULTILINE)
REASON_PATTERN = re.compile(r"^REASON:\s*(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class LLMRoutingDecision:
    route: str
    tool_input: str
    reason: str
    confidence: float


def _build_router_prompt(user_input: str) -> str:
    return (
        "You are a routing classifier for a local AI chatbot.\n"
        "Choose exactly one route:\n"
        "- chat\n"
        "- rag\n"
        "- tool:summarize_text\n\n"
        "Use tool:summarize_text only when the user is asking to summarize text they already provided.\n"
        "Use rag when the user is asking about the knowledge base, documents, retrieval, semantic search, or RAG concepts.\n"
        "Use chat for general conversation.\n\n"
        "Return exactly this format:\n"
        "ROUTE: <chat|rag|tool:summarize_text>\n"
        "TOOL_INPUT: <text for summarize tool or empty>\n"
        "REASON: <short reason>\n\n"
        f"User input:\n{user_input}"
    )


def _extract_summarize_tool_input(user_input: str, proposed_tool_input: str) -> str:
    if proposed_tool_input.strip():
        return normalize_summarize_input(proposed_tool_input)

    lowered = user_input.lower()
    for trigger in ("summarize", "summary"):
        index = lowered.find(trigger)
        if index != -1:
            remainder = user_input[index + len(trigger):].lstrip(" :")
            return normalize_summarize_input(remainder)

    return ""


def get_llm_routing_decision(user_input: str) -> LLMRoutingDecision:
    try:
        raw_response = generate_langchain_response(_build_router_prompt(user_input))
    except Exception:
        return LLMRoutingDecision(
            route="chat",
            tool_input="",
            reason="llm_router_error",
            confidence=0.0,
        )

    route_match = ROUTE_PATTERN.search(raw_response)
    tool_input_match = TOOL_INPUT_PATTERN.search(raw_response)
    reason_match = REASON_PATTERN.search(raw_response)

    route = route_match.group(1).strip() if route_match else "chat"
    if route not in {"chat", "rag", "tool:summarize_text"}:
        route = "chat"

    tool_input = tool_input_match.group(1).strip() if tool_input_match else ""
    if route == "tool:summarize_text":
        tool_input = _extract_summarize_tool_input(user_input, tool_input)
    else:
        tool_input = ""

    reason = reason_match.group(1).strip() if reason_match else "llm_router_default"

    return LLMRoutingDecision(
        route=route,
        tool_input=tool_input,
        reason=reason,
        confidence=0.6,
    )
