"""Public service-runtime management composed from standard-library utilities."""

from __future__ import annotations

import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from zmem.utils.protocol import PROTOCOL_VERSION
from zmem.utils.registration import registration_plan
from zmem.utils.release import acquire_release_binary
from zmem.utils.runtime import (
    SCHEMA_VERSION,
    RuntimeManifest,
    RuntimePaths,
    ServiceIdentity,
    activate_runtime,
    current_package_root,
    find_service_binary,
    resolve_runtime_paths,
    sha256_file,
    stage_runtime,
)


class ServiceManagementError(RuntimeError):
    pass


def _package_version() -> str:
    try:
        return importlib.metadata.version("zmem")
    except importlib.metadata.PackageNotFoundError:
        return "0.1.0"


def _environment(paths: RuntimePaths) -> dict[str, str]:
    environment = os.environ.copy()
    environment["ZMEM_HOME"] = str(paths.home)
    environment["ZMEM_RUNTIME_ROOT"] = str(paths.root)
    environment.pop("ZMEM_EXTENSION_HOST", None)
    return environment


def _run_binary(
    binary: Path,
    *arguments: str,
    paths: RuntimePaths,
    timeout: float = 30,
) -> tuple[subprocess.CompletedProcess[str], object | None]:
    try:
        completed = subprocess.run(
            [binary, *arguments],
            env=_environment(paths),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ServiceManagementError(f"could not run managed service: {exc}") from exc
    payload: object | None = None
    if completed.stdout.strip():
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            pass
    return completed, payload


def _binary_identity(binary: Path, paths: RuntimePaths) -> ServiceIdentity:
    completed, payload = _run_binary(binary, "version-json", paths=paths, timeout=10)
    if completed.returncode or not isinstance(payload, Mapping):
        detail = completed.stderr.strip() or "native service returned invalid version metadata"
        raise ServiceManagementError(f"invalid native service artifact: {detail}")
    expected = {"release_version", "protocol_version", "schema_version"}
    if set(payload) != expected:
        raise ServiceManagementError("invalid native service artifact: unexpected version metadata")
    release = payload["release_version"]
    protocol = payload["protocol_version"]
    schema = payload["schema_version"]
    if not isinstance(release, str) or not release or type(protocol) is not int or type(schema) is not int:
        raise ServiceManagementError("invalid native service artifact: ill-typed version metadata")
    return ServiceIdentity(_package_version(), release, protocol, schema)


def _load_manifest(paths: RuntimePaths) -> RuntimeManifest:
    if not paths.manifest.is_file():
        raise ServiceManagementError("managed runtime is not installed; run `zmem service install`")
    try:
        return RuntimeManifest.read(paths.manifest)
    except (TypeError, ValueError) as exc:
        raise ServiceManagementError(f"managed runtime metadata is invalid: {exc}; run `zmem service doctor`") from exc


def _stop_binary(binary: Path, paths: RuntimePaths) -> None:
    try:
        _run_binary(binary, "stop", paths=paths, timeout=10)
    except ServiceManagementError:
        return
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            _completed, payload = _run_binary(binary, "status", paths=paths, timeout=5)
        except ServiceManagementError:
            return
        if isinstance(payload, Mapping) and payload.get("running") is False:
            return
        time.sleep(0.025)


def _healthcheck(paths: RuntimePaths, manifest: RuntimeManifest) -> bool:
    completed, _payload = _run_binary(manifest.binary, "ensure", paths=paths, timeout=15)
    if completed.returncode:
        return False
    completed, payload = _run_binary(manifest.binary, "status", paths=paths, timeout=10)
    return bool(
        completed.returncode == 0
        and isinstance(payload, Mapping)
        and payload.get("running") is True
        and payload.get("protocol_version") == manifest.protocol_version
        and payload.get("schema_version") == manifest.schema_version
    )


def status(paths: RuntimePaths) -> dict[str, Any]:
    if not paths.manifest.is_file():
        return {
            "command": "service status",
            "runtime_installed": False,
            "running": False,
            "healthy": False,
            "compatible": False,
            "home": str(paths.home),
            "runtime_root": str(paths.root),
        }
    manifest = _load_manifest(paths)
    artifact_ok = (
        manifest.binary == paths.binary
        and manifest.host == paths.host_python
        and manifest.binary.is_file()
        and manifest.host.is_file()
        and sha256_file(manifest.binary) == manifest.sha256
    )
    service_payload: Mapping[str, Any] = {}
    if manifest.binary.is_file():
        try:
            completed, payload = _run_binary(manifest.binary, "status", paths=paths, timeout=10)
            if completed.returncode == 0 and isinstance(payload, Mapping):
                service_payload = payload
        except ServiceManagementError:
            pass
    running = service_payload.get("running") is True
    compatible = bool(
        manifest.compatible
        and (not running or service_payload.get("protocol_version") == PROTOCOL_VERSION)
        and (not running or service_payload.get("schema_version") == SCHEMA_VERSION)
    )
    return {
        "command": "service status",
        "runtime_installed": True,
        "running": running,
        "healthy": artifact_ok and running and compatible,
        "compatible": compatible,
        "home": str(paths.home),
        "runtime_root": str(paths.root),
        **manifest.to_mapping(),
    }


def install_or_upgrade(
    paths: RuntimePaths,
    *,
    binary: Path | None,
    register: bool,
    upgrade: bool,
) -> dict[str, Any]:
    existing = paths.manifest.is_file()
    if upgrade and not existing:
        raise ServiceManagementError("cannot upgrade an absent runtime; run `zmem service install`")
    try:
        source = find_service_binary(binary, package_root=current_package_root())
    except FileNotFoundError as exc:
        raise ServiceManagementError(str(exc)) from exc
    if source is not None:
        return _replace_runtime(paths, source=source, register=register, upgrade=upgrade, existing=existing)
    try:
        with acquire_release_binary(
            _package_version(),
            paths.staging_root,
            expected_protocol=PROTOCOL_VERSION,
            expected_schema=SCHEMA_VERSION,
        ) as downloaded:
            return _replace_runtime(paths, source=downloaded, register=register, upgrade=upgrade, existing=existing)
    except ValueError as exc:
        raise ServiceManagementError(str(exc)) from exc


def _replace_runtime(
    paths: RuntimePaths,
    *,
    source: Path,
    register: bool,
    upgrade: bool,
    existing: bool,
) -> dict[str, Any]:
    identity = _binary_identity(source, paths)
    if identity.protocol_version != PROTOCOL_VERSION or identity.schema_version != SCHEMA_VERSION:
        raise ServiceManagementError("native service is incompatible with this zmem release")
    staged = stage_runtime(paths, source, current_package_root(), identity)
    old_manifest = _load_manifest(paths) if existing else None
    if old_manifest is not None and old_manifest.binary.is_file():
        _stop_binary(old_manifest.binary, paths)
    elif not existing:
        _stop_binary(source, paths)
    try:
        manifest = activate_runtime(paths, staged, lambda candidate: _healthcheck(paths, candidate))
    except Exception as exc:
        if paths.manifest.is_file():
            restored = _load_manifest(paths)
            if restored.binary.is_file():
                _healthcheck(paths, restored)
        raise ServiceManagementError(f"runtime replacement failed and was rolled back: {exc}") from exc
    if register:
        try:
            plan = registration_plan(sys.platform, paths, manifest)
            if upgrade:
                plan.remove()
            plan.install()
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise ServiceManagementError(
                f"runtime installed but per-user startup registration failed: {exc}; use `zmem service doctor`"
            ) from exc
    result = status(paths)
    result["command"] = "service upgrade" if upgrade else "service install"
    result["registered"] = register
    return result


def start(paths: RuntimePaths) -> dict[str, Any]:
    manifest = _load_manifest(paths)
    if not manifest.compatible:
        raise ServiceManagementError("managed runtime is incompatible; run `zmem service upgrade`")
    completed, _payload = _run_binary(manifest.binary, "ensure", paths=paths, timeout=15)
    if completed.returncode:
        raise ServiceManagementError(completed.stderr.strip() or "managed service failed to start")
    result = status(paths)
    result["command"] = "service start"
    return result


def stop(paths: RuntimePaths) -> dict[str, Any]:
    manifest = _load_manifest(paths)
    _stop_binary(manifest.binary, paths)
    result = status(paths)
    result["command"] = "service stop"
    return result


def doctor(paths: RuntimePaths) -> dict[str, Any]:
    diagnostics: list[str] = []
    try:
        result = status(paths)
    except ServiceManagementError as exc:
        result = {"runtime_installed": paths.manifest.exists(), "running": False, "compatible": False}
        diagnostics.append(str(exc))
    if paths.staging_root.exists() and any(paths.staging_root.iterdir()):
        diagnostics.append("incomplete staged runtime exists")
    if paths.previous.exists():
        diagnostics.append("previous runtime remains after an interrupted replacement")
    if result.get("runtime_installed") and not result.get("compatible"):
        diagnostics.append("managed runtime is incompatible; run `zmem service upgrade`")
    if result.get("runtime_installed") and not result.get("healthy"):
        diagnostics.append("managed runtime is not healthy; run `zmem service start` or reinstall")
    return {"command": "service doctor", **result, "diagnostics": diagnostics, "ok": not diagnostics}


def uninstall(paths: RuntimePaths, *, unregister: bool, remove_data: bool) -> dict[str, Any]:
    manifest = _load_manifest(paths)
    _stop_binary(manifest.binary, paths)
    if unregister:
        try:
            registration_plan(sys.platform, paths, manifest).remove()
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise ServiceManagementError(f"could not remove per-user startup registration: {exc}") from exc
    if paths.root.exists():
        shutil.rmtree(paths.root)
    if remove_data and paths.home.exists():
        resolved = paths.home.resolve()
        if resolved == Path(resolved.anchor):
            raise ServiceManagementError("refusing to remove a filesystem root")
        shutil.rmtree(resolved)
    return {
        "command": "service uninstall",
        "runtime_installed": False,
        "running": False,
        "data_removed": remove_data,
        "home": str(paths.home),
        "runtime_root": str(paths.root),
    }


def dispatch(action: str, *, home: Path | None, runtime_root: Path | None, **options: Any) -> dict[str, Any]:
    paths = resolve_runtime_paths(home, runtime_root)
    if action == "status":
        return status(paths)
    if action == "install":
        return install_or_upgrade(
            paths, binary=options.get("binary"), register=not options["no_register"], upgrade=False
        )
    if action == "upgrade":
        return install_or_upgrade(
            paths, binary=options.get("binary"), register=not options["no_register"], upgrade=True
        )
    if action == "start":
        return start(paths)
    if action == "stop":
        return stop(paths)
    if action == "doctor":
        return doctor(paths)
    if action == "uninstall":
        return uninstall(paths, unregister=not options["no_register"], remove_data=options["remove_data"])
    raise ServiceManagementError(f"unknown service action: {action}")
