import json

from pathlib import Path

from backend.rag.pgvector_search import (
    search_policy_chunks,
)


POSITIVE_FILE = (
    Path(__file__).parent
    / "rag_retrieval_cases.json"
)

NEGATIVE_FILE = (
    Path(__file__).parent
    / "rag_negative_cases.json"
)


THRESHOLDS = [
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
]


def load_json(
    path: Path,
) -> list[dict]:

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def evaluate_positive_cases(
    cases: list[dict],
) -> list[dict]:

    evaluated = []


    for case in cases:

        results = search_policy_chunks(
            query=case["query"],
            top_k=3,
            region=case["region"],
        )


        expected_rank = None
        expected_score = None


        for index, result in enumerate(
            results,
            start=1,
        ):

            if (
                result["source"]
                == case["expected_source"]

                and

                result["heading"]
                == case["expected_heading"]
            ):

                expected_rank = index
                expected_score = (
                    result["score"]
                )

                break


        top_score = (
            results[0]["score"]
            if results
            else 0.0
        )


        evaluated.append(
            {
                "id":
                    case["id"],

                "query":
                    case["query"],

                "expected_rank":
                    expected_rank,

                "expected_score":
                    expected_score,

                "top_score":
                    top_score,
            }
        )


    return evaluated


def evaluate_negative_cases(
    cases: list[dict],
) -> list[dict]:

    evaluated = []


    for case in cases:

        results = search_policy_chunks(
            query=case["query"],
            top_k=3,
            region=case["region"],
        )


        top_result = (
            results[0]
            if results
            else None
        )


        evaluated.append(
            {
                "id":
                    case["id"],

                "query":
                    case["query"],

                "top_score":
                    (
                        top_result["score"]
                        if top_result
                        else 0.0
                    ),

                "top_source":
                    (
                        top_result["source"]
                        if top_result
                        else None
                    ),

                "top_heading":
                    (
                        top_result["heading"]
                        if top_result
                        else None
                    ),
            }
        )


    return evaluated


def safe_divide(
    numerator: int,
    denominator: int,
) -> float:

    if denominator == 0:

        return 0.0

    return (
        numerator
        / denominator
    )


def run_evaluation():

    positive_cases = load_json(
        POSITIVE_FILE
    )

    negative_cases = load_json(
        NEGATIVE_FILE
    )


    print()
    print(
        "RAG THRESHOLD EVALUATION"
    )

    print(
        "========================================"
    )


    positives = (
        evaluate_positive_cases(
            positive_cases
        )
    )

    negatives = (
        evaluate_negative_cases(
            negative_cases
        )
    )


    print()
    print(
        "POSITIVE CASES"
    )

    print(
        "========================================"
    )


    for case in positives:

        print()

        print(
            f"{case['id']}"
        )

        print(
            f"  Expected rank: "
            f"{case['expected_rank']}"
        )

        if (
            case["expected_score"]
            is None
        ):

            print(
                "  Expected score: "
                "NOT FOUND"
            )

        else:

            print(
                f"  Expected score: "
                f"{case['expected_score']:.4f}"
            )

        print(
            f"  Top result score: "
            f"{case['top_score']:.4f}"
        )


    print()
    print(
        "NEGATIVE / UNSUPPORTED CASES"
    )

    print(
        "========================================"
    )


    for case in negatives:

        print()

        print(
            f"{case['id']}"
        )

        print(
            f"  Top result: "
            f"{case['top_source']} "
            f"/ {case['top_heading']}"
        )

        print(
            f"  Top score: "
            f"{case['top_score']:.4f}"
        )


    print()
    print(
        "========================================"
    )

    print(
        "THRESHOLD COMPARISON"
    )

    print(
        "========================================"
    )

    print(
        "Threshold | Precision | Recall | "
        "Specificity | F1 | False accepts"
    )

    print(
        "----------------------------------------"
        "--------------------------"
    )


    for threshold in THRESHOLDS:

        true_positive = sum(
            1
            for case in positives
            if (
                case["expected_score"]
                is not None

                and

                case["expected_score"]
                >= threshold
            )
        )


        false_negative = (
            len(positives)
            - true_positive
        )


        false_positive = sum(
            1
            for case in negatives
            if (
                case["top_score"]
                >= threshold
            )
        )


        true_negative = (
            len(negatives)
            - false_positive
        )


        precision = safe_divide(
            true_positive,
            true_positive
            + false_positive,
        )


        recall = safe_divide(
            true_positive,
            true_positive
            + false_negative,
        )


        specificity = safe_divide(
            true_negative,
            true_negative
            + false_positive,
        )


        if (
            precision
            + recall
            == 0
        ):

            f1 = 0.0

        else:

            f1 = (
                2
                * precision
                * recall
                / (
                    precision
                    + recall
                )
            )


        print(
            f"{threshold:>8.2f} | "
            f"{precision:>9.2%} | "
            f"{recall:>6.2%} | "
            f"{specificity:>11.2%} | "
            f"{f1:>6.2%} | "
            f"{false_positive}"
        )


    positive_scores = [
        case["expected_score"]

        for case in positives

        if (
            case["expected_score"]
            is not None
        )
    ]


    negative_scores = [
        case["top_score"]

        for case in negatives
    ]


    print()
    print(
        "========================================"
    )

    print(
        "SCORE DISTRIBUTION"
    )

    print(
        "========================================"
    )


    if positive_scores:

        print(
            "Lowest correct-evidence score: "
            f"{min(positive_scores):.4f}"
        )


    if negative_scores:

        print(
            "Highest unsupported-query score: "
            f"{max(negative_scores):.4f}"
        )


if __name__ == "__main__":

    run_evaluation()