"""Native per-user startup registration plans."""

from __future__ import annotations

import html
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from zmem.utils.runtime import RuntimeManifest, RuntimePaths

Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class RegistrationPlan:
    artifact_path: Path | None
    artifact_content: str
    install_commands: tuple[tuple[str, ...], ...]
    remove_commands: tuple[tuple[str, ...], ...]

    def install(self, runner: Runner = subprocess.run) -> None:
        if self.artifact_path is not None:
            self.artifact_path.parent.mkdir(parents=True, exist_ok=True)
            self.artifact_path.write_text(self.artifact_content, encoding="utf-8")
        for command in self.install_commands:
            runner(command, capture_output=True, text=True, check=True)

    def remove(self, runner: Runner = subprocess.run) -> None:
        commands = iter(self.remove_commands)
        if first := next(commands, None):
            runner(first, capture_output=True, text=True, check=False)
        if self.artifact_path is not None:
            self.artifact_path.unlink(missing_ok=True)
        for command in commands:
            runner(command, capture_output=True, text=True, check=False)


def registration_plan(
    platform: str,
    paths: RuntimePaths,
    manifest: RuntimeManifest,
    *,
    user_home: Path | None = None,
    user_id: int | None = None,
) -> RegistrationPlan:
    user_home = (user_home or Path.home()).resolve()
    executable = str(manifest.binary)
    if platform == "win32":
        task = "zmem-svc"
        launch = f'"{executable}" serve'
        return RegistrationPlan(
            None,
            "",
            (("schtasks.exe", "/Create", "/F", "/SC", "ONLOGON", "/TN", task, "/TR", launch),),
            (("schtasks.exe", "/Delete", "/F", "/TN", task),),
        )
    if platform == "darwin":
        uid = user_id if user_id is not None else os.getuid()
        artifact = user_home / "Library" / "LaunchAgents" / "dev.zmem.service.plist"
        escaped = html.escape(executable)
        content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0"><dict><key>Label</key><string>dev.zmem.service</string>'
            f"<key>ProgramArguments</key><array><string>{escaped}</string><string>serve</string></array>"
            "<key>RunAtLoad</key><true/></dict></plist>\n"
        )
        return RegistrationPlan(
            artifact,
            content,
            (("launchctl", "bootstrap", f"gui/{uid}", str(artifact)),),
            (("launchctl", "bootout", f"gui/{uid}/dev.zmem.service"),),
        )
    if platform.startswith("linux"):
        artifact = user_home / ".config" / "systemd" / "user" / "zmem-svc.service"
        content = (
            "[Unit]\nDescription=zmem Git-history cache service\n\n"
            f'[Service]\nExecStart="{executable}" serve\nRestart=on-failure\n\n'
            "[Install]\nWantedBy=default.target\n"
        )
        return RegistrationPlan(
            artifact,
            content,
            (
                ("systemctl", "--user", "daemon-reload"),
                ("systemctl", "--user", "enable", "--now", "zmem-svc.service"),
            ),
            (
                ("systemctl", "--user", "disable", "--now", "zmem-svc.service"),
                ("systemctl", "--user", "daemon-reload"),
            ),
        )
    raise ValueError(f"unsupported platform for service registration: {platform}")
