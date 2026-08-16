"""Subprocess client for the sole-writer Rust backend."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from zmem.utils.attention import AttentionPolicy
from zmem.utils.protocol import PROTOCOL_VERSION
from zmem.utils.runtime import RuntimeManifest, resolve_runtime_paths


class ServiceError(RuntimeError):
    pass


def _service_binary() -> str:
    if explicit := os.getenv("ZMEM_SVC"):
        return explicit
    paths = resolve_runtime_paths()
    if paths.manifest.is_file():
        try:
            manifest = RuntimeManifest.read(paths.manifest)
        except (TypeError, ValueError) as exc:
            raise ServiceError(f"managed runtime metadata is invalid; run `zmem service doctor`: {exc}") from exc
        if manifest.protocol_version != PROTOCOL_VERSION:
            raise ServiceError("managed runtime is incompatible; run `zmem service upgrade`")
        if not manifest.binary.is_file():
            raise ServiceError("managed service binary is missing; run `zmem service doctor`")
        return str(manifest.binary)
    return "zmem-svc"


def _append_attention(command: list[str], attention: AttentionPolicy | None) -> None:
    policy = attention or AttentionPolicy(commit_limit=500, node_limit=400)
    command.extend(("--commit-limit", str(policy.commit_limit), "--node-limit", str(policy.node_limit)))


def query(
    repo: Path,
    *,
    include_invalid: bool = True,
    attention: AttentionPolicy | None = None,
) -> dict:
    executable = _service_binary()
    command = [executable, "query", str(repo)]
    if include_invalid:
        command.append("--include-invalid")
    _append_attention(command, attention)
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise ServiceError(f"service unavailable: {exc}") from exc
    if completed.returncode:
        raise ServiceError(completed.stderr.strip() or "service request failed")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ServiceError("service returned invalid JSON") from exc


def check(
    repo: Path,
    *,
    message: str | None,
    reference: str | None,
    deep: bool,
    attention: AttentionPolicy | None = None,
) -> dict:
    if (message is None) == (reference is None):
        raise ValueError("exactly one proposed message or commit reference is required")
    executable = _service_binary()
    command = [executable, "check", str(repo)]
    if deep:
        command.append("--deep")
    if reference is not None:
        command.extend(("--ref", reference))
    _append_attention(command, attention)
    try:
        completed = subprocess.run(
            command,
            input=message,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ServiceError(f"service unavailable: {exc}") from exc
    if completed.returncode:
        detail = completed.stderr.strip() or "service check failed"
        if "unrecognized subcommand" in detail or "unexpected argument" in detail:
            detail = "service does not support commit checking; run `zmem service upgrade`"
        raise ServiceError(detail)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ServiceError("service returned invalid check JSON") from exc
