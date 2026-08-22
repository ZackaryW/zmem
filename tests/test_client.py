import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from zmem.client import ServiceError, query
from zmem.utils.trails import ObservedRef


def _payload() -> dict:
    return {
        "summary": {
            "trail": {
                "requested_selector": "feature",
                "resolved_oid": "a" * 40,
                "trail_id": "trail-1",
                "attention_identity": "attention-1",
                "selected_commits": 1,
                "selected_nodes": 1,
                "extension_identity": "extension-1",
                "protocol_version": 4,
                "schema_version": 4,
            }
        },
        "entries": [],
        "relationships": [],
        "diagnostics": [],
    }


def test_query_keeps_selector_and_observed_oid_in_native_argv(monkeypatch) -> None:
    captured: list[str] = []

    def run(command, **_kwargs):
        captured.extend(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps(_payload()), stderr="")

    monkeypatch.setattr("zmem.client._service_binary", lambda: "zmem-svc")
    monkeypatch.setattr("zmem.client.subprocess.run", run)

    result = query(Path("repo"), observed=ObservedRef("feature", "a" * 40))

    assert captured[:3] == ["zmem-svc", "query", "repo"]
    assert captured[captured.index("--ref") + 1] == "feature"
    assert captured[captured.index("--observed-oid") + 1] == "a" * 40
    assert result["summary"]["trail"]["trail_id"] == "trail-1"


def test_query_rejects_an_untyped_trail_summary(monkeypatch) -> None:
    payload = _payload()
    payload["summary"]["trail"]["selected_commits"] = "1"
    monkeypatch.setattr("zmem.client._service_binary", lambda: "zmem-svc")
    monkeypatch.setattr(
        "zmem.client.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
    )

    with pytest.raises(ServiceError, match="invalid JSON"):
        query(Path("repo"))


def test_query_classifies_native_stale_ref_failure(monkeypatch) -> None:
    monkeypatch.setattr("zmem.client._service_binary", lambda: "zmem-svc")
    monkeypatch.setattr(
        "zmem.client.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Error: stale ref: observed old, resolved new",
        ),
    )

    with pytest.raises(ServiceError) as caught:
        query(Path("repo"))
    assert caught.value.category == "stale_ref"
