import argparse
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path


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


def _collect_response_metrics(response_events: list[dict]) -> dict:
    latencies = [
        float(event["latency_ms"])
        for event in response_events
        if isinstance(event.get("latency_ms"), (int, float))
    ]

    route_counter = Counter()
    route_latencies: dict[str, list[float]] = {}
    tool_counter = Counter()

    for event in response_events:
        route = event.get("effective_route")
        if isinstance(route, str) and route:
            route_counter[route] += 1

            latency = event.get("latency_ms")
            if isinstance(latency, (int, float)):
                route_latencies.setdefault(route, []).append(float(latency))

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
        "tool_usage": tool_counter,
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
    }


def build_metrics_report(events: list[dict]) -> str:
    if not events:
        return (
            "No structured observability logs were found.\n\n"
            "Provide one or more log files, or pipe backend output into the command."
        )

    response_events = [event for event in events if event.get("stage") == "response"]
    retrieval_events = [event for event in events if event.get("stage") == "retrieval"]

    if not response_events and not retrieval_events:
        return (
            "No supported observability events were found.\n\n"
            "Expected JSON log lines with a `stage` field such as `response` or `retrieval`."
        )

    response_metrics = _collect_response_metrics(response_events)
    retrieval_metrics = _collect_retrieval_metrics(retrieval_events)

    lines = [
        "Metrics Summary",
        "",
        "Request-level metrics",
        f"- Overall request count: {response_metrics['request_count']}",
        f"- Overall average response-stage latency: {_format_ms(response_metrics['average_latency_ms'])}",
        f"- Response-stage latency p50: {_format_ms(response_metrics['p50_latency_ms'])}",
        f"- Response-stage latency p95: {_format_ms(response_metrics['p95_latency_ms'])}",
        "",
        "Average response-stage latency by effective route",
    ]

    route_latencies = response_metrics["route_latencies"]
    if route_latencies:
        for route, values in sorted(route_latencies.items()):
            lines.append(f"- {route}: {_format_ms(_safe_mean(values))}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Route distribution",
            *_format_route_distribution(
                response_metrics["route_distribution"],
                response_metrics["request_count"],
            ),
            "",
            "Tool usage frequency",
            *_format_count_map(response_metrics["tool_usage"]),
            "",
            "Retrieval-event metrics",
            f"- Retrieval event count: {retrieval_metrics['retrieval_event_count']}",
            f"- Average retrieved chunk count: "
            f"{retrieval_metrics['average_retrieved_chunk_count']:.2f}"
            if retrieval_metrics["average_retrieved_chunk_count"] is not None
            else "- Average retrieved chunk count: n/a",
            f"- Zero-retrieval case count: {retrieval_metrics['zero_retrieval_count']}",
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
