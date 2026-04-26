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
SUMMARIZE_REWRITE_TOOL_NAME = "summarize_then_rewrite"
EXTRACT_ENTITIES_TRIGGERS = {
    "extract entities",
    "extract entity",
}
EXTRACT_ENTITIES_TOOL_NAME = "extract_entities"
SUMMARIZE_THEN_REWRITE_PATTERN = re.compile(
    r"^(?:summarize|summary)\s+(?:this text:|the following(?: text)?:)?\s*(.+?)\s+and then\s+rewrite(?: it)?(?: more clearly| professionally| clearly)?\s*:\s*(.+)$",
    re.IGNORECASE,
)
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


@dataclass(frozen=True)
class ToolWorkflowPlan:
    steps: list[str]
    tool_input: str
    reason: str
    confidence: float


@dataclass(frozen=True)
class ToolWorkflowResult:
    output: str
    tools_used: list[str]
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


def _extract_summarize_then_rewrite_input(user_input: str) -> str | None:
    match = SUMMARIZE_THEN_REWRITE_PATTERN.match(user_input.strip())
    if not match:
        return None

    prefix_text = normalize_summarize_input(match.group(1))
    main_text = match.group(2).strip()

    if prefix_text and not main_text:
        main_text = prefix_text

    normalized_text = main_text.strip()
    return normalized_text or None


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
    summarize_then_rewrite_input = _extract_summarize_then_rewrite_input(normalized)
    if summarize_then_rewrite_input is not None:
        return ToolRoutingDecision(
            tool_name=SUMMARIZE_REWRITE_TOOL_NAME,
            tool_input=summarize_then_rewrite_input,
            reason="summarize_then_rewrite_match",
            confidence=0.98,
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


def plan_tool_workflow(user_input: str) -> ToolWorkflowPlan | None:
    decision = get_tool_routing_decision(user_input)
    if decision.tool_name == SUMMARIZE_REWRITE_TOOL_NAME:
        return ToolWorkflowPlan(
            steps=[SUMMARIZE_TOOL_NAME, REWRITE_TOOL_NAME],
            tool_input=decision.tool_input or "",
            reason=decision.reason,
            confidence=decision.confidence,
        )

    if decision.tool_name in {SUMMARIZE_TOOL_NAME, REWRITE_TOOL_NAME, EXTRACT_ENTITIES_TOOL_NAME}:
        return ToolWorkflowPlan(
            steps=[decision.tool_name],
            tool_input=decision.tool_input or "",
            reason=decision.reason,
            confidence=decision.confidence,
        )

    return None


def run_tool_workflow(user_input: str) -> ToolWorkflowResult | None:
    plan = plan_tool_workflow(user_input)
    if plan is None:
        return None

    if plan.steps == [SUMMARIZE_TOOL_NAME, REWRITE_TOOL_NAME]:
        summarize_tool = get_tool(SUMMARIZE_TOOL_NAME)
        rewrite_tool = get_tool(REWRITE_TOOL_NAME)
        if summarize_tool is None or rewrite_tool is None:
            return None
        if not plan.tool_input:
            return ToolWorkflowResult(
                output="Please provide text to summarize.",
                tools_used=[],
                reason=plan.reason,
                confidence=plan.confidence,
            )

        summary = summarize_tool.run(plan.tool_input)
        if not summary.strip():
            return ToolWorkflowResult(
                output="Please provide text to summarize.",
                tools_used=[SUMMARIZE_TOOL_NAME],
                reason=plan.reason,
                confidence=plan.confidence,
            )

        return ToolWorkflowResult(
            output=rewrite_tool.run(summary),
            tools_used=plan.steps,
            reason=plan.reason,
            confidence=plan.confidence,
        )

    tool_name = plan.steps[0]
    tool = get_tool(tool_name)
    if tool is None:
        return None

    if tool_name == REWRITE_TOOL_NAME and (
        not plan.tool_input or not INFORMATIVE_CHARACTER_PATTERN.search(plan.tool_input)
    ):
        return ToolWorkflowResult(
            output="Please provide text to rewrite.",
            tools_used=[],
            reason=plan.reason,
            confidence=plan.confidence,
        )

    if not plan.tool_input:
        if tool_name == SUMMARIZE_TOOL_NAME:
            output = "Please provide text to summarize."
        elif tool_name == REWRITE_TOOL_NAME:
            output = "Please provide text to rewrite."
        elif tool_name == EXTRACT_ENTITIES_TOOL_NAME:
            output = "Please provide text to extract entities from."
        else:
            return None

        return ToolWorkflowResult(
            output=output,
            tools_used=[],
            reason=plan.reason,
            confidence=plan.confidence,
        )

    return ToolWorkflowResult(
        output=tool.run(plan.tool_input),
        tools_used=[tool_name],
        reason=plan.reason,
        confidence=plan.confidence,
    )


def maybe_run_tool(user_input: str) -> str | None:
    result = run_tool_workflow(user_input)
    if result is None:
        return None

    return result.output
