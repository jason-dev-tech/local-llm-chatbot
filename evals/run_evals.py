import json
from pathlib import Path

from evals.response_checks import (
    build_rag_eval_response,
    has_inline_citations,
    has_sources_section,
)
from rag.retrieval import retrieve_relevant_chunks
from rag.router import get_routing_decision


def load_test_cases() -> list[dict]:
    test_cases_path = Path(__file__).with_name("test_cases.json")
    with test_cases_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def has_effective_sources(chunks: list[dict]) -> bool:
    return any(chunk.get("metadata", {}).get("source") for chunk in chunks)


def main() -> None:
    test_cases = load_test_cases()
    route_passes = 0
    sources_passes = 0
    citations_passes = 0
    non_rag_clean_passes = 0
    chat_route_passes = 0
    rag_route_passes = 0
    failed_cases = []

    print("Running chatbot evals")
    print()

    for test_case in test_cases:
        decision = get_routing_decision(test_case["query"])
        actual_route = decision.route
        route_ok = actual_route == test_case["expected_route"]
        route_passes += int(route_ok)
        if test_case["expected_route"] == "chat":
            chat_route_passes += int(route_ok)
        elif test_case["expected_route"] == "rag":
            rag_route_passes += int(route_ok)

        chunks = retrieve_relevant_chunks(test_case["query"]) if actual_route == "rag" else []
        response_text = build_rag_eval_response(chunks) if actual_route == "rag" else "General chat response."

        actual_has_sources = has_sources_section(response_text)
        sources_ok = actual_has_sources == test_case["must_include_sources"]
        sources_passes += int(sources_ok)

        actual_has_citations = has_inline_citations(response_text)
        expected_has_citations = test_case["expected_route"] == "rag" and has_effective_sources(chunks)
        citations_ok = actual_has_citations == expected_has_citations
        citations_passes += int(citations_ok)

        non_rag_clean_ok = True
        if actual_route != "rag":
            non_rag_clean_ok = not actual_has_sources and not actual_has_citations
        non_rag_clean_passes += int(non_rag_clean_ok)

        if not route_ok or not sources_ok or not citations_ok or not non_rag_clean_ok:
            failed_checks = []
            if not route_ok:
                failed_checks.append("route")
            if not sources_ok:
                failed_checks.append("sources_section")
            if not citations_ok:
                failed_checks.append("inline_citations")
            if not non_rag_clean_ok:
                failed_checks.append("non_rag_sources")
            failed_cases.append(
                {
                    "id": test_case["id"],
                    "failed_checks": ", ".join(failed_checks),
                }
            )

        print(
            f"[{test_case['id']}] "
            f"route={'PASS' if route_ok else 'FAIL'} "
            f"(expected={test_case['expected_route']}, actual={actual_route}, "
            f"reason={decision.reason}, confidence={decision.confidence:.2f}) | "
            f"sources_section={'PASS' if sources_ok else 'FAIL'} "
            f"(expected={test_case['must_include_sources']}, actual={actual_has_sources}) | "
            f"inline_citations={'PASS' if citations_ok else 'FAIL'} "
            f"(expected={expected_has_citations}, actual={actual_has_citations}) | "
            f"non_rag_sources={'PASS' if non_rag_clean_ok else 'FAIL'}"
        )

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed route checks: {route_passes}/{len(test_cases)}")
    print(f"Passed sources section checks: {sources_passes}/{len(test_cases)}")
    print(f"Passed inline citation checks: {citations_passes}/{len(test_cases)}")
    print(f"Passed non-RAG source checks: {non_rag_clean_passes}/{len(test_cases)}")
    print(f"Overall route pass rate: {route_passes / len(test_cases):.1%}")
    print(f"Overall sources section pass rate: {sources_passes / len(test_cases):.1%}")
    print(f"Overall inline citation pass rate: {citations_passes / len(test_cases):.1%}")
    print(f"Overall non-RAG source pass rate: {non_rag_clean_passes / len(test_cases):.1%}")
    print(f"Chat route pass count: {chat_route_passes}")
    print(f"RAG route pass count: {rag_route_passes}")

    if failed_cases:
        print()
        print("Failed cases:")
        for failed_case in failed_cases:
            print(f"- {failed_case['id']}: {failed_case['failed_checks']}")


if __name__ == "__main__":
    main()
