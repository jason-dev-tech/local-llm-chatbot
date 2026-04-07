import json
from dataclasses import dataclass
import re

from tools.registry import get_tool


SUMMARIZE_TRIGGERS = {
    "summarize",
    "summary",
}
SUMMARIZE_TOOL_NAME = "summarize_text"
REWRITE_TRIGGERS = {
    "rewrite",
    "rephrase",
    "make this clearer",
    "improve this sentence",
}
REWRITE_TOOL_NAME = "rewrite_text"
EXTRACT_ENTITIES_TRIGGERS = {
    "extract entities",
    "extract entity",
}
EXTRACT_ENTITIES_TOOL_NAME = "extract_entities"
SUMMARIZE_INPUT_PREFIX_PATTERN = re.compile(
    r"^(?:this text:|the following text:|text:)\s*",
    re.IGNORECASE,
)
REWRITE_INPUT_PREFIX_PATTERN = re.compile(
    r"^(?:this text:|the following text:|text:)\s*",
    re.IGNORECASE,
)
EXTRACT_ENTITIES_INPUT_PREFIX_PATTERN = re.compile(
    r"^(?:this text:|the following text:|text:)\s*",
    re.IGNORECASE,
)
INFORMATIVE_CHARACTER_PATTERN = re.compile(r"[A-Za-z0-9]")


@dataclass(frozen=True)
class ToolRoutingDecision:
    tool_name: str | None
    tool_input: str | None
    reason: str
    confidence: float


def normalize_summarize_input(tool_input: str) -> str:
    normalized = tool_input.strip()
    return SUMMARIZE_INPUT_PREFIX_PATTERN.sub("", normalized).strip()


def normalize_rewrite_input(tool_input: str) -> str:
    normalized = tool_input.strip()
    return REWRITE_INPUT_PREFIX_PATTERN.sub("", normalized).strip()


def normalize_extract_entities_input(tool_input: str) -> str:
    normalized = tool_input.strip()
    return EXTRACT_ENTITIES_INPUT_PREFIX_PATTERN.sub("", normalized).strip()


def _get_structured_query_type(user_input: str) -> str | None:
    extract_entities_tool = get_tool(EXTRACT_ENTITIES_TOOL_NAME)
    if extract_entities_tool is None:
        return None

    try:
        payload = json.loads(extract_entities_tool.run(user_input))
    except (TypeError, json.JSONDecodeError):
        return None

    query_type = payload.get("query_type")
    return query_type if isinstance(query_type, str) else None


def get_tool_routing_decision(user_input: str) -> ToolRoutingDecision:
    normalized = user_input.strip()
    lowered = normalized.lower()

    if not normalized:
        return ToolRoutingDecision(
            tool_name=None,
            tool_input=None,
            reason="empty_input",
            confidence=1.0,
        )

    structured_query_type = _get_structured_query_type(normalized)

    for trigger in SUMMARIZE_TRIGGERS:
        if lowered == trigger:
            return ToolRoutingDecision(
                tool_name=SUMMARIZE_TOOL_NAME,
                tool_input="",
                reason="summarize_exact_match",
                confidence=0.95,
            )

        if lowered.startswith(f"{trigger} "):
            remainder = normalized[len(trigger):].strip()
            normalized_remainder = normalize_summarize_input(remainder)
            if remainder == normalized_remainder:
                continue

            return ToolRoutingDecision(
                tool_name=SUMMARIZE_TOOL_NAME,
                tool_input=normalized_remainder,
                reason="summarize_prefix_match",
                confidence=0.95,
            )

        marker = f"{trigger}:"
        if lowered.startswith(marker):
            return ToolRoutingDecision(
                tool_name=SUMMARIZE_TOOL_NAME,
                tool_input=normalize_summarize_input(normalized[len(marker):]),
                reason="summarize_prefix_match",
                confidence=0.95,
            )

    for trigger in REWRITE_TRIGGERS:
        if lowered == trigger:
            return ToolRoutingDecision(
                tool_name=REWRITE_TOOL_NAME,
                tool_input="",
                reason="rewrite_exact_match",
                confidence=0.95,
            )

        if lowered.startswith(f"{trigger} "):
            remainder = normalized[len(trigger):].strip()
            normalized_remainder = normalize_rewrite_input(remainder)
            if remainder == normalized_remainder:
                continue

            return ToolRoutingDecision(
                tool_name=REWRITE_TOOL_NAME,
                tool_input=normalized_remainder,
                reason="rewrite_prefix_match",
                confidence=0.95,
            )

        marker = f"{trigger}:"
        if lowered.startswith(marker):
            return ToolRoutingDecision(
                tool_name=REWRITE_TOOL_NAME,
                tool_input=normalize_rewrite_input(normalized[len(marker):]),
                reason="rewrite_prefix_match",
                confidence=0.95,
            )

    for trigger in EXTRACT_ENTITIES_TRIGGERS:
        if lowered == trigger:
            return ToolRoutingDecision(
                tool_name=EXTRACT_ENTITIES_TOOL_NAME,
                tool_input="",
                reason="extract_entities_exact_match",
                confidence=0.95,
            )

        marker = f"{trigger}:"
        if lowered.startswith(marker):
            return ToolRoutingDecision(
                tool_name=EXTRACT_ENTITIES_TOOL_NAME,
                tool_input=normalize_extract_entities_input(normalized[len(marker):]),
                reason="extract_entities_prefix_match",
                confidence=0.95,
            )

    if structured_query_type == "summarization":
        return ToolRoutingDecision(
            tool_name=None,
            tool_input=None,
            reason="structured_summarization_deferred_to_rag",
            confidence=0.8,
        )

    return ToolRoutingDecision(
        tool_name=None,
        tool_input=None,
        reason="no_tool_trigger",
        confidence=0.7,
    )


def maybe_run_tool(user_input: str) -> str | None:
    decision = get_tool_routing_decision(user_input)
    if decision.tool_name not in {SUMMARIZE_TOOL_NAME, REWRITE_TOOL_NAME}:
        if decision.tool_name != EXTRACT_ENTITIES_TOOL_NAME:
            return None

    tool = get_tool(decision.tool_name)
    if tool is None:
        return None

    if decision.tool_name == REWRITE_TOOL_NAME and (
        not decision.tool_input or not INFORMATIVE_CHARACTER_PATTERN.search(decision.tool_input)
    ):
        return "Please provide text to rewrite."

    if not decision.tool_input:
        if decision.tool_name == SUMMARIZE_TOOL_NAME:
            return "Please provide text to summarize."
        if decision.tool_name == REWRITE_TOOL_NAME:
            return "Please provide text to rewrite."
        if decision.tool_name == EXTRACT_ENTITIES_TOOL_NAME:
            return "Please provide text to extract entities from."
        return None

    return tool.run(decision.tool_input)
