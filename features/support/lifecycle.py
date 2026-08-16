from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def before_scenario(context, _scenario) -> None:
    context.temp_root = Path(tempfile.mkdtemp(prefix="zmem-behave-"))
    context.repo = context.temp_root / "repo"
    context.home = context.temp_root / "home"
    context.home.mkdir()
    context.env = os.environ.copy()
    context.env["ZMEM_HOME"] = str(context.home)
    context.runtime_root = context.temp_root / "runtime"
    context.env["ZMEM_RUNTIME_ROOT"] = str(context.runtime_root)
    context.env["ZMEM_SVC"] = str(
        (Path(__file__).parents[3] / "zmem-cache" / "target" / "debug" / "zmem-svc.exe").resolve()
    )
    context.env["ZMEM_EXTENSION_HOST"] = str(
        (Path(__file__).parents[2] / ".venv" / "Scripts" / "zmem-extension-host.exe").resolve()
    )
    context.zmem_executable = Path(__file__).parents[2] / ".venv" / "Scripts" / "zmem.exe"


def after_scenario(context, _scenario) -> None:
    if service := context.env.get("ZMEM_SVC"):
        subprocess.run(
            [service, "stop"],
            env=context.env,
            capture_output=True,
            timeout=5,
            check=False,
        )
    if server := getattr(context, "release_server", None):
        server.shutdown()
        server.server_close()
        context.release_thread.join(timeout=5)
    shutil.rmtree(context.temp_root, ignore_errors=True)


def init_repo(context) -> None:
    context.repo.mkdir(exist_ok=True)
    subprocess.run(["git", "init", "-q", context.repo], check=True)
    subprocess.run(["git", "-C", context.repo, "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", context.repo, "config", "user.email", "test@example.com"], check=True)


def commit(context, subject: str, body: str = "", content: str | None = None) -> str:
    path = context.repo / "memory.txt"
    path.write_text(content or subject)
    subprocess.run(["git", "-C", context.repo, "add", "memory.txt"], check=True)
    command = ["git", "-C", context.repo, "commit", "-q", "-m", subject]
    if body:
        command += ["-m", body]
    subprocess.run(command, check=True)
    return subprocess.run(
        ["git", "-C", context.repo, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def run_zmem(context, *args: str, input_text: str | None = None) -> None:
    command = [str(context.zmem_executable), "--repo", str(context.repo), *args]
    context.completed = subprocess.run(
        command,
        cwd=Path(__file__).parents[2],
        env=context.env,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )


def run_zmem_service(context, *args: str) -> None:
    context.completed = subprocess.run(
        [str(context.zmem_executable), "service", *args],
        cwd=Path(__file__).parents[2],
        env=context.env,
        capture_output=True,
        text=True,
        check=False,
    )
