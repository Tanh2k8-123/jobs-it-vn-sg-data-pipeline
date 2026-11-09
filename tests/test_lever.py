import pytest
import responses

from sea_it_jobs.lever import ExtractionError, LeverClient

URL = "https://api.lever.co/v0/postings/testboard"


@responses.activate
def test_pagination_follows_actual_length_until_empty():
    for page in [[{"id": "one"}], [{"id": "two"}], []]:
        responses.get(URL, json=page)
    client = LeverClient(page_size=100)
    result = client.fetch("testboard")
    assert [p["id"] for p in result.postings] == ["one", "two"]
    assert result.page_count == 3
    assert [call.request.params["skip"] for call in responses.calls] == ["0", "1", "2"]


@responses.activate
def test_duplicate_across_pages_is_incomplete():
    responses.get(URL, json=[{"id": "one"}])
    responses.get(URL, json=[{"id": "one"}])
    with pytest.raises(ExtractionError, match="Duplicate") as error:
        LeverClient().fetch("testboard")
    assert len(error.value.partial) == 1


@responses.activate
def test_transient_status_is_retried():
    responses.get(URL, status=503)
    responses.get(URL, json=[])
    assert LeverClient().fetch("testboard").postings == []
    assert len(responses.calls) == 2


@pytest.mark.parametrize(
    "payload", [{"error": "oops"}, [None], [{}], [{"id": "a", "categories": []}]]
)
@responses.activate
def test_invalid_payload_is_not_an_empty_success(payload):
    responses.get(URL, json=payload)
    with pytest.raises(ExtractionError):
        LeverClient().fetch("testboard")


@responses.activate
def test_missing_board_fails_without_retry():
    responses.get(URL, status=404)
    with pytest.raises(ExtractionError):
        LeverClient().fetch("testboard")
    assert len(responses.calls) == 1


@responses.activate
def test_invalid_json_fails():
    responses.get(URL, body="not json", content_type="text/plain")
    with pytest.raises(ExtractionError):
        LeverClient().fetch("testboard")


@responses.activate
def test_max_pages_fails_instead_of_silently_truncating():
    responses.get(URL, json=[{"id": "one"}])
    with pytest.raises(ExtractionError, match="max_pages"):
        LeverClient(max_pages=1).fetch("testboard")
