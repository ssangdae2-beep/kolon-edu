"""
Co-located test template for an ADK tool.

Save next to your tool as `tools/<your_tool>_test.py`. Run with `pytest tools/`.
The pattern: mock `requests` at the HTTP boundary, call the @tool function, and
assert on the ToolResponse shape (NOT on raw HTTP behavior).

Note: the @tool decorator wraps the return value. In the wxo-domains repo,
tests access the underlying ToolResponse via `.content.tool_output`. If your
@tool decorator version returns the bare ToolResponse directly, drop `.content`.
Try one, and switch if you get an AttributeError.
"""

from unittest.mock import MagicMock, patch

from my_tool import my_tool_function_name  # adjust import path for your project


def test_my_tool_happy_path() -> None:
    """Tool returns a populated ToolResponse on a 200 response."""
    with patch("my_tool.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"items": [{"id": 1}, {"id": 2}, {"id": 3}]},
        )
        mock_get.return_value.raise_for_status = MagicMock(return_value=None)

        result = my_tool_function_name(query="hello", limit=10)
        response = result.content if hasattr(result, "content") else result

        assert response.is_success is True
        assert response.error_details is None
        assert response.tool_output is not None
        assert "3 results" in response.tool_output.summary


def test_my_tool_error_path() -> None:
    """Tool returns an ErrorDetails-populated ToolResponse on HTTP failure."""
    import requests

    with patch("my_tool.requests.get") as mock_get:
        mock_response = MagicMock(status_code=500, text="boom")
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        result = my_tool_function_name(query="hello")
        response = result.content if hasattr(result, "content") else result

        assert response.is_success is False
        assert response.error_details is not None
        assert response.error_details.status_code == 500
        assert response.tool_output is None
