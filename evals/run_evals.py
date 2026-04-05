import json
from pathlib import Path

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
    source_passes = 0
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
        actual_has_sources = has_effective_sources(chunks)
        source_ok = actual_has_sources == test_case["must_include_sources"]
        source_passes += int(source_ok)
        if not route_ok or not source_ok:
            failed_checks = []
            if not route_ok:
                failed_checks.append("route")
            if not source_ok:
                failed_checks.append("sources")
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
            f"sources={'PASS' if source_ok else 'FAIL'} "
            f"(expected={test_case['must_include_sources']}, actual={actual_has_sources})"
        )

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed route checks: {route_passes}/{len(test_cases)}")
    print(f"Passed source checks: {source_passes}/{len(test_cases)}")
    print(f"Overall route pass rate: {route_passes / len(test_cases):.1%}")
    print(f"Overall source pass rate: {source_passes / len(test_cases):.1%}")
    print(f"Chat route pass count: {chat_route_passes}")
    print(f"RAG route pass count: {rag_route_passes}")

    if failed_cases:
        print()
        print("Failed cases:")
        for failed_case in failed_cases:
            print(f"- {failed_case['id']}: {failed_case['failed_checks']}")


if __name__ == "__main__":
    main()
