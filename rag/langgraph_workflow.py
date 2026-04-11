from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph


class RagWorkflowState(TypedDict, total=False):
    user_input: str
    history: list[dict]
    file_filters: list[str] | None
    chunks: list[dict]
    context_text: str
    evidence_sufficient: bool
    system_prompt: str
    raw_answer: str
    final_answer: str
    mode: str
    stream_callback: Callable[[str], None] | None


def _ensure_current_user_message(history: list[dict], user_input: str) -> list[dict]:
    if history and history[-1].get("role") == "user" and history[-1].get("content") == user_input:
        return history
    return history + [{"role": "user", "content": user_input}]


def build_rag_workflow(
    *,
    retrieve_chunks: Callable[[str, int, list[str] | None], list[dict]],
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
        chunks = retrieve_chunks(
            state["user_input"],
            3,
            state.get("file_filters"),
        )
        context_text = build_context_text(chunks)
        system_prompt = build_system_prompt(context_text, state["user_input"])
        return {
            "chunks": chunks,
            "context_text": context_text,
            "system_prompt": system_prompt,
        }

    def evidence_node(state: RagWorkflowState) -> RagWorkflowState:
        chunks = state.get("chunks", [])
        return {
            "evidence_sufficient": check_evidence(state["user_input"], chunks),
        }

    def route_after_evidence(state: RagWorkflowState) -> str:
        return "generate" if state.get("evidence_sufficient") else "insufficient"

    def generate_node(state: RagWorkflowState) -> RagWorkflowState:
        system_prompt = state.get("system_prompt", "")
        if state.get("mode") == "stream":
            raw_answer = generate_stream(
                system_prompt,
                state["user_input"],
                state.get("stream_callback"),
            )
        else:
            messages = [{"role": "system", "content": system_prompt}] + _ensure_current_user_message(
                state.get("history", []),
                state["user_input"],
            )
            raw_answer = generate_sync(messages)

        return {"raw_answer": raw_answer}

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
    graph.add_edge("generate", "format")
    graph.add_edge("format", END)
    graph.add_edge("insufficient", END)

    return graph.compile()
