import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from chat_service import send_message_and_stream
from db import create_session, delete_session, init_db


def load_test_cases() -> list[dict]:
    test_cases_path = Path(__file__).with_name("route_metadata_test_cases.json")
    with test_cases_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def run_streaming_query(query: str) -> dict | None:
    metadata = {}
    session_id = f"eval_route_metadata_{uuid4().hex}"
    create_session(session_id, "Eval")

    try:
        for _token in send_message_and_stream(
            session_id,
            query,
            metadata_callback=metadata.update,
        ):
            pass
        route_metadata = metadata.get("route_metadata")
        return route_metadata if isinstance(route_metadata, dict) else None
    finally:
        delete_session(session_id)


def evaluate_case(test_case: dict, route_metadata: dict | None) -> dict:
    if route_metadata is None:
        return {
            "route": False,
            "response_mode": False,
            "retrieval_scope": False,
            "tool_steps": False,
            "source_count": False,
        }

    source_count = route_metadata.get("source_count")
    min_source_count = test_case.get("min_source_count")
    expected_source_count = test_case.get("expected_source_count")

    if min_source_count is not None:
        source_count_ok = isinstance(source_count, int) and source_count >= min_source_count
    else:
        source_count_ok = source_count == expected_source_count

    return {
        "route": route_metadata.get("route") == test_case["expected_route"],
        "response_mode": route_metadata.get("response_mode") == test_case["expected_response_mode"],
        "retrieval_scope": route_metadata.get("retrieval_scope") == test_case["expected_retrieval_scope"],
        "tool_steps": route_metadata.get("tool_steps") == test_case["expected_tool_steps"],
        "source_count": source_count_ok,
    }


def main() -> None:
    init_db()
    test_cases = load_test_cases()
    field_passes = {
        "route": 0,
        "response_mode": 0,
        "retrieval_scope": 0,
        "tool_steps": 0,
        "source_count": 0,
    }
    case_passes = 0

    print("Running route metadata evals")
    print()

    for test_case in test_cases:
        try:
            route_metadata = run_streaming_query(test_case["query"])
            checks = evaluate_case(test_case, route_metadata)
            passed = all(checks.values())
        except Exception as error:
            route_metadata = None
            checks = {key: False for key in field_passes}
            passed = False
            error_message = f"{type(error).__name__}: {error}"
        else:
            error_message = None

        case_passes += int(passed)
        for field_name, field_passed in checks.items():
            field_passes[field_name] += int(field_passed)

        check_summary = " | ".join(
            f"{field_name}={'PASS' if field_passed else 'FAIL'}"
            for field_name, field_passed in checks.items()
        )
        print(
            f"[{test_case['id']}] "
            f"{'PASS' if passed else 'FAIL'} "
            f"{check_summary} | "
            f"metadata={route_metadata!r}"
        )
        if test_case.get("note"):
            print(f"  note={test_case['note']}")
        if error_message:
            print(f"  error={error_message}")

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed cases: {case_passes}/{len(test_cases)}")
    for field_name, passed_count in field_passes.items():
        print(f"Passed {field_name} checks: {passed_count}/{len(test_cases)}")
    print(f"Overall pass rate: {case_passes / len(test_cases):.1%}")


if __name__ == "__main__":
    main()
