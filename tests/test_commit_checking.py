import json
import subprocess
from pathlib import Path

import pytest

from zmem.cli import run as run_cli
from zmem.client import ServiceError
from zmem.client import check as service_check
from zmem.host import expand_request
from zmem.utils.commit_messages import validate_policy


@pytest.mark.parametrize(
    ("message", "annotations", "options", "expected"),
    [
        ("ordinary subject", 0, {}, ()),
        ("", 0, {}, ("commit subject is empty",)),
        ("ordinary subject", 0, {"conventional": True}, ("subject is not a conventional commit",)),
        (
            "feat(core): subject",
            0,
            {"max_subject_length": 10},
            ("subject exceeds 10 characters",),
        ),
        (
            "feat: subject",
            0,
            {"require_annotation": True},
            ("message requires at least one zmem annotation",),
        ),
    ],
)
def test_policy_diagnostics_are_independent(message, annotations, options, expected):
    assert validate_policy(message, annotations, **options) == expected


def test_policy_combines_requested_failures():
    assert validate_policy(
        "not conventional and long",
        0,
        conventional=True,
        max_subject_length=5,
        require_annotation=True,
    ) == (
        "subject is not a conventional commit",
        "subject exceeds 5 characters",
        "message requires at least one zmem annotation",
    )


def test_preview_runs_expander_but_skips_hooks(tmp_path: Path):
    extension_root = tmp_path / "extensions"
    expander = extension_root / "expanders" / "custom.py"
    hook = extension_root / "hooks" / "observe.py"
    marker = tmp_path / "hook-ran"
    expander.parent.mkdir(parents=True)
    hook.parent.mkdir(parents=True)
    expander.write_text(
        "API_VERSION=1\n"
        "class Custom:\n"
        " extension_id='CUSTOM'\n"
        " def expand(self, context): context.add_entry(type='CUSTOM', content=context.annotation.content)\n"
        "def register(registry, mode='extend'): registry.extend('CUSTOM', Custom())\n"
    )
    hook.write_text(
        "from pathlib import Path\n"
        "API_VERSION=1\n"
        f"def observe(context): Path({str(marker)!r}).write_text('ran')\n"
        "def register(registry): registry.register('after_expand', observe)\n"
    )

    result = expand_request(
        {
            "repo": str(tmp_path),
            "global_extension_root": str(extension_root),
            "commit_sha": "0" * 40,
            "message": "feat: preview\n\nzmem(CUSTOM): projected",
            "run_hooks": False,
            "preview": True,
        }
    )

    assert result["annotation_count"] == 1
    assert result["journal"]["actions"][0]["content"] == "projected"
    assert not marker.exists()


def test_service_check_passes_proposed_message_on_stdin(monkeypatch, tmp_path: Path):
    observed = {}

    def completed(command, **options):
        observed.update(command=command, options=options)
        return subprocess.CompletedProcess(command, 0, '{"ok":true}', "")

    monkeypatch.setattr("zmem.client._service_binary", lambda: "zmem-svc")
    monkeypatch.setattr("zmem.client.subprocess.run", completed)

    assert service_check(tmp_path, message="feat: proposed", reference=None, deep=True) == {"ok": True}
    assert observed["command"][:8] == [
        "zmem-svc",
        "check",
        str(tmp_path),
        "--deep",
        "--commit-limit",
        "500",
        "--node-limit",
        "400",
    ]
    assert observed["command"][8] == "--timeout-ms"
    assert int(observed["command"][9]) > 0
    assert observed["options"]["input"] == "feat: proposed"


def test_unsupported_native_check_requests_upgrade(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("zmem.client._service_binary", lambda: "zmem-svc")
    monkeypatch.setattr(
        "zmem.client.subprocess.run",
        lambda command, **options: subprocess.CompletedProcess(
            command,
            2,
            "",
            "error: unrecognized subcommand 'check'",
        ),
    )

    with pytest.raises(ServiceError, match="service upgrade"):
        service_check(tmp_path, message="feat: proposed", reference=None, deep=False)


@pytest.mark.parametrize("code", ["timeout", "busy", "not_ready"])
def test_cli_check_service_delay_exits_four_without_validation_result(monkeypatch, tmp_path: Path, capsys, code):
    message = tmp_path / "message.txt"
    message.write_text("feat: proposed\n\nzmem(DECISION): valid")
    monkeypatch.setattr("zmem.cli._repo_root", lambda _path, *, deadline: tmp_path)

    def delayed(*_args, **_kwargs):
        raise ServiceError("native work delayed", code=code, retryable=True)

    monkeypatch.setattr("zmem.cli.service_check", delayed)
    assert run_cli(["check", "--file", str(message)]) == 4
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "command": "check",
        "category": "service",
        "error": "native work delayed",
        "code": code,
        "retryable": True,
    }
