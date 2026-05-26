"""Gmail API client: authenticate and fetch transaction notification emails."""

from typing import Any


def get_service() -> Any:
    """Return an authenticated Gmail API service object."""
    raise NotImplementedError


def fetch_emails(service: Any, label: str, max_results: int = 100) -> list[dict[str, Any]]:
    """Return raw message dicts for emails under the given Gmail label."""
    raise NotImplementedError
