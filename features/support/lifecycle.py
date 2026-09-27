from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def before_scenario(context, _scenario) -> None:
    executable_suffix = ".exe" if os.name == "nt" else ""
    scripts_dir = Path(sys.executable).parent
    context.temp_root = Path(tempfile.mkdtemp(prefix="zmem-behave-"))
    context.repo = context.temp_root / "repo"
    context.home = context.temp_root / "home"
    context.home.mkdir()
    context.env = os.environ.copy()
    context.env["ZMEM_HOME"] = str(context.home)
    context.runtime_root = context.temp_root / "runtime"
    context.env["ZMEM_RUNTIME_ROOT"] = str(context.runtime_root)
    context.env.setdefault(
        "ZMEM_SVC",
        str((Path(__file__).parents[3] / "zmem-cache" / "target" / "debug" / f"zmem-svc{executable_suffix}").resolve()),
    )
    context.env["ZMEM_EXTENSION_HOST"] = str(scripts_dir / f"zmem-extension-host{executable_suffix}")
    context.zmem_executable = scripts_dir / f"zmem{executable_suffix}"


def after_scenario(context, _scenario) -> None:
    state_file = context.home / "service.json"
    try:
        pid = int(json.loads(state_file.read_text())["pid"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        pid = None
    service = context.env.get("REAL_ZMEM_SVC") or context.env.get("ZMEM_SVC")
    if service:
        subprocess.run(
            [service, "stop", "--timeout-ms", "10000"],
            env=context.env,
            capture_output=True,
            timeout=12,
            check=False,
        )
    if pid is not None:
        expected = {
            str(Path(service).resolve()).casefold() if service else "",
            str((context.runtime_root / "binary" / f"zmem-svc{'.exe' if os.name == 'nt' else ''}").resolve()).casefold(),
        }
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and _owned_service_alive(pid, expected):
            time.sleep(0.05)
        if _owned_service_alive(pid, expected):
            os.kill(pid, signal.SIGTERM)
    if server := getattr(context, "release_server", None):
        server.shutdown()
        server.server_close()
        context.release_thread.join(timeout=5)
    shutil.rmtree(context.temp_root, ignore_errors=True)


def _owned_service_alive(pid: int, expected: set[str]) -> bool:
    if os.name == "nt":
        import ctypes

        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        code = ctypes.c_ulong()
        image = ctypes.create_unicode_buffer(32768)
        image_length = ctypes.c_ulong(len(image))
        try:
            return (
                bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code)))
                and code.value == 259
                and bool(kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(image_length)))
                and image.value.casefold() in expected
            )
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    executable = Path(f"/proc/{pid}/exe")
    return not executable.exists() or str(executable.resolve()).casefold() in expected


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
    """Run one CLI request; test orchestration explicitly waits for admitted jobs."""
    command = [str(context.zmem_executable), "--repo", str(context.repo), *args]
    deadline = time.monotonic() + 20
    context.pending_failure = None
    while True:
        context.completed = subprocess.run(
            command,
            cwd=Path(__file__).parents[2],
            env=context.env,
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            failure = json.loads(context.completed.stdout) if context.completed.returncode else {}
        except json.JSONDecodeError:
            failure = {}
        if failure.get("code") != "not_ready":
            return
        context.pending_failure = failure
        job_id = failure["job_id"]
        while time.monotonic() < deadline:
            status = subprocess.run(
                [context.env["ZMEM_SVC"], "job-status", job_id, "--timeout-ms", "10000"],
                env=context.env,
                capture_output=True,
                text=True,
                check=False,
            )
            if status.returncode:
                raise AssertionError(f"index job status failed: {status.stderr}")
            state = json.loads(status.stdout)["state"]
            if state == "ready":
                break
            if state == "failed":
                context.completed = subprocess.run(
                    command,
                    cwd=Path(__file__).parents[2],
                    env=context.env,
                    input=input_text,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                return
            time.sleep(0.05)
        else:
            raise AssertionError(f"index job {job_id} did not become ready")


def run_zmem_service(context, *args: str) -> None:
    context.completed = subprocess.run(
        [str(context.zmem_executable), "service", *args],
        cwd=Path(__file__).parents[2],
        env=context.env,
        capture_output=True,
        text=True,
        check=False,
    )
