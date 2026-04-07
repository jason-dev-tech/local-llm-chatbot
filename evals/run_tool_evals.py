import json
from pathlib import Path

from tools.router import get_tool_routing_decision, maybe_run_tool


def load_test_cases() -> list[dict]:
    test_cases_path = Path(__file__).with_name("tool_test_cases.json")
    with test_cases_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    test_cases = load_test_cases()
    route_passes = 0
    response_passes = 0

    print("Running tool evals")
    print()

    for test_case in test_cases:
        decision = get_tool_routing_decision(test_case["query"])
        actual_tool_name = decision.tool_name
        actual_response = maybe_run_tool(test_case["query"])

        route_ok = actual_tool_name == test_case["expected_tool_name"]
        response_checks = []

        if "expected_response" in test_case:
            response_checks.append(actual_response == test_case.get("expected_response"))

        if "expected_response_contains" in test_case:
            expected_contains = test_case["expected_response_contains"]
            response_checks.append(
                actual_response is not None and all(
                    value in actual_response for value in expected_contains
                )
            )

        if "expected_response_not_contains" in test_case:
            expected_not_contains = test_case["expected_response_not_contains"]
            response_checks.append(
                actual_response is not None and all(
                    value not in actual_response for value in expected_not_contains
                )
            )

        if test_case.get("expected_response_not_equal_input"):
            response_checks.append(
                actual_response is not None and actual_response != test_case["tool_input"]
            )

        if test_case.get("expected_response_not_equal_query"):
            response_checks.append(
                actual_response is not None and actual_response != test_case["query"]
            )

        if test_case.get("expected_response_non_empty"):
            response_checks.append(
                actual_response is not None and bool(actual_response.strip())
            )

        response_ok = all(response_checks) if response_checks else True

        route_passes += int(route_ok)
        response_passes += int(response_ok)

        print(
            f"[{test_case['id']}] "
            f"route={'PASS' if route_ok else 'FAIL'} "
            f"(expected={test_case['expected_tool_name']}, actual={actual_tool_name}, reason={decision.reason}) | "
            f"response={'PASS' if response_ok else 'FAIL'} "
            f"(expected={test_case.get('expected_response')!r}, actual={actual_response!r})"
        )

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed route checks: {route_passes}/{len(test_cases)}")
    print(f"Passed response checks: {response_passes}/{len(test_cases)}")
    print(f"Overall route pass rate: {route_passes / len(test_cases):.1%}")
    print(f"Overall response pass rate: {response_passes / len(test_cases):.1%}")


if __name__ == "__main__":
    main()
