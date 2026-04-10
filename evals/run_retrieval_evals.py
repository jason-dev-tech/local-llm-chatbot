import json
from pathlib import Path

from rag.retrieval import retrieve_relevant_chunks
from rag.source_metadata import resolve_chunk_source


def load_test_cases() -> list[dict]:
    test_cases_path = Path(__file__).with_name("retrieval_test_cases.json")
    with test_cases_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _extract_retrieved_sources(chunks: list[dict]) -> list[str]:
    sources = []

    for chunk in chunks:
        source = resolve_chunk_source(chunk)
        if source and source not in sources:
            sources.append(source)

    return sources


def _build_metrics(expected_sources: list[str], retrieved_sources: list[str]) -> dict:
    expected_set = {
        source.strip()
        for source in expected_sources
        if isinstance(source, str) and source.strip()
    }
    retrieved_set = set(retrieved_sources)

    matched_sources = [
        source for source in retrieved_sources
        if source in expected_set
    ]
    hit = bool(matched_sources)
    recall = (
        len(expected_set & retrieved_set) / len(expected_set)
        if expected_set
        else 0.0
    )

    first_relevant_rank = None
    for index, source in enumerate(retrieved_sources, start=1):
        if source in expected_set:
            first_relevant_rank = index
            break

    return {
        "hit": hit,
        "recall": recall,
        "first_relevant_rank": first_relevant_rank,
        "matched_sources": matched_sources,
    }


def main() -> None:
    test_cases = load_test_cases()
    hit_passes = 0
    full_recall_passes = 0
    recall_total = 0.0
    reciprocal_rank_total = 0.0

    print("Running retrieval evals")
    print()

    for test_case in test_cases:
        top_k = test_case.get("top_k", 3)
        expected_sources = test_case["expected_sources"]
        chunks = retrieve_relevant_chunks(test_case["query"], top_k=top_k)
        retrieved_sources = _extract_retrieved_sources(chunks)
        metrics = _build_metrics(expected_sources, retrieved_sources)

        hit_passes += int(metrics["hit"])
        full_recall_passes += int(metrics["recall"] == 1.0)
        recall_total += metrics["recall"]
        if metrics["first_relevant_rank"] is not None:
            reciprocal_rank_total += 1 / metrics["first_relevant_rank"]

        first_relevant_rank = (
            str(metrics["first_relevant_rank"])
            if metrics["first_relevant_rank"] is not None
            else "not_found"
        )

        print(
            f"[{test_case['id']}] "
            f"top_k_hit={'PASS' if metrics['hit'] else 'FAIL'} "
            f"(top_k={top_k}) | "
            f"recall@{top_k}={metrics['recall']:.2f} | "
            f"first_relevant_rank={first_relevant_rank} | "
            f"expected={expected_sources} | "
            f"retrieved={retrieved_sources}"
        )

    total_cases = len(test_cases)
    average_recall = (
        recall_total / total_cases
        if total_cases
        else 0.0
    )
    mean_reciprocal_rank = (
        reciprocal_rank_total / total_cases
        if total_cases
        else 0.0
    )

    print()
    print(f"Total cases: {total_cases}")
    print(f"Top-k hit passes: {hit_passes}/{total_cases}")
    print(f"Full recall passes: {full_recall_passes}/{total_cases}")
    print(f"Average recall@k: {average_recall:.2f}")
    print(f"Mean reciprocal rank: {mean_reciprocal_rank:.2f}")


if __name__ == "__main__":
    main()
