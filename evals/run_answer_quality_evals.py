import json
from pathlib import Path
from uuid import uuid4

from chat_service import get_effective_routing_decision, get_response_mode, has_usable_retrieval_evidence, send_message
from db import create_session, delete_session, init_db
from rag.retrieval import retrieve_relevant_chunks
from tools.router import get_tool_routing_decision


def load_test_cases() -> list[dict]:
    test_cases_path = Path(__file__).with_name("answer_quality_test_cases.json")
    with test_cases_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def infer_response_mode(query: str) -> str:
    tool_decision = get_tool_routing_decision(query)
    if tool_decision.tool_name:
        return get_response_mode("tool", tool_decision.tool_name, evidence_sufficient=None)

    routing_decision = get_effective_routing_decision(query)
    route = routing_decision.route
    if route != "rag":
        return get_response_mode(route, None, evidence_sufficient=None)

    chunks = retrieve_relevant_chunks(query)
    evidence_sufficient = has_usable_retrieval_evidence(query, chunks)
    return get_response_mode(route, None, evidence_sufficient=evidence_sufficient)


def main() -> None:
    init_db()
    test_cases = load_test_cases()
    response_mode_passes = 0
    groundedness_passes = 0
    hallucination_passes = 0

    print("Running answer quality evals")
    print()

    for test_case in test_cases:
        session_id = f"eval_quality_{uuid4().hex}"
        create_session(session_id, "Eval")

        try:
            answer = send_message(session_id, test_case["query"])
            actual_response_mode = infer_response_mode(test_case["query"])

            expected_response_mode = test_case["expected_response_mode"]
            response_mode_ok = actual_response_mode == expected_response_mode

            must_contain = test_case.get("must_contain", [])
            groundedness_ok = all(value in answer for value in must_contain)

            must_not_contain = test_case.get("must_not_contain", [])
            hallucination_ok = all(value not in answer for value in must_not_contain)

            response_mode_passes += int(response_mode_ok)
            groundedness_passes += int(groundedness_ok)
            hallucination_passes += int(hallucination_ok)

            print(
                f"[{test_case['id']}] "
                f"response_mode={'PASS' if response_mode_ok else 'FAIL'} "
                f"(expected={expected_response_mode}, actual={actual_response_mode}) | "
                f"groundedness={'PASS' if groundedness_ok else 'FAIL'} | "
                f"hallucination={'PASS' if hallucination_ok else 'FAIL'}"
            )
        finally:
            delete_session(session_id)

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed response_mode checks: {response_mode_passes}/{len(test_cases)}")
    print(f"Passed groundedness checks: {groundedness_passes}/{len(test_cases)}")
    print(f"Passed hallucination checks: {hallucination_passes}/{len(test_cases)}")
    print(f"Overall response_mode pass rate: {response_mode_passes / len(test_cases):.1%}")
    print(f"Overall groundedness pass rate: {groundedness_passes / len(test_cases):.1%}")
    print(f"Overall hallucination pass rate: {hallucination_passes / len(test_cases):.1%}")


if __name__ == "__main__":
    main()
