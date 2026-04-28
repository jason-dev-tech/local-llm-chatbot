import argparse
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path


RESPONSE_MODE_ORDER = (
    "chat",
    "tool",
    "rag_response",
    "insufficient_evidence",
)


def _iter_lines(paths: list[str]):
    missing_paths = []

    if not paths:
        for line in sys.stdin:
            yield line
        return

    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            missing_paths.append(raw_path)
            continue

        with path.open("r", encoding="utf-8") as file:
            for line in file:
                yield line

    for raw_path in missing_paths:
        print(
            f"Warning: log file not found or not a regular file: {raw_path}",
            file=sys.stderr,
        )


def _extract_json_text(line: str) -> str | None:
    start = line.find("{")
    end = line.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    return line[start:end + 1]


def _parse_events(paths: list[str]) -> list[dict]:
    events = []

    for raw_line in _iter_lines(paths):
        line = raw_line.strip()
        if not line:
            continue

        json_text = _extract_json_text(line)
        if json_text is None:
            continue

        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            continue

        if isinstance(payload, dict) and isinstance(payload.get("stage"), str):
            events.append(payload)

    return events


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.fmean(values)


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None

    if len(values) == 1:
        return values[0]

    ordered = sorted(values)
    rank = math.ceil(percentile * len(ordered)) - 1
    index = min(max(rank, 0), len(ordered) - 1)
    return ordered[index]


def _format_ms(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f} ms"


def _format_count_map(counter: Counter) -> list[str]:
    if not counter:
        return ["- none"]

    return [f"- {key}: {count}" for key, count in counter.most_common()]


def _format_route_distribution(counter: Counter, total: int) -> list[str]:
    if not counter or total <= 0:
        return ["- none"]

    lines = []
    for route, count in counter.most_common():
        percentage = (count / total) * 100
        lines.append(f"- {route}: {count} ({percentage:.1f}%)")
    return lines


def _format_response_mode_distribution(counter: Counter, total: int) -> list[str]:
    if total <= 0:
        return ["- none"]

    lines = []

    for mode in RESPONSE_MODE_ORDER:
        count = counter.get(mode, 0)
        percentage = (count / total) * 100
        lines.append(f"- {mode}: {count} ({percentage:.1f}%)")

    remaining_modes = sorted(mode for mode in counter if mode not in RESPONSE_MODE_ORDER)
    for mode in remaining_modes:
        count = counter[mode]
        percentage = (count / total) * 100
        lines.append(f"- {mode}: {count} ({percentage:.1f}%)")

    return lines


def _collect_latency_summary(events: list[dict], field_name: str) -> dict:
    values = [
        float(event[field_name])
        for event in events
        if isinstance(event.get(field_name), (int, float))
    ]

    return {
        "count": len(values),
        "average_ms": _safe_mean(values),
        "p50_ms": _percentile(values, 0.50),
        "p95_ms": _percentile(values, 0.95),
    }


def _format_latency_summary(label: str, summary: dict) -> str:
    return (
        f"- {label}: count={summary['count']}, "
        f"avg={_format_ms(summary['average_ms'])}, "
        f"p50={_format_ms(summary['p50_ms'])}, "
        f"p95={_format_ms(summary['p95_ms'])}"
    )


def _collect_response_metrics(response_events: list[dict]) -> dict:
    latencies = [
        float(event["latency_ms"])
        for event in response_events
        if isinstance(event.get("latency_ms"), (int, float))
    ]

    route_counter = Counter()
    route_latencies: dict[str, list[float]] = {}
    response_mode_counter = Counter()
    tool_counter = Counter()

    for event in response_events:
        route = event.get("effective_route")
        if isinstance(route, str) and route:
            route_counter[route] += 1

            latency = event.get("latency_ms")
            if isinstance(latency, (int, float)):
                route_latencies.setdefault(route, []).append(float(latency))

        response_mode = event.get("response_mode")
        if isinstance(response_mode, str) and response_mode:
            response_mode_counter[response_mode] += 1
        else:
            response_mode_counter["unknown"] += 1

        tool_name = event.get("tool_used")
        if isinstance(tool_name, str) and tool_name:
            tool_counter[tool_name] += 1

    return {
        "request_count": len(response_events),
        "average_latency_ms": _safe_mean(latencies),
        "p50_latency_ms": _percentile(latencies, 0.50),
        "p95_latency_ms": _percentile(latencies, 0.95),
        "route_distribution": route_counter,
        "route_latencies": route_latencies,
        "response_mode_distribution": response_mode_counter,
        "tool_usage": tool_counter,
    }


def _collect_outcome_metrics(response_events: list[dict], error_events: list[dict]) -> dict:
    total_successes = len(response_events)
    total_failures = len(error_events)
    total_outcomes = total_successes + total_failures

    route_outcomes: dict[str, dict[str, int]] = {}

    for event in response_events:
        route = event.get("effective_route")
        if not isinstance(route, str) or not route:
            route = "unknown"
        route_outcomes.setdefault(route, {"success": 0, "failure": 0})
        route_outcomes[route]["success"] += 1

    for event in error_events:
        route = event.get("effective_route")
        if not isinstance(route, str) or not route:
            route = "unknown"
        route_outcomes.setdefault(route, {"success": 0, "failure": 0})
        route_outcomes[route]["failure"] += 1

    return {
        "request_count": total_outcomes,
        "success_count": total_successes,
        "failure_count": total_failures,
        "success_rate": (total_successes / total_outcomes) if total_outcomes else None,
        "route_outcomes": route_outcomes,
    }


def _collect_session_metrics(response_events: list[dict], error_events: list[dict]) -> dict:
    session_requests = Counter()
    session_route_usage: dict[str, Counter] = {}

    for event in [*response_events, *error_events]:
        session_id = event.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            continue

        session_requests[session_id] += 1

        route = event.get("effective_route")
        if not isinstance(route, str) or not route:
            route = "unknown"

        session_route_usage.setdefault(session_id, Counter())
        session_route_usage[session_id][route] += 1

    return {
        "active_session_count": len(session_requests),
        "requests_per_session": session_requests,
        "route_usage_per_session": session_route_usage,
    }


def _collect_query_metrics(response_events: list[dict], error_events: list[dict], retrieval_events: list[dict]) -> dict:
    repeated_queries = Counter()
    route_queries: dict[str, Counter] = {}
    zero_retrieval_queries = Counter()

    for event in [*response_events, *error_events]:
        user_query = event.get("user_query")
        if not isinstance(user_query, str) or not user_query.strip():
            continue

        normalized_query = user_query.strip()
        if normalized_query.startswith("/"):
            continue

        repeated_queries[normalized_query] += 1

        route = event.get("effective_route")
        if not isinstance(route, str) or not route:
            route = "unknown"

        route_queries.setdefault(route, Counter())
        route_queries[route][normalized_query] += 1

    for event in retrieval_events:
        route = event.get("effective_route")
        if route != "rag":
            continue

        if event.get("retrieved_chunk_count") != 0:
            continue

        user_query = event.get("user_query")
        if not isinstance(user_query, str) or not user_query.strip():
            continue

        normalized_query = user_query.strip()
        if normalized_query.startswith("/"):
            continue

        zero_retrieval_queries[normalized_query] += 1

    return {
        "repeated_queries": repeated_queries,
        "route_queries": route_queries,
        "zero_retrieval_queries": zero_retrieval_queries,
    }


def _collect_retrieval_metrics(retrieval_events: list[dict]) -> dict:
    chunk_counts = [
        int(event["retrieved_chunk_count"])
        for event in retrieval_events
        if isinstance(event.get("retrieved_chunk_count"), int)
    ]

    filename_counter = Counter()
    zero_retrieval_count = 0

    for event in retrieval_events:
        retrieved_chunk_count = event.get("retrieved_chunk_count")
        if retrieved_chunk_count == 0:
            zero_retrieval_count += 1

        filenames = event.get("retrieved_filenames", [])
        if isinstance(filenames, list):
            for filename in filenames:
                if isinstance(filename, str) and filename.strip():
                    filename_counter[filename.strip()] += 1

    return {
        "retrieval_event_count": len(retrieval_events),
        "average_retrieved_chunk_count": _safe_mean(chunk_counts),
        "zero_retrieval_count": zero_retrieval_count,
        "top_filenames": filename_counter,
        "retrieval_latency": _collect_latency_summary(retrieval_events, "retrieval_latency_ms"),
    }


def _collect_route_metadata_metrics(response_events: list[dict]) -> dict:
    retrieval_scope_counter = Counter()
    tool_step_chain_counter = Counter()
    route_reason_counter = Counter()
    source_counts = []
    route_confidences = []

    for event in response_events:
        route_metadata = event.get("route_metadata")
        if not isinstance(route_metadata, dict):
            continue

        retrieval_scope = route_metadata.get("retrieval_scope")
        if isinstance(retrieval_scope, str) and retrieval_scope:
            retrieval_scope_counter[retrieval_scope] += 1
        else:
            retrieval_scope_counter["none"] += 1

        tool_steps = route_metadata.get("tool_steps")
        if isinstance(tool_steps, list):
            steps = [
                step
                for step in tool_steps
                if isinstance(step, str) and step.strip()
            ]
            if steps:
                tool_step_chain_counter[" -> ".join(steps)] += 1

        route_reason = route_metadata.get("route_reason")
        if isinstance(route_reason, str) and route_reason.strip():
            route_reason_counter[route_reason.strip()] += 1

        if route_metadata.get("route") == "rag":
            source_count = route_metadata.get("source_count")
            if isinstance(source_count, int):
                source_counts.append(source_count)

        route_confidence = route_metadata.get("route_confidence")
        if isinstance(route_confidence, (int, float)):
            route_confidences.append(float(route_confidence))

    return {
        "event_count": sum(
            1
            for event in response_events
            if isinstance(event.get("route_metadata"), dict)
        ),
        "retrieval_scope_distribution": retrieval_scope_counter,
        "tool_step_chain_frequency": tool_step_chain_counter,
        "route_reason_frequency": route_reason_counter,
        "average_rag_source_count": _safe_mean(source_counts),
        "route_confidence": {
            "count": len(route_confidences),
            "average": _safe_mean(route_confidences),
            "p50": _percentile(route_confidences, 0.50),
            "p95": _percentile(route_confidences, 0.95),
        },
    }


def _format_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def build_metrics_report(events: list[dict]) -> str:
    if not events:
        return (
            "No structured observability logs were found.\n\n"
            "Provide one or more log files, or pipe backend output into the command."
        )

    response_events = [event for event in events if event.get("stage") == "response"]
    error_events = [event for event in events if event.get("stage") == "error"]
    retrieval_events = [event for event in events if event.get("stage") == "retrieval"]

    if not response_events and not error_events and not retrieval_events:
        return (
            "No supported observability events were found.\n\n"
            "Expected JSON log lines with a `stage` field such as `response`, `error`, or `retrieval`."
        )

    response_metrics = _collect_response_metrics(response_events)
    outcome_metrics = _collect_outcome_metrics(response_events, error_events)
    session_metrics = _collect_session_metrics(response_events, error_events)
    query_metrics = _collect_query_metrics(response_events, error_events, retrieval_events)
    retrieval_metrics = _collect_retrieval_metrics(retrieval_events)
    route_metadata_metrics = _collect_route_metadata_metrics(response_events)
    stage_latency_metrics = {
        "route_decision": _collect_latency_summary(response_events, "route_decision_latency_ms"),
        "retrieval": _collect_latency_summary(response_events, "retrieval_latency_ms"),
        "llm_generation": _collect_latency_summary(response_events, "llm_generation_latency_ms"),
        "total_request": _collect_latency_summary(response_events, "latency_ms"),
    }

    lines = [
        "Metrics Summary",
        "",
        "Request-level metrics",
        f"- Overall request count: {outcome_metrics['request_count']}",
        f"- Successful response count: {response_metrics['request_count']}",
        f"- Overall average response-stage latency: {_format_ms(response_metrics['average_latency_ms'])}",
        f"- Response-stage latency p50: {_format_ms(response_metrics['p50_latency_ms'])}",
        f"- Response-stage latency p95: {_format_ms(response_metrics['p95_latency_ms'])}",
        "",
        "Stage latency metrics",
        _format_latency_summary("Route decision", stage_latency_metrics["route_decision"]),
        _format_latency_summary("Retrieval", stage_latency_metrics["retrieval"]),
        _format_latency_summary("LLM generation", stage_latency_metrics["llm_generation"]),
        _format_latency_summary("Total request", stage_latency_metrics["total_request"]),
        "",
        "Request outcome metrics",
        f"- Overall success count: {outcome_metrics['success_count']}",
        f"- Overall failure count: {outcome_metrics['failure_count']}",
        (
            f"- Overall success rate: {outcome_metrics['success_rate'] * 100:.1f}%"
            if outcome_metrics["success_rate"] is not None
            else "- Overall success rate: n/a"
        ),
        "",
        "Per-route outcomes",
    ]

    route_outcomes = outcome_metrics["route_outcomes"]
    if route_outcomes:
        for route in sorted(route_outcomes):
            success_count = route_outcomes[route]["success"]
            failure_count = route_outcomes[route]["failure"]
            total_count = success_count + failure_count
            success_rate = (success_count / total_count) if total_count else 0.0
            lines.append(
                f"- {route}: success={success_count}, failure={failure_count}, "
                f"success_rate={success_rate * 100:.1f}%"
            )
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
        "Average response-stage latency by effective route",
        ]
    )

    route_latencies = response_metrics["route_latencies"]
    if route_latencies:
        for route, values in sorted(route_latencies.items()):
            lines.append(f"- {route}: {_format_ms(_safe_mean(values))}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Successful response distribution by effective route",
            *_format_route_distribution(
                response_metrics["route_distribution"],
                response_metrics["request_count"],
            ),
            "",
            "Response mode distribution",
            *_format_response_mode_distribution(
                response_metrics["response_mode_distribution"],
                response_metrics["request_count"],
            ),
            "",
            "Tool usage frequency",
            *_format_count_map(response_metrics["tool_usage"]),
            "",
            "Route metadata metrics",
            f"- Response events with route_metadata: {route_metadata_metrics['event_count']}",
            "- Retrieval scope distribution:",
            *_format_count_map(route_metadata_metrics["retrieval_scope_distribution"]),
            "- Tool step chain frequency:",
            *_format_count_map(route_metadata_metrics["tool_step_chain_frequency"]),
            f"- Average source count for RAG responses: "
            f"{_format_number(route_metadata_metrics['average_rag_source_count'])}",
            "- Route reason frequency:",
            *_format_count_map(route_metadata_metrics["route_reason_frequency"]),
            (
                "- Route confidence: "
                f"count={route_metadata_metrics['route_confidence']['count']}, "
                f"avg={_format_number(route_metadata_metrics['route_confidence']['average'])}, "
                f"p50={_format_number(route_metadata_metrics['route_confidence']['p50'])}, "
                f"p95={_format_number(route_metadata_metrics['route_confidence']['p95'])}"
            ),
            "",
            "Session usage metrics",
            f"- Active session count: {session_metrics['active_session_count']}",
            "- Requests per session:",
            *(
                [f"- {session_id}: {count}" for session_id, count in session_metrics["requests_per_session"].most_common()]
                if session_metrics["requests_per_session"]
                else ["- none"]
            ),
            "",
            "Route usage per session",
            *(
                [
                    f"- {session_id}: "
                    + ", ".join(
                        f"{route}={count}"
                        for route, count in session_metrics["route_usage_per_session"][session_id].most_common()
                    )
                    for session_id, _count in session_metrics["requests_per_session"].most_common()
                ]
                if session_metrics["route_usage_per_session"]
                else ["- none"]
            ),
            "",
            "Query insights",
            "- Top repeated user queries:",
            *(
                [f"- {query}: {count}" for query, count in query_metrics["repeated_queries"].most_common(5)]
                if query_metrics["repeated_queries"]
                else ["- none"]
            ),
            "",
            "Query counts grouped by effective route",
            *(
                [
                    f"- {route}: "
                    + ", ".join(
                        f"{query}={count}"
                        for query, count in query_metrics["route_queries"][route].most_common(5)
                    )
                    for route in sorted(query_metrics["route_queries"])
                ]
                if query_metrics["route_queries"]
                else ["- none"]
            ),
            "",
            "Top zero-retrieval queries",
            *(
                [f"- {query}: {count}" for query, count in query_metrics["zero_retrieval_queries"].most_common(5)]
                if query_metrics["zero_retrieval_queries"]
                else ["- none"]
            ),
            "",
            "Retrieval-event metrics",
            f"- Retrieval event count: {retrieval_metrics['retrieval_event_count']}",
            f"- Average retrieved chunk count: "
            f"{retrieval_metrics['average_retrieved_chunk_count']:.2f}"
            if retrieval_metrics["average_retrieved_chunk_count"] is not None
            else "- Average retrieved chunk count: n/a",
            f"- Zero-retrieval case count: {retrieval_metrics['zero_retrieval_count']}",
            _format_latency_summary("Retrieval event latency", retrieval_metrics["retrieval_latency"]),
            "- Most frequently retrieved filenames:",
            *_format_count_map(retrieval_metrics["top_filenames"]),
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize structured observability logs for the local AI chatbot.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional log file paths. If omitted, the command reads from stdin.",
    )
    args = parser.parse_args()

    events = _parse_events(args.paths)
    print(build_metrics_report(events))


if __name__ == "__main__":
    main()
