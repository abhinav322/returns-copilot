from backend.workflow.order_return_graph import (
    claims_order_is_final_sale,
    claims_order_is_not_final_sale,
)


def test_detects_direct_final_sale_claim():

    answer = (
        "This item is marked as final sale."
    )

    assert (
        claims_order_is_final_sale(
            answer
        )
        is True
    )


def test_detects_pronoun_final_sale_claim():

    answer = (
        "It is marked as final sale."
    )

    assert (
        claims_order_is_final_sale(
            answer
        )
        is True
    )


def test_does_not_treat_negative_claim_as_positive():

    answer = (
        "This item is not a final sale item."
    )

    assert (
        claims_order_is_final_sale(
            answer
        )
        is False
    )

    assert (
        claims_order_is_not_final_sale(
            answer
        )
        is True
    )


def test_does_not_treat_whether_it_is_as_final_sale_claim():

    answer = (
        "The return is not eligible regardless "
        "of the item's condition or whether "
        "it is marked as final sale."
    )

    assert (
        claims_order_is_final_sale(
            answer
        )
        is False
    )


def test_does_not_treat_whether_item_is_as_final_sale_claim():

    answer = (
        "The decision does not depend on "
        "whether the item is marked as "
        "final sale."
    )

    assert (
        claims_order_is_final_sale(
            answer
        )
        is False
    )