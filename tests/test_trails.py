import subprocess

import pytest

from zmem.utils.trails import NativeQueryRequest, ObservedRef, TrailSummary, observe_ref


def _git(path, *args):
    return subprocess.run(["git", "-C", path, *args], check=True, capture_output=True, text=True).stdout.strip()


def test_observe_ref_resolves_unoccupied_branch_without_checkout(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "config", "user.email", "test@example.com")
    (tmp_path / "file").write_text("base")
    _git(tmp_path, "add", "file")
    _git(tmp_path, "commit", "-q", "-m", "base")
    _git(tmp_path, "branch", "feature")
    current = _git(tmp_path, "branch", "--show-current")
    observed = observe_ref(tmp_path, "feature")
    assert observed.selector == "feature"
    assert observed.oid == _git(tmp_path, "rev-parse", "feature^{commit}")
    assert _git(tmp_path, "branch", "--show-current") == current


def test_trail_summary_strictly_decodes_typed_identity():
    payload = {
        "requested_selector": "feature",
        "resolved_oid": "a" * 40,
        "trail_id": "trail-1",
        "attention_identity": "attention-1",
        "selected_commits": 3,
        "selected_nodes": 2,
        "extension_identity": "ext-1",
        "protocol_version": 4,
        "schema_version": 4,
    }
    assert TrailSummary.from_mapping(payload).to_mapping() == payload
    with pytest.raises((TypeError, ValueError)):
        TrailSummary.from_mapping(payload | {"selected_commits": "3"})


def test_native_request_keeps_selector_and_observed_oid_together(tmp_path):
    request = NativeQueryRequest(str(tmp_path)).with_ref(ObservedRef("feature", "a" * 40))
    assert request.to_mapping() == {
        "repository": str(tmp_path),
        "selector": "feature",
        "observed_oid": "a" * 40,
    }
