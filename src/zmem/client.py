"""Subprocess client for the sole-writer Rust backend."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from zmem.utils.attention import AttentionPolicy
from zmem.utils.protocol import PROTOCOL_VERSION
from zmem.utils.runtime import RuntimeManifest, resolve_runtime_paths
from zmem.utils.trails import ObservedRef, TrailSummary


class ServiceError(RuntimeError):
    def __init__(self, message: str, *, category: str = "service", code: str = "service", retryable: bool = False,
                 job_id: str | None = None, retry_after_ms: int | None = None,
                 requested_oid: str | None = None, stage: str | None = None) -> None:
        super().__init__(message)
        self.category = category
        self.code = code
        self.retryable = retryable
        self.job_id = job_id
        self.retry_after_ms = retry_after_ms
        self.requested_oid = requested_oid
        self.stage = stage

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {"category": self.category, "error": str(self), "code": self.code,
                                      "retryable": self.retryable}
        for field in ("job_id", "retry_after_ms", "requested_oid", "stage"):
            if (value := getattr(self, field)) is not None:
                payload[field] = value
        return payload


def _raise_native_error(stderr: str, fallback: str) -> None:
    try:
        payload = json.loads(stderr.strip())
    except json.JSONDecodeError as exc:
        if "unrecognized subcommand" in stderr or "unexpected argument" in stderr:
            raise ServiceError("service does not support this request; run `zmem service upgrade`",
                               code="protocol") from exc
        raise ServiceError(f"service returned invalid error JSON: {stderr.strip() or fallback}", code="protocol") from exc
    if (not isinstance(payload, dict) or not isinstance(payload.get("code"), str)
            or not payload["code"] or not isinstance(payload.get("message"), str)
            or type(payload.get("retryable")) is not bool):
        raise ServiceError("service returned invalid error JSON", code="protocol")
    for key in ("job_id", "requested_oid", "stage"):
        if key in payload and not isinstance(payload[key], str):
            raise ServiceError("service returned invalid error JSON", code="protocol")
    if "retry_after_ms" in payload and (type(payload["retry_after_ms"]) is not int or payload["retry_after_ms"] < 0):
        raise ServiceError("service returned invalid error JSON", code="protocol")
    raise ServiceError(payload["message"], category="stale_ref" if payload["code"] == "stale_ref" else "service",
                       code=payload["code"], retryable=payload["retryable"],
                       job_id=payload.get("job_id"), retry_after_ms=payload.get("retry_after_ms"),
                       requested_oid=payload.get("requested_oid"), stage=payload.get("stage"))


def remaining_ms(deadline: float) -> int:
    remaining = int((deadline - time.monotonic()) * 1000)
    if remaining <= 0:
        raise ServiceError("service request deadline expired", code="timeout", retryable=True)
    return remaining


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
    observed: ObservedRef | None = None,
    deadline: float | None = None,
) -> dict:
    deadline = deadline if deadline is not None else time.monotonic() + 2
    executable = _service_binary()
    command = [executable, "query", str(repo)]
    if include_invalid:
        command.append("--include-invalid")
    if observed is not None:
        if observed.selector is not None:
            command.extend(("--ref", observed.selector))
        command.extend(("--observed-oid", observed.oid))
    _append_attention(command, attention)
    command.extend(("--timeout-ms", str(remaining_ms(deadline))))
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False,
                                   timeout=remaining_ms(deadline) / 1000)
    except subprocess.TimeoutExpired as exc:
        raise ServiceError("service request deadline expired", code="timeout", retryable=True) from exc
    except OSError as exc:
        raise ServiceError(f"service unavailable: {exc}") from exc
    if completed.returncode:
        _raise_native_error(completed.stderr, "service request failed")
    try:
        payload = json.loads(completed.stdout)
        if not isinstance(payload, dict) or not isinstance(payload.get("summary"), dict):
            raise TypeError("service query response must contain a summary object")
        trail = TrailSummary.from_mapping(payload["summary"].get("trail", {}))
        payload["summary"]["trail"] = trail.to_mapping()
        return payload
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ServiceError("service returned invalid JSON") from exc


def check(
    repo: Path,
    *,
    message: str | None,
    reference: str | None,
    deep: bool,
    attention: AttentionPolicy | None = None,
    deadline: float | None = None,
) -> dict:
    deadline = deadline if deadline is not None else time.monotonic() + 120
    if (message is None) == (reference is None):
        raise ValueError("exactly one proposed message or commit reference is required")
    executable = _service_binary()
    command = [executable, "check", str(repo)]
    if deep:
        command.append("--deep")
    if reference is not None:
        command.extend(("--ref", reference))
    _append_attention(command, attention)
    command.extend(("--timeout-ms", str(remaining_ms(deadline))))
    try:
        completed = subprocess.run(
            command,
            input=message,
            capture_output=True,
            text=True,
            check=False,
            timeout=remaining_ms(deadline) / 1000,
        )
    except subprocess.TimeoutExpired as exc:
        raise ServiceError("service check deadline expired", code="timeout", retryable=True) from exc
    except OSError as exc:
        raise ServiceError(f"service unavailable: {exc}") from exc
    if completed.returncode:
        _raise_native_error(completed.stderr, "service check failed")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ServiceError("service returned invalid check JSON") from exc
