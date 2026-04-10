import json
from pathlib import Path
from uuid import uuid4

from chat_service import send_message
from db import create_session, delete_session, init_db


def load_test_cases() -> list[dict]:
    test_cases_path = Path(__file__).with_name("retrieval_test_cases.json")
    with test_cases_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _contains_expected_keywords(answer: str, expected_values: list[str]) -> bool:
    normalized_answer = answer.lower()
    return all(
        isinstance(value, str)
        and value.strip()
        and value.lower() in normalized_answer
        for value in expected_values
    )


def main() -> None:
    init_db()
    test_cases = load_test_cases()
    passes = 0

    print("Running RAG response evals")
    print()

    for test_case in test_cases:
        session_id = f"eval_rag_response_{uuid4().hex}"
        create_session(session_id, "Eval")

        try:
            answer = send_message(session_id, test_case["query"])
            expected_values = test_case.get("expected_answer_contains", [])
            passed = _contains_expected_keywords(answer, expected_values)
            passes += int(passed)

            print(
                f"[{test_case['id']}] "
                f"{'PASS' if passed else 'FAIL'} "
                f"expected_contains={expected_values} | "
                f"answer={answer!r}"
            )
        finally:
            delete_session(session_id)

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed: {passes}/{len(test_cases)}")
    print(f"Pass rate: {passes / len(test_cases):.1%}")


if __name__ == "__main__":
    main()
