import json
import re

from pathlib import Path

from backend.rag.rag_pipeline import (
    answer_question,
)


EVAL_FILE = (
    Path(__file__).parent
    / "rag_answer_cases.json"
)


def load_cases() -> list[dict]:

    with open(
        EVAL_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def extract_citations(
    answer: str,
) -> set[int]:

    return {
        int(number)

        for number in re.findall(
            r"\[Source\s+(\d+)\]",
            answer,
            flags=re.IGNORECASE,
        )
    }


def run_evaluation():

    cases = load_cases()

    total_passed = 0

    positive_total = 0
    positive_passed = 0

    negative_total = 0
    negative_passed = 0

    failures = []


    print()
    print(
        "RAG ANSWER GROUNDING EVALUATION"
    )

    print(
        "========================================"
    )


    for case in cases:

        result = answer_question(
            question=case["question"],
            region=case["region"],
        )

        answer = result[
            "answer"
        ]

        sources = result[
            "sources"
        ]

        answer_lower = (
            answer.lower()
        )


        print()
        print(
            f"CASE: {case['id']}"
        )

        print(
            f"Question: "
            f"{case['question']}"
        )

        print(
            f"Answer: {answer}"
        )


        if case[
            "expected_abstain"
        ]:

            negative_total += 1

            no_sources = (
                len(sources) == 0
            )

            abstention_message = (
                "do not contain enough information"
                in answer_lower
            )

            passed = (
                no_sources
                and abstention_message
            )


            print(
                f"No sources: {no_sources}"
            )

            print(
                "Correct abstention message: "
                f"{abstention_message}"
            )


            if passed:

                negative_passed += 1

        else:

            positive_total += 1

            expected_source_found = any(
                source["source"]
                == case["expected_source"]

                and

                source["heading"]
                == case["expected_heading"]

                for source in sources
            )


            citations = extract_citations(
                answer
            )


            valid_source_numbers = {
                source["number"]
                for source in sources
            }


            has_citation = (
                len(citations) > 0
            )


            citation_integrity = (
                has_citation

                and

                citations.issubset(
                    valid_source_numbers
                )
            )


            required_term_found = any(
                term.lower()
                in answer_lower

                for term in case[
                    "required_terms"
                ]
            )


            passed = (
                expected_source_found
                and citation_integrity
                and required_term_found
            )


            print(
                "Expected source found: "
                f"{expected_source_found}"
            )

            print(
                f"Citations: "
                f"{sorted(citations)}"
            )

            print(
                "Citation integrity: "
                f"{citation_integrity}"
            )

            print(
                "Required content found: "
                f"{required_term_found}"
            )


            if positive_passed is not None:

                if passed:

                    positive_passed += 1


        if passed:

            total_passed += 1

            print(
                "RESULT: PASS ✅"
            )

        else:

            failures.append(
                case["id"]
            )

            print(
                "RESULT: FAIL ❌"
            )


    total_cases = len(
        cases
    )


    overall_accuracy = (
        total_passed
        / total_cases
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
        f"Cases: {total_cases}"
    )

    print(
        f"Passed: {total_passed}"
    )

    print(
        f"Overall pass rate: "
        f"{overall_accuracy:.2%}"
    )

    print(
        f"Grounded answer cases: "
        f"{positive_passed}/"
        f"{positive_total}"
    )

    print(
        f"Abstention cases: "
        f"{negative_passed}/"
        f"{negative_total}"
    )


    print()

    print(
        "FAILURES"
    )

    print(
        "----------------------------------------"
    )


    if failures:

        for failure in failures:

            print(
                failure
            )

    else:

        print(
            "No failures. ✅"
        )


if __name__ == "__main__":

    run_evaluation()