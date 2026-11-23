
from mcp_server import search_policy


def test_uk_return_window_retrieval():
    result = search_policy(
        query="standard return window",
        region="UK"
    )

    assert result["found"] is True

    # The correct policy must appear in the results
    matching_chunks = [
        chunk
        for chunk in result["results"]
        if chunk["id"] == "uk_returns_1"
    ]

    assert len(matching_chunks) == 1

    # Verify the retrieved passage contains the rule
    assert "30 days" in matching_chunks[0]["text"]

    # Ensure retrieval remains limited to three passages
    assert len(result["results"]) <= 3
