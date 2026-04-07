import json
from pathlib import Path

from rag.router import get_routing_decision
from routing.llm_router import get_llm_routing_decision
from tools.router import get_tool_routing_decision
from tools.summarize import summarize_text_tool


def load_test_cases() -> list[dict]:
    test_cases_path = Path(__file__).with_name("routing_test_cases.json")
    with test_cases_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_effective_route(query: str) -> tuple[str, str]:
    tool_decision = get_tool_routing_decision(query)
    if tool_decision.tool_name == summarize_text_tool.name:
        return "tool:summarize_text", f"direct_tool:{tool_decision.reason}"

    heuristic_decision = get_routing_decision(query)
    if heuristic_decision.route == "rag":
        return "rag", f"heuristic:{heuristic_decision.reason}"

    llm_decision = get_llm_routing_decision(query)
    if llm_decision.route in {"rag", "tool:summarize_text"}:
        return llm_decision.route, f"llm:{llm_decision.reason}"

    return "chat", f"heuristic:{heuristic_decision.reason}"


def main() -> None:
    test_cases = load_test_cases()
    passes = 0

    print("Running routing evals")
    print()

    for test_case in test_cases:
        query = test_case["query"]
        expected_route = test_case["expected_route"]

        heuristic_decision = get_routing_decision(query)
        llm_decision = get_llm_routing_decision(query)
        effective_route, effective_reason = get_effective_route(query)

        passed = effective_route == expected_route
        passes += int(passed)

        print(
            f"[{test_case['id']}] "
            f"{'PASS' if passed else 'FAIL'} "
            f"expected={expected_route} "
            f"effective={effective_route} "
            f"heuristic={heuristic_decision.route} "
            f"llm={llm_decision.route} "
            f"reason={effective_reason}"
        )

    print()
    print(f"Total cases: {len(test_cases)}")
    print(f"Passed: {passes}/{len(test_cases)}")
    print(f"Pass rate: {passes / len(test_cases):.1%}")


if __name__ == "__main__":
    main()
