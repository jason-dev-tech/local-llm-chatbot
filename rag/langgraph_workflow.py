import time
from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph


class RagWorkflowState(TypedDict, total=False):
    user_input: str
    history: list[dict]
    file_filters: list[str] | None
    session_id: str | None
    chunks: list[dict]
    context_text: str
    evidence_sufficient: bool
    system_prompt: str
    raw_answer: str
    answer_valid: bool
    retried: bool
    final_answer: str
    retrieval_latency_ms: float
    llm_generation_latency_ms: float
    mode: str
    stream_callback: Callable[[str], None] | None


def _elapsed_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 2)


def _ensure_current_user_message(history: list[dict], user_input: str) -> list[dict]:
    if history and history[-1].get("role") == "user" and history[-1].get("content") == user_input:
        return history
    return history + [{"role": "user", "content": user_input}]


def _generate_raw_answer(
    state: RagWorkflowState,
    generate_sync: Callable[[list[dict]], str],
    generate_stream: Callable[[str, str, Callable[[str], None] | None], str],
) -> str:
    system_prompt = state.get("system_prompt", "")
    if state.get("mode") == "stream":
        return generate_stream(
            system_prompt,
            state["user_input"],
            state.get("stream_callback"),
        )

    messages = [{"role": "system", "content": system_prompt}] + _ensure_current_user_message(
        state.get("history", []),
        state["user_input"],
    )
    return generate_sync(messages)


def build_rag_workflow(
    *,
    retrieve_chunks: Callable[[str, int, list[str] | None, str | None], list[dict]],
    build_context_text: Callable[[list[dict]], str],
    build_system_prompt: Callable[[str, str], str],
    check_evidence: Callable[[str, list[dict]], bool],
    generate_sync: Callable[[list[dict]], str],
    generate_stream: Callable[[str, str, Callable[[str], None] | None], str],
    format_answer: Callable[[str, list[dict]], str],
    insufficient_response: str,
):
    graph = StateGraph(RagWorkflowState)

    def retrieve_node(state: RagWorkflowState) -> RagWorkflowState:
        started_at = time.perf_counter()
        chunks = retrieve_chunks(
            state["user_input"],
            3,
            state.get("file_filters"),
            state.get("session_id"),
        )
        context_text = build_context_text(chunks)
        system_prompt = build_system_prompt(context_text, state["user_input"])
        return {
            "chunks": chunks,
            "context_text": context_text,
            "system_prompt": system_prompt,
            "retrieval_latency_ms": _elapsed_ms(started_at),
        }

    def evidence_node(state: RagWorkflowState) -> RagWorkflowState:
        chunks = state.get("chunks", [])
        return {
            "evidence_sufficient": check_evidence(state["user_input"], chunks),
        }

    def route_after_evidence(state: RagWorkflowState) -> str:
        return "generate" if state.get("evidence_sufficient") else "insufficient"

    def generate_node(state: RagWorkflowState) -> RagWorkflowState:
        started_at = time.perf_counter()
        return {
            "raw_answer": _generate_raw_answer(state, generate_sync, generate_stream),
            "llm_generation_latency_ms": _elapsed_ms(started_at),
        }

    def validate_answer_node(state: RagWorkflowState) -> RagWorkflowState:
        raw_answer = state.get("raw_answer", "")
        chunks = state.get("chunks", [])
        answer_valid = bool(raw_answer.strip())
        if answer_valid and chunks:
            answer_valid = "[" in raw_answer
        return {"answer_valid": answer_valid}

    def route_after_validation(state: RagWorkflowState) -> str:
        return "format" if state.get("answer_valid") else "retry_generate"

    def retry_generate_node(state: RagWorkflowState) -> RagWorkflowState:
        started_at = time.perf_counter()
        raw_answer = _generate_raw_answer(state, generate_sync, generate_stream)
        previous_latency = state.get("llm_generation_latency_ms", 0)
        return {
            "raw_answer": raw_answer,
            "llm_generation_latency_ms": previous_latency + _elapsed_ms(started_at),
            "retried": True,
        }

    def insufficient_node(_: RagWorkflowState) -> RagWorkflowState:
        return {"final_answer": insufficient_response}

    def format_node(state: RagWorkflowState) -> RagWorkflowState:
        return {
            "final_answer": format_answer(
                state.get("raw_answer", ""),
                state.get("chunks", []),
            )
        }

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("check_evidence", evidence_node)
    graph.add_node("generate", generate_node)
    graph.add_node("validate_answer", validate_answer_node)
    graph.add_node("retry_generate", retry_generate_node)
    graph.add_node("insufficient", insufficient_node)
    graph.add_node("format", format_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "check_evidence")
    graph.add_conditional_edges(
        "check_evidence",
        route_after_evidence,
        {
            "generate": "generate",
            "insufficient": "insufficient",
        },
    )
    graph.add_edge("generate", "validate_answer")
    graph.add_conditional_edges(
        "validate_answer",
        route_after_validation,
        {
            "format": "format",
            "retry_generate": "retry_generate",
        },
    )
    graph.add_edge("retry_generate", "format")
    graph.add_edge("format", END)
    graph.add_edge("insufficient", END)

    return graph.compile()
