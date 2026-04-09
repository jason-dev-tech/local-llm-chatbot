import json
from pathlib import Path

from chat_service import get_response_mode, has_usable_retrieval_evidence
from rag.retrieval import retrieve_relevant_chunks
from rag.router import get_routing_decision
from tools.router import get_tool_routing_decision


def load_test_cases() -> list[dict]:
    test_cases_path = Path(__file__).with_name("guardrail_test_cases.json")
    with test_cases_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_query(query: str) -> dict:
    tool_decision = get_tool_routing_decision(query)
    if tool_decision.tool_name:
        return {
            "effective_route": "tool",
            "response_mode": "tool",
            "guardrail_type": None,
        }

    routing_decision = get_routing_decision(query)
    if routing_decision.route != "rag":
        return {
            "effective_route": "chat",
            "response_mode": "chat",
            "guardrail_type": None,
        }

    chunks = retrieve_relevant_chunks(query)
    evidence_sufficient = has_usable_retrieval_evidence(query, chunks)
    response_mode = get_response_mode(
        "rag",
        None,
        evidence_sufficient=evidence_sufficient,
    )

    return {
        "effective_route": "rag",
        "response_mode": response_mode,
        "guardrail_type": None if evidence_sufficient else "insufficient_evidence",
    }


def main() -> None:
    test_cases = load_test_cases()
    route_passes = 0
    response_mode_passes = 0
    guardrail_passes = 0

    print("Running guardrail evals")
    print()

    for test_case in test_cases:
        result = evaluate_query(test_case["query"])

        route_ok = result["effective_route"] == test_case["expected_route"]
        response_mode_ok = result["response_mode"] == test_case["expected_response_mode"]
        guardrail_ok = result["guardrail_type"] == test_case["expected_guardrail_type"]

        route_passes += int(route_ok)
        response_mode_passes += int(response_mode_ok)
        guardrail_passes += int(guardrail_ok)

        print(
            f"[{test_case['id']}] "
            f"route={'PASS' if route_ok else 'FAIL'} "
            f"(expected={test_case['expected_route']}, actual={result['effective_route']}) | "
            f"response_mode={'PASS' if response_mode_ok else 'FAIL'} "
            f"(expected={test_case['expected_response_mode']}, actual={result['response_mode']}) | "
            f"guardrail={'PASS' if guardrail_ok else 'FAIL'} "
            f"(expected={test_case['expected_guardrail_type']}, actual={result['guardrail_type']})"
        )

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed route checks: {route_passes}/{len(test_cases)}")
    print(f"Passed response_mode checks: {response_mode_passes}/{len(test_cases)}")
    print(f"Passed guardrail checks: {guardrail_passes}/{len(test_cases)}")
    print(f"Overall route pass rate: {route_passes / len(test_cases):.1%}")
    print(f"Overall response_mode pass rate: {response_mode_passes / len(test_cases):.1%}")
    print(f"Overall guardrail pass rate: {guardrail_passes / len(test_cases):.1%}")


if __name__ == "__main__":
    main()
