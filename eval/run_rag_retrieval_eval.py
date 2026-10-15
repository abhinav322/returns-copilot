import json
from pathlib import Path

from backend.rag.pgvector_search import (
    search_policy_chunks,
)


EVAL_FILE = (
    Path(__file__).parent
    / "rag_retrieval_cases.json"
)


TOP_K = 3


def load_cases() -> list[dict]:

    with open(
        EVAL_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def run_evaluation():

    cases = load_cases()

    top_1_hits = 0
    top_3_hits = 0

    reciprocal_rank_total = 0.0

    expected_scores = []

    print()
    print(
        "RAG RETRIEVAL EVALUATION"
    )

    print(
        "========================================"
    )


    for case in cases:

        results = search_policy_chunks(
            query=case["query"],
            top_k=TOP_K,
            region=case["region"],
        )

        expected_rank = None
        expected_score = None


        for index, result in enumerate(
            results,
            start=1,
        ):

            source_matches = (
                result["source"]
                == case["expected_source"]
            )

            heading_matches = (
                result["heading"]
                == case["expected_heading"]
            )


            if (
                source_matches
                and heading_matches
            ):

                expected_rank = index
                expected_score = (
                    result["score"]
                )

                break


        if expected_rank == 1:

            top_1_hits += 1


        if expected_rank is not None:

            top_3_hits += 1

            reciprocal_rank_total += (
                1 / expected_rank
            )

            expected_scores.append(
                expected_score
            )


        print()

        print(
            f"CASE: {case['id']}"
        )

        print(
            f"Query: {case['query']}"
        )

        print(
            "Expected:"
            f" {case['expected_source']}"
            f" / {case['expected_heading']}"
        )


        if expected_rank is None:

            print(
                "Result: MISS ❌"
            )

        else:

            print(
                "Result: HIT ✅"
            )

            print(
                f"Expected rank: "
                f"{expected_rank}"
            )

            print(
                f"Expected score: "
                f"{expected_score:.4f}"
            )


        print(
            "Retrieved:"
        )


        for index, result in enumerate(
            results,
            start=1,
        ):

            print(
                f"  {index}. "
                f"{result['source']} "
                f"/ {result['heading']} "
                f"score="
                f"{result['score']:.4f}"
            )


    total_cases = len(
        cases
    )


    top_1_accuracy = (
        top_1_hits
        / total_cases
    )


    hit_at_3 = (
        top_3_hits
        / total_cases
    )


    mean_reciprocal_rank = (
        reciprocal_rank_total
        / total_cases
    )


    if expected_scores:

        minimum_expected_score = min(
            expected_scores
        )

        average_expected_score = (
            sum(expected_scores)
            / len(expected_scores)
        )

    else:

        minimum_expected_score = 0.0
        average_expected_score = 0.0


    print()
    print(
        "========================================"
    )

    print(
        "SUMMARY"
    )

    print(
        "========================================"
    )

    print(
        f"Cases: {total_cases}"
    )

    print(
        f"Top-1 accuracy: "
        f"{top_1_accuracy:.2%}"
    )

    print(
        f"Hit@3: "
        f"{hit_at_3:.2%}"
    )

    print(
        f"MRR: "
        f"{mean_reciprocal_rank:.4f}"
    )

    print(
        f"Minimum expected score: "
        f"{minimum_expected_score:.4f}"
    )

    print(
        f"Average expected score: "
        f"{average_expected_score:.4f}"
    )


if __name__ == "__main__":

    run_evaluation()