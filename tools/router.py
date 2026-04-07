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
}
REWRITE_TOOL_NAME = "rewrite_text"
SUMMARIZE_INPUT_PREFIX_PATTERN = re.compile(
    r"^(?:this text:|the following text:|text:)\s*",
    re.IGNORECASE,
)
REWRITE_INPUT_PREFIX_PATTERN = re.compile(
    r"^(?:this text:|the following text:|text:)\s*",
    re.IGNORECASE,
)


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

    return ToolRoutingDecision(
        tool_name=None,
        tool_input=None,
        reason="no_tool_trigger",
        confidence=0.7,
    )


def maybe_run_tool(user_input: str) -> str | None:
    decision = get_tool_routing_decision(user_input)
    if decision.tool_name not in {SUMMARIZE_TOOL_NAME, REWRITE_TOOL_NAME}:
        return None

    tool = get_tool(decision.tool_name)
    if tool is None:
        return None

    if not decision.tool_input:
        if decision.tool_name == SUMMARIZE_TOOL_NAME:
            return "Please provide text to summarize."
        if decision.tool_name == REWRITE_TOOL_NAME:
            return "Please provide text to rewrite."
        return None

    return tool.run(decision.tool_input)
