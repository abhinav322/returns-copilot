import json

from collections import defaultdict

from pathlib import Path

from backend.intent_classifier import (
    classify_intent,
)


EVAL_FILE = (
    Path(__file__).parent
    / "intent_cases.json"
)


def load_cases() -> list[dict]:

    with open(
        EVAL_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def run_evaluation():

    cases = load_cases()

    correct = 0

    per_class_total = defaultdict(int)

    per_class_correct = defaultdict(int)

    mistakes = []


    print()
    print(
        "INTENT CLASSIFIER EVALUATION"
    )

    print(
        "========================================"
    )


    for case in cases:

        expected = case[
            "expected"
        ]

        predicted = classify_intent(
            case["question"]
        )


        per_class_total[
            expected
        ] += 1


        is_correct = (
            predicted
            == expected
        )


        if is_correct:

            correct += 1

            per_class_correct[
                expected
            ] += 1

            marker = "✅"

        else:

            marker = "❌"

            mistakes.append(
                {
                    "id":
                        case["id"],

                    "question":
                        case["question"],

                    "expected":
                        expected,

                    "predicted":
                        predicted,
                }
            )


        print()

        print(
            f"{marker} {case['id']}"
        )

        print(
            f"Question: "
            f"{case['question']}"
        )

        print(
            f"Expected: {expected}"
        )

        print(
            f"Predicted: {predicted}"
        )


    total = len(
        cases
    )

    accuracy = (
        correct
        / total
    )


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
        f"Cases: {total}"
    )

    print(
        f"Correct: {correct}"
    )

    print(
        f"Accuracy: "
        f"{accuracy:.2%}"
    )


    print()

    print(
        "PER-CLASS ACCURACY"
    )

    print(
        "----------------------------------------"
    )


    for intent in [
        "RETURN",
        "WISMO",
        "UNKNOWN",
    ]:

        class_total = (
            per_class_total[
                intent
            ]
        )

        class_correct = (
            per_class_correct[
                intent
            ]
        )


        if class_total == 0:

            class_accuracy = 0.0

        else:

            class_accuracy = (
                class_correct
                / class_total
            )


        print(
            f"{intent}: "
            f"{class_correct}/"
            f"{class_total} "
            f"({class_accuracy:.2%})"
        )


    print()

    print(
        "========================================"
    )

    print(
        "MISTAKES"
    )

    print(
        "========================================"
    )


    if not mistakes:

        print(
            "No classification mistakes. ✅"
        )

    else:

        for mistake in mistakes:

            print()

            print(
                f"{mistake['id']}"
            )

            print(
                f"  Question: "
                f"{mistake['question']}"
            )

            print(
                f"  Expected: "
                f"{mistake['expected']}"
            )

            print(
                f"  Predicted: "
                f"{mistake['predicted']}"
            )


if __name__ == "__main__":

    run_evaluation()