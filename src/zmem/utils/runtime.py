"""Stable runtime paths, typed metadata, and transactional activation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import venv
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from zmem.utils.protocol import PROTOCOL_VERSION

MANIFEST_VERSION = 1
SCHEMA_VERSION = 2
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _binary_name() -> str:
    return "zmem-svc.exe" if os.name == "nt" else "zmem-svc"


def _host_python(host: Path) -> Path:
    return host / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


@dataclass(frozen=True)
class RuntimePaths:
    home: Path
    root: Path
    binary_dir: Path
    binary: Path
    host_dir: Path
    host_python: Path
    manifest: Path
    staging_root: Path
    previous: Path

    @classmethod
    def for_root(cls, home: Path, root: Path) -> RuntimePaths:
        home = home.resolve()
        root = root.resolve()
        binary_dir = root / "binary"
        host_dir = root / "host"
        return cls(
            home=home,
            root=root,
            binary_dir=binary_dir,
            binary=binary_dir / _binary_name(),
            host_dir=host_dir,
            host_python=_host_python(host_dir),
            manifest=root / "runtime.json",
            staging_root=root / ".staging",
            previous=root / ".previous",
        )


def resolve_runtime_paths(
    home: Path | None = None,
    runtime_root: Path | None = None,
    *,
    environ: Mapping[str, str] = os.environ,
) -> RuntimePaths:
    selected_home = home or (Path(environ["ZMEM_HOME"]) if environ.get("ZMEM_HOME") else Path.home() / ".zmem")
    selected_root = runtime_root or (
        Path(environ["ZMEM_RUNTIME_ROOT"]) if environ.get("ZMEM_RUNTIME_ROOT") else selected_home / "runtime"
    )
    return RuntimePaths.for_root(selected_home, selected_root)


def find_service_binary(
    explicit: Path | None,
    *,
    environ: Mapping[str, str] = os.environ,
    package_root: Path,
    which: Callable[[str], str | None] = shutil.which,
) -> Path | None:
    if explicit is not None:
        if explicit.is_file():
            return explicit.resolve()
        raise FileNotFoundError(f"explicit native service binary does not exist: {explicit}")
    if configured := environ.get("ZMEM_SVC_SOURCE"):
        candidate = Path(configured)
        if candidate.is_file():
            return candidate.resolve()
        raise FileNotFoundError(f"ZMEM_SVC_SOURCE does not name a file: {candidate}")
    candidates = [package_root / "_native" / _binary_name()]
    found = which("zmem-svc")
    candidates.append(Path(found) if found else None)
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate.resolve()
    return None


def discover_service_binary(
    explicit: Path | None,
    *,
    environ: Mapping[str, str] = os.environ,
    package_root: Path,
    which: Callable[[str], str | None] = shutil.which,
) -> Path:
    found = find_service_binary(explicit, environ=environ, package_root=package_root, which=which)
    if found is not None:
        return found
    raise FileNotFoundError(
        "no native zmem service binary found; use --binary, ZMEM_SVC_SOURCE, a platform wheel, or PATH"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class RuntimeManifest:
    manifest_version: int
    release_version: str
    binary_version: str
    host_version: str
    protocol_version: int
    schema_version: int
    sha256: str
    installation_id: str
    binary: Path
    host: Path
    installed_at: str

    @classmethod
    def from_mapping(cls, value: object) -> RuntimeManifest:
        if not isinstance(value, Mapping):
            raise TypeError("runtime manifest must be an object")
        expected = set(cls.__dataclass_fields__)
        actual = set(value)
        missing = expected - actual
        unknown = actual - expected
        if missing:
            raise ValueError(f"runtime manifest missing fields: {', '.join(sorted(missing))}")
        if unknown:
            raise ValueError(f"runtime manifest has unknown fields: {', '.join(sorted(unknown))}")
        integers = ("manifest_version", "protocol_version", "schema_version")
        for name in integers:
            if type(value[name]) is not int:
                raise ValueError(f"{name} must be an integer")
        strings = (
            "release_version",
            "binary_version",
            "host_version",
            "sha256",
            "installation_id",
            "binary",
            "host",
            "installed_at",
        )
        for name in strings:
            if not isinstance(value[name], str) or not value[name]:
                raise ValueError(f"{name} must be a non-empty string")
        if value["manifest_version"] != MANIFEST_VERSION:
            raise ValueError("unsupported runtime manifest version")
        if not SHA256_PATTERN.fullmatch(value["sha256"]):
            raise ValueError("sha256 must contain 64 lowercase hexadecimal characters")
        binary = Path(value["binary"])
        host = Path(value["host"])
        if not binary.is_absolute() or not host.is_absolute():
            raise ValueError("runtime binary and host paths must be absolute")
        try:
            datetime.fromisoformat(value["installed_at"])
        except ValueError as exc:
            raise ValueError("installed_at must be an ISO-8601 timestamp") from exc
        return cls(**{**value, "binary": binary, "host": host})  # type: ignore[arg-type]

    @classmethod
    def read(cls, path: Path) -> RuntimeManifest:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid runtime manifest: {exc}") from exc
        return cls.from_mapping(value)

    def to_mapping(self) -> dict[str, Any]:
        value = asdict(self)
        value["binary"] = str(self.binary)
        value["host"] = str(self.host)
        return value

    def write_atomic(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)

    @property
    def compatible(self) -> bool:
        return self.protocol_version == PROTOCOL_VERSION and self.schema_version == SCHEMA_VERSION


@dataclass(frozen=True)
class StagedRuntime:
    root: Path
    manifest: RuntimeManifest


@dataclass(frozen=True)
class ServiceIdentity:
    release_version: str
    binary_version: str
    protocol_version: int
    schema_version: int


def assemble_host(target: Path, package_root: Path) -> Path:
    venv.EnvBuilder(with_pip=False, clear=True).create(target)
    python = _host_python(target)
    completed = subprocess.run(
        [python, "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        capture_output=True,
        text=True,
        check=True,
    )
    site_packages = Path(completed.stdout.strip())
    destination = site_packages / "zmem"
    shutil.copytree(package_root, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "_native"))
    return python


def stage_runtime(
    paths: RuntimePaths,
    binary: Path,
    package_root: Path,
    identity: ServiceIdentity,
) -> StagedRuntime:
    installation_id = uuid.uuid4().hex
    staged_root = paths.staging_root / installation_id
    staged_paths = RuntimePaths.for_root(paths.home, staged_root)
    staged_paths.binary_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(binary, staged_paths.binary)
    staged_paths.binary.chmod(staged_paths.binary.stat().st_mode | 0o111)
    assemble_host(staged_paths.host_dir, package_root)
    manifest = RuntimeManifest(
        manifest_version=MANIFEST_VERSION,
        release_version=identity.release_version,
        binary_version=identity.binary_version,
        host_version=identity.release_version,
        protocol_version=identity.protocol_version,
        schema_version=identity.schema_version,
        sha256=sha256_file(staged_paths.binary),
        installation_id=installation_id,
        binary=paths.binary,
        host=paths.host_python,
        installed_at=datetime.now(UTC).isoformat(),
    )
    manifest.write_atomic(staged_paths.manifest)
    return StagedRuntime(staged_root, manifest)


def _remove_runtime_item(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def activate_runtime(
    paths: RuntimePaths,
    staged: StagedRuntime,
    healthcheck: Callable[[RuntimeManifest], bool],
) -> RuntimeManifest:
    active_items = (paths.binary_dir, paths.host_dir, paths.manifest)
    staged_items = (staged.root / "binary", staged.root / "host", staged.root / "runtime.json")
    _remove_runtime_item(paths.previous)
    paths.previous.mkdir(parents=True, exist_ok=True)
    had_active = False
    for active in active_items:
        if active.exists():
            had_active = True
            active.replace(paths.previous / active.name)
    try:
        for source, active in zip(staged_items, active_items, strict=True):
            if not source.exists():
                raise RuntimeError(f"staged runtime is incomplete: {source.name}")
            source.replace(active)
        if not healthcheck(staged.manifest):
            raise RuntimeError("replacement runtime failed its health check")
    except Exception:
        for active in active_items:
            _remove_runtime_item(active)
        if had_active:
            for old in tuple(paths.previous.iterdir()):
                old.replace(paths.root / old.name)
        _remove_runtime_item(paths.previous)
        raise
    _remove_runtime_item(paths.previous)
    _remove_runtime_item(staged.root)
    return staged.manifest


def current_package_root() -> Path:
    return Path(__file__).parents[1]


def current_python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
