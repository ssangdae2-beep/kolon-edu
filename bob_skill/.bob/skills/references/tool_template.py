"""
Watsonx Orchestrate ADK tool template.

Copy this file into your project as `tools/<your_tool_name>.py`. The function name
(snake_case) must match the filename stem AND the string you list under `tools:` in
your agent YAML. This three-way match is the single most important convention in
the skill — it eliminates pitfall #1 (tools list / function name drift).
"""

from typing import Generic, Optional, TypeVar

import requests
from ibm_watsonx_orchestrate.agent_builder.connections import (
    ConnectionType,
    ExpectedCredentials,
)
from ibm_watsonx_orchestrate.agent_builder.tools import tool
from pydantic import BaseModel, computed_field
from pydantic.dataclasses import dataclass


# ---------------------------------------------------------------------------
# Inlined ToolResponse / ErrorDetails.
#
# In the wxo-domains repo these live in agent_ready_tools/tools/tool_response.py
# and agent_ready_tools/clients/error_handling.py. They're inlined here so the
# starter project has zero shared-utils dependency. Keep the shapes identical to
# the upstream repo so tools you ship to production work unchanged.
# ---------------------------------------------------------------------------

T = TypeVar("T")


@dataclass
class ErrorDetails:
    """Unified wrapper for tool error information."""

    status_code: Optional[int]
    url: Optional[str]
    reason: Optional[str]
    details: Optional[str]
    recommendation: Optional[str]


class ToolResponse(BaseModel, Generic[T]):
    """Unified wrapper for all tool responses."""

    error_details: Optional[ErrorDetails]
    tool_output: Optional[T]

    @computed_field  # type: ignore[misc]
    @property
    def is_success(self) -> bool:
        return self.error_details is None


# ---------------------------------------------------------------------------
# Connection declaration.
#
# `app_id` matches the `--app-id` you'll pass to `orchestrate connections add`
# and the YAML in your connections/ directory. Pick the ConnectionType that
# matches how the external API authenticates.
# ---------------------------------------------------------------------------

MY_APP_CONNECTIONS = [
    ExpectedCredentials(
        app_id="my_app",
        type=ConnectionType.KEY_VALUE,  # or BASIC_AUTH, BEARER_TOKEN, API_KEY_AUTH, OAUTH2_AUTH_CODE
    ),
]


@dataclass
class Response:
    """Whatever your tool returns. Use a Pydantic dataclass — the model
    becomes part of the schema the agent's LLM sees."""

    summary: str
    raw: Optional[dict] = None


@tool(expected_credentials=MY_APP_CONNECTIONS)
def my_tool_function_name(query: str, limit: int = 10) -> ToolResponse[Response]:
    """
    One-line summary of what this tool does. The agent's LLM reads this docstring to
    decide when to call the tool, so be specific about the task it solves.

    Args:
        query: Plain-English search string from the user.
        limit: Maximum number of results to return. Defaults to 10.

    Returns:
        A ToolResponse wrapping a Response on success, or ErrorDetails on failure.
    """
    # In production you'd resolve credentials via the ADK; for hackathons calling
    # `requests` directly with a token loaded from the connection or `.env` is fine.
    try:
        api_response = requests.get(
            "https://api.example.com/search",
            params={"q": query, "limit": limit},
            timeout=10,
        )
        api_response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        # NEVER raise from a @tool — always wrap the error in ToolResponse so the
        # agent's "Error Handling" instructions can surface a useful message.
        return ToolResponse(
            tool_output=None,
            error_details=ErrorDetails(
                status_code=getattr(exc.response, "status_code", None),
                url="https://api.example.com/search",
                reason=str(exc),
                details=getattr(exc.response, "text", None),
                recommendation="Check the query, your network, and your API token.",
            ),
        )

    payload = api_response.json()
    return ToolResponse(
        error_details=None,
        tool_output=Response(
            summary=f"Found {len(payload.get('items', []))} results", raw=payload
        ),
    )
