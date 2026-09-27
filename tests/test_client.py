import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from zmem.cli import run as run_cli
from zmem.client import ServiceError, check, query
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
                "protocol_version": 5,
                "schema_version": 6,
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
            stderr=json.dumps({"code": "stale_ref", "message": "stale ref: observed old, resolved new", "retryable": False}),
        ),
    )

    with pytest.raises(ServiceError) as caught:
        query(Path("repo"))
    assert caught.value.category == "stale_ref"


@pytest.mark.parametrize("code,retryable", [("not_ready", True), ("busy", True),
                                             ("timeout", True), ("failed", False)])
def test_query_preserves_typed_native_failures(monkeypatch, code, retryable) -> None:
    monkeypatch.setattr("zmem.client._service_binary", lambda: "zmem-svc")
    failure = {"code": code, "message": "indexing status", "retryable": retryable,
               "job_id": "job-1", "retry_after_ms": 100, "requested_oid": "a" * 40,
               "stage": "indexing"}
    monkeypatch.setattr("zmem.client.subprocess.run", lambda *_args, **_kwargs:
                        SimpleNamespace(returncode=1, stdout="", stderr=json.dumps(failure)))

    with pytest.raises(ServiceError) as caught:
        query(Path("repo"))
    assert caught.value.to_mapping() == {"category": "service", "error": "indexing status",
                                         **{key: value for key, value in failure.items() if key != "message"}}


@pytest.mark.parametrize("stderr", ["plain error", "{}", '{"code":"timeout","message":"late","retryable":"yes"}'])
def test_query_rejects_malformed_native_failures(monkeypatch, stderr) -> None:
    monkeypatch.setattr("zmem.client._service_binary", lambda: "zmem-svc")
    monkeypatch.setattr("zmem.client.subprocess.run", lambda *_args, **_kwargs:
                        SimpleNamespace(returncode=1, stdout="", stderr=stderr))
    with pytest.raises(ServiceError) as caught:
        query(Path("repo"))
    assert caught.value.code == "protocol"


def test_cli_emits_typed_pending_error_with_service_exit(monkeypatch, capsys) -> None:
    monkeypatch.setattr("zmem.cli._repo_root", lambda path, **_kwargs: Path("repo"))
    monkeypatch.setattr("zmem.cli.observe_ref", lambda *_args, **_kwargs: ObservedRef(None, "a" * 40))

    def pending(*_args, **_kwargs):
        raise ServiceError("indexing", code="not_ready", retryable=True,
                           job_id="job-1", retry_after_ms=100, requested_oid="a" * 40)

    monkeypatch.setattr("zmem.cli.service_query", pending)
    assert run_cli(["recall"]) == 4
    assert json.loads(capsys.readouterr().out) == {
        "command": "recall", "category": "service", "error": "indexing", "code": "not_ready",
        "retryable": True, "job_id": "job-1", "retry_after_ms": 100, "requested_oid": "a" * 40,
    }


@pytest.mark.parametrize("value", ["0", "-1", "oops", "1.5"])
def test_cli_rejects_bad_timeout_before_git(monkeypatch, value) -> None:
    monkeypatch.setattr("zmem.cli._repo_root", lambda *_args, **_kwargs:
                        pytest.fail("Git must not run for invalid timeout"))
    with pytest.raises(SystemExit) as caught:
        run_cli(["--timeout-ms", value, "recall"])
    assert caught.value.code == 2


def test_cli_passes_one_decreasing_budget_to_ref_and_native(monkeypatch, capsys) -> None:
    observed: dict[str, float] = {}
    monkeypatch.setattr("zmem.cli._repo_root", lambda _path, *, deadline: Path("repo"))

    def observe(_repo, _selector, *, timeout):
        observed["git_timeout"] = timeout
        time.sleep(0.03)
        return ObservedRef(None, "a" * 40)

    def pending(*_args, **kwargs):
        observed["native_remaining"] = kwargs["deadline"] - time.monotonic()
        raise ServiceError("indexing", code="not_ready", retryable=True)

    monkeypatch.setattr("zmem.cli.observe_ref", observe)
    monkeypatch.setattr("zmem.cli.service_query", pending)
    assert run_cli(["--timeout-ms", "100", "recall"]) == 4
    assert json.loads(capsys.readouterr().out)["code"] == "not_ready"
    assert 0 < observed["native_remaining"] < observed["git_timeout"] <= 0.101, observed


def test_cli_classifies_git_observation_timeout_as_service_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr("zmem.cli._repo_root", lambda _path, *, deadline: Path("repo"))

    def observe(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["git"], 0.001)

    monkeypatch.setattr("zmem.cli.observe_ref", observe)
    assert run_cli(["--timeout-ms", "1", "recall"]) == 4
    assert json.loads(capsys.readouterr().out)["code"] == "timeout"


@pytest.mark.parametrize("command", ["query", "check"])
def test_real_stalled_native_child_is_bounded(monkeypatch, tmp_path, command) -> None:
    (tmp_path / command).write_text(
        "import os, pathlib, time\n"
        "pathlib.Path('child.pid').write_text(str(os.getpid()))\n"
        "time.sleep(5)\n"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("zmem.client._service_binary", lambda: sys.executable)
    deadline = time.monotonic() + 0.4
    started = time.monotonic()
    with pytest.raises(ServiceError) as caught:
        if command == "query":
            query(Path("repo"), deadline=deadline)
        else:
            check(Path("repo"), message="feat: test", reference=None, deep=True, deadline=deadline)
    assert caught.value.code == "timeout"
    assert time.monotonic() - started < 1.4
    pid = int((tmp_path / "child.pid").read_text())
    if os.name == "nt":
        import ctypes

        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(0x1000, False, pid)
        if handle:
            code = ctypes.c_ulong()
            try:
                assert kernel.GetExitCodeProcess(handle, ctypes.byref(code))
                assert code.value != 259
            finally:
                kernel.CloseHandle(handle)
    else:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
