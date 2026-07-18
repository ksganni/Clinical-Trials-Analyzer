"""Fetch clinical trial studies from ClinicalTrials.gov API v2."""

from __future__ import annotations

import time
from typing import Any, Iterator

import requests

from etl.config import API_BASE_URL, MAX_STUDIES, PAGE_SIZE


class ClinicalTrialsAPIError(Exception):
    """Raised when the API returns an error."""


def fetch_studies_page(
    page_token: str | None = None,
    page_size: int = PAGE_SIZE,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Fetch one page of studies from the API."""
    client = session or requests.Session()
    params: dict[str, Any] = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token

    response = client.get(f"{API_BASE_URL}/studies", params=params, timeout=60)
    if response.status_code != 200:
        raise ClinicalTrialsAPIError(
            f"API error {response.status_code}: {response.text[:200]}"
        )
    return response.json()


def iter_studies(
    max_studies: int = MAX_STUDIES,
    page_size: int = PAGE_SIZE,
    pause_seconds: float = 0.2,
) -> Iterator[dict[str, Any]]:
    """
    Yield studies page by page.

    max_studies=0 means no limit (can take a very long time for 500k+ trials).
    """
    session = requests.Session()
    page_token: str | None = None
    fetched = 0

    while True:
        payload = fetch_studies_page(page_token, page_size, session)
        studies = payload.get("studies", [])
        if not studies:
            break

        for study in studies:
            yield study
            fetched += 1
            if max_studies > 0 and fetched >= max_studies:
                return

        page_token = payload.get("nextPageToken")
        if not page_token:
            break

        time.sleep(pause_seconds)
