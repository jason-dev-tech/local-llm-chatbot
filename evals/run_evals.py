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

    print("Running chatbot evals")
    print()

    for test_case in test_cases:
        decision = get_routing_decision(test_case["query"])
        actual_route = decision.route
        route_ok = actual_route == test_case["expected_route"]
        route_passes += int(route_ok)

        chunks = retrieve_relevant_chunks(test_case["query"]) if actual_route == "rag" else []
        actual_has_sources = has_effective_sources(chunks)
        source_ok = actual_has_sources == test_case["must_include_sources"]
        source_passes += int(source_ok)

        print(
            f"[{test_case['id']}] "
            f"route={'PASS' if route_ok else 'FAIL'} "
            f"(expected={test_case['expected_route']}, actual={actual_route}) | "
            f"sources={'PASS' if source_ok else 'FAIL'} "
            f"(expected={test_case['must_include_sources']}, actual={actual_has_sources})"
        )

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed route checks: {route_passes}/{len(test_cases)}")
    print(f"Passed source checks: {source_passes}/{len(test_cases)}")


if __name__ == "__main__":
    main()
