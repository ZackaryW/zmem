from __future__ import annotations

from pathlib import Path

import pytest

from zmem.utils.registration import registration_plan
from zmem.utils.runtime import RuntimeManifest, resolve_runtime_paths


def _manifest(tmp_path: Path) -> tuple:
    paths = resolve_runtime_paths(tmp_path / "home", tmp_path / "runtime", environ={})
    manifest = RuntimeManifest.from_mapping(
        {
            "manifest_version": 1,
            "release_version": "1.0.0",
            "binary_version": "1.0.0",
            "host_version": "1.0.0",
            "protocol_version": 2,
            "schema_version": 2,
            "sha256": "a" * 64,
            "installation_id": "test",
            "binary": str(paths.binary),
            "host": str(paths.host_python),
            "installed_at": "2026-08-15T00:00:00+00:00",
        }
    )
    return paths, manifest


@pytest.mark.parametrize(
    ("platform", "tool", "artifact_suffix"),
    [
        ("win32", "schtasks.exe", None),
        ("darwin", "launchctl", "Library/LaunchAgents/dev.zmem.service.plist"),
        ("linux", "systemctl", ".config/systemd/user/zmem-svc.service"),
    ],
)
def test_registration_plan_uses_native_user_surface(
    tmp_path: Path, platform: str, tool: str, artifact_suffix: str | None
) -> None:
    paths, manifest = _manifest(tmp_path)
    user_home = tmp_path / "user"
    plan = registration_plan(platform, paths, manifest, user_home=user_home, user_id=123)
    assert any(command[0] == tool for command in plan.install_commands)
    assert any(command[0] == tool for command in plan.remove_commands)
    if artifact_suffix is None:
        assert plan.artifact_path is None
    else:
        assert plan.artifact_path == user_home / Path(artifact_suffix)
        assert str(paths.binary) in plan.artifact_content


def test_registration_rejects_unknown_platform(tmp_path: Path) -> None:
    paths, manifest = _manifest(tmp_path)
    with pytest.raises(ValueError, match="unsupported platform"):
        registration_plan("plan9", paths, manifest, user_home=tmp_path, user_id=1)


def test_artifact_is_removed_before_native_reload(tmp_path: Path) -> None:
    paths, manifest = _manifest(tmp_path)
    plan = registration_plan("linux", paths, manifest, user_home=tmp_path / "user", user_id=1)
    observed: list[tuple[tuple[str, ...], bool]] = []

    def runner(command, **_kwargs):
        observed.append((tuple(command), bool(plan.artifact_path and plan.artifact_path.exists())))

    plan.install(runner)
    assert plan.artifact_path and plan.artifact_path.exists()
    plan.remove(runner)
    assert observed[-1][0] == ("systemctl", "--user", "daemon-reload")
    assert observed[-1][1] is False
