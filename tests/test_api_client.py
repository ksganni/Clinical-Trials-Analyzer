from unittest.mock import MagicMock, patch

import pytest

from etl.api_client import ClinicalTrialsAPIError, fetch_studies_page, iter_studies


def test_fetch_studies_page_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"studies": [{"id": 1}], "nextPageToken": "abc"}

    session = MagicMock()
    session.get.return_value = mock_response

    result = fetch_studies_page(session=session)
    assert result["studies"] == [{"id": 1}]
    session.get.assert_called_once()


def test_fetch_studies_page_error():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server error"

    session = MagicMock()
    session.get.return_value = mock_response

    with pytest.raises(ClinicalTrialsAPIError):
        fetch_studies_page(session=session)


@patch("etl.api_client.fetch_studies_page")
def test_iter_studies_respects_max(mock_fetch):
    mock_fetch.side_effect = [
        {"studies": [{"n": 1}, {"n": 2}], "nextPageToken": "t1"},
        {"studies": [{"n": 3}], "nextPageToken": None},
    ]

    results = list(iter_studies(max_studies=2, page_size=2, pause_seconds=0))
    assert len(results) == 2
    assert results[0]["n"] == 1
