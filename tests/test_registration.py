from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
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
        ("win32", "schtasks.exe", "start-service.pyw"),
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
    if platform == "win32":
        assert plan.artifact_path == paths.root / artifact_suffix
        assert str(manifest.host.with_name("pythonw.exe")) in plan.install_commands[0][-1]
    else:
        assert plan.artifact_path == user_home / Path(artifact_suffix)
        assert str(paths.binary) in plan.artifact_content


def test_registration_rejects_unknown_platform(tmp_path: Path) -> None:
    paths, manifest = _manifest(tmp_path)
    with pytest.raises(ValueError, match="unsupported platform"):
        registration_plan("plan9", paths, manifest, user_home=tmp_path, user_id=1)


def test_windows_registration_requires_windowless_host_before_replacing_task(tmp_path: Path) -> None:
    paths, manifest = _manifest(tmp_path)
    plan = registration_plan("win32", paths, manifest)
    commands = []
    with pytest.raises(FileNotFoundError, match="startup launcher is missing"):
        plan.install(lambda *args, **kwargs: commands.append(args))
    assert not commands
    assert plan.artifact_path and not plan.artifact_path.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="real Windows console visibility")
def test_windowless_launcher_hides_service_and_descendants_and_preserves_exit(tmp_path: Path) -> None:
    paths, manifest = _manifest(tmp_path / "launch space's \u03a9")
    manifest = replace(manifest, binary=Path(sys.executable), host=Path(sys.executable))
    plan = registration_plan("win32", paths, manifest)
    paths.home.mkdir(parents=True)
    output = paths.home / "probe.json"
    probe = (
        "import ctypes,json,os,subprocess,sys\n"
        "from pathlib import Path\n"
        "def visible():\n"
        "    kernel=ctypes.WinDLL('kernel32',use_last_error=True)\n"
        "    kernel.GetConsoleWindow.restype=ctypes.c_void_p\n"
        "    user=ctypes.WinDLL('user32',use_last_error=True)\n"
        "    user.IsWindowVisible.argtypes=[ctypes.c_void_p]\n"
        "    return bool(user.IsWindowVisible(kernel.GetConsoleWindow()))\n"
        "child='import ctypes; k=ctypes.windll.kernel32; k.GetConsoleWindow.restype=ctypes.c_void_p; "
        "u=ctypes.windll.user32; u.IsWindowVisible.argtypes=[ctypes.c_void_p]; "
        "print(bool(u.IsWindowVisible(k.GetConsoleWindow())))'\n"
        "result=subprocess.run([sys.executable,'-c',child],capture_output=True,text=True,check=True)\n"
        f"Path({str(output)!r}).write_text(json.dumps(dict(visible=visible(),child=result.stdout.strip(),"
        "home=os.environ['ZMEM_HOME'],root=os.environ['ZMEM_RUNTIME_ROOT'],"
        "override=os.environ.get('ZMEM_EXTENSION_HOST'))))\n"
        "sys.exit(7)\n"
    )
    (paths.home / "serve").write_text(probe, encoding="utf-8")
    commands = []
    plan.install(lambda command, **kwargs: commands.append(command))
    assert plan.artifact_path and plan.artifact_path.exists()
    environment = os.environ.copy()
    environment["ZMEM_EXTENSION_HOST"] = "unrelated override"
    # Execute exactly the task action, without a command shell.
    completed = subprocess.run(commands[0][-1], env=environment, timeout=15, check=False)
    assert completed.returncode == 7
    observed = json.loads(output.read_text())
    assert observed == {"visible": False, "child": "False", "home": str(paths.home),
                        "root": str(paths.root), "override": None}
    plan.remove(lambda command, **kwargs: commands.append(command))
    assert commands[-1] == ("schtasks.exe", "/Delete", "/F", "/TN", "zmem-svc")
    assert not plan.artifact_path.exists()


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
