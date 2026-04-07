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
        response_ok = actual_response == test_case["expected_response"]
        route_passes += int(route_ok)
        response_passes += int(response_ok)

        print(
            f"[{test_case['id']}] "
            f"route={'PASS' if route_ok else 'FAIL'} "
            f"(expected={test_case['expected_tool_name']}, actual={actual_tool_name}, reason={decision.reason}) | "
            f"response={'PASS' if response_ok else 'FAIL'} "
            f"(expected={test_case['expected_response']!r}, actual={actual_response!r})"
        )

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed route checks: {route_passes}/{len(test_cases)}")
    print(f"Passed response checks: {response_passes}/{len(test_cases)}")
    print(f"Overall route pass rate: {route_passes / len(test_cases):.1%}")
    print(f"Overall response pass rate: {response_passes / len(test_cases):.1%}")


if __name__ == "__main__":
    main()
