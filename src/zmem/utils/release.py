"""Strict acquisition of versioned native service release artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import sys
import tempfile
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO
from urllib.error import URLError
from urllib.request import urlopen

RELEASE_MANIFEST_VERSION = 1
DEFAULT_RELEASE_ROOT = "https://github.com/ZackaryW/zmem-cache/releases/download"
MAX_RELEASE_MANIFEST_BYTES = 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
ASSET_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def platform_target(system: str, machine: str) -> str:
    normalized_system = system.lower()
    normalized_machine = machine.lower()
    systems = {
        "win32": "windows",
        "windows": "windows",
        "darwin": "macos",
        "linux": "linux",
    }
    machines = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "aarch64",
        "aarch64": "aarch64",
        "x86": "i686",
        "i386": "i686",
        "i686": "i686",
    }
    operating_system = systems.get(normalized_system)
    architecture = machines.get(normalized_machine)
    targets = {
        ("windows", "x86_64"): "x86_64-pc-windows-msvc",
        ("windows", "aarch64"): "aarch64-pc-windows-msvc",
        ("windows", "i686"): "i686-pc-windows-msvc",
        ("macos", "x86_64"): "x86_64-apple-darwin",
        ("macos", "aarch64"): "aarch64-apple-darwin",
        ("linux", "x86_64"): "x86_64-unknown-linux-musl",
        ("linux", "aarch64"): "aarch64-unknown-linux-musl",
    }
    target = targets.get((operating_system, architecture))
    if target is None:
        raise ValueError(f"unsupported service release platform: {system}/{machine}")
    return target


@dataclass(frozen=True)
class ReleaseAsset:
    target: str
    name: str
    size: int
    sha256: str

    @classmethod
    def from_mapping(cls, value: object) -> ReleaseAsset:
        if not isinstance(value, Mapping):
            raise TypeError("release asset must be an object")
        expected = set(cls.__dataclass_fields__)
        missing = expected - set(value)
        unknown = set(value) - expected
        if missing:
            raise ValueError(f"release asset missing fields: {', '.join(sorted(missing))}")
        if unknown:
            raise ValueError(f"release asset has unknown fields: {', '.join(sorted(unknown))}")
        target = value["target"]
        name = value["name"]
        size = value["size"]
        sha256 = value["sha256"]
        if not isinstance(target, str) or not target:
            raise ValueError("release asset target must be a non-empty string")
        if (
            not isinstance(name, str)
            or not ASSET_NAME_PATTERN.fullmatch(name)
            or Path(name).name != name
            or name in {".", ".."}
        ):
            raise ValueError("release asset name must be a safe single path component")
        if type(size) is not int or size <= 0:
            raise ValueError("release asset size must be a positive integer")
        if not isinstance(sha256, str) or not SHA256_PATTERN.fullmatch(sha256):
            raise ValueError("release asset sha256 must contain 64 lowercase hexadecimal characters")
        return cls(target, name, size, sha256)


@dataclass(frozen=True)
class ReleaseManifest:
    manifest_version: int
    release_version: str
    protocol_version: int
    schema_version: int
    assets: tuple[ReleaseAsset, ...]

    @classmethod
    def from_mapping(cls, value: object, *, expected_release: str) -> ReleaseManifest:
        if not isinstance(value, Mapping):
            raise TypeError("release manifest must be an object")
        expected = set(cls.__dataclass_fields__)
        missing = expected - set(value)
        unknown = set(value) - expected
        if missing:
            raise ValueError(f"release manifest missing fields: {', '.join(sorted(missing))}")
        if unknown:
            raise ValueError(f"release manifest has unknown fields: {', '.join(sorted(unknown))}")
        for field in ("manifest_version", "protocol_version", "schema_version"):
            if type(value[field]) is not int:
                raise ValueError(f"release manifest {field} must be an integer")
        if value["manifest_version"] != RELEASE_MANIFEST_VERSION:
            raise ValueError("unsupported release manifest version")
        release_version = value["release_version"]
        if not isinstance(release_version, str) or not release_version:
            raise ValueError("release manifest release_version must be a non-empty string")
        if release_version != expected_release:
            raise ValueError(f"release manifest does not describe expected release {expected_release}")
        raw_assets = value["assets"]
        if not isinstance(raw_assets, list) or not raw_assets:
            raise ValueError("release manifest assets must be a non-empty array")
        assets = tuple(ReleaseAsset.from_mapping(asset) for asset in raw_assets)
        targets = [asset.target for asset in assets]
        if len(targets) != len(set(targets)):
            raise ValueError("release manifest contains duplicate targets")
        return cls(
            manifest_version=value["manifest_version"],
            release_version=release_version,
            protocol_version=value["protocol_version"],
            schema_version=value["schema_version"],
            assets=assets,
        )

    def asset_for(self, target: str) -> ReleaseAsset:
        for asset in self.assets:
            if asset.target == target:
                return asset
        raise ValueError(f"release {self.release_version} does not support target {target}")


def copy_verified(source: BinaryIO, destination: Path, asset: ReleaseAsset) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    try:
        with destination.open("wb") as output:
            while block := source.read(1024 * 1024):
                total += len(block)
                if total > asset.size:
                    raise ValueError(f"release artifact size exceeds advertised size {asset.size}")
                digest.update(block)
                output.write(block)
        if total != asset.size:
            raise ValueError(f"release artifact size {total} does not match advertised size {asset.size}")
        if digest.hexdigest() != asset.sha256:
            raise ValueError("release artifact SHA-256 does not match the manifest")
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def _read_bounded(source: BinaryIO, limit: int) -> bytes:
    value = source.read(limit + 1)
    if len(value) > limit:
        raise ValueError(f"release manifest exceeds {limit} bytes")
    return value


@contextmanager
def acquire_release_binary(
    release_version: str,
    staging_root: Path,
    *,
    environ: Mapping[str, str] = os.environ,
    system: str | None = None,
    machine: str | None = None,
    expected_protocol: int | None = None,
    expected_schema: int | None = None,
    opener: Callable[..., Any] = urlopen,
) -> Iterator[Path]:
    target = platform_target(system or sys.platform, machine or platform.machine())
    root = environ.get("ZMEM_SVC_RELEASE_ROOT", DEFAULT_RELEASE_ROOT).rstrip("/")
    release_url = f"{root}/v{release_version}"
    manifest_url = f"{release_url}/release-manifest.json"
    try:
        with opener(manifest_url, timeout=30) as response:
            raw_manifest = _read_bounded(response, MAX_RELEASE_MANIFEST_BYTES)
        value = json.loads(raw_manifest)
        manifest = ReleaseManifest.from_mapping(value, expected_release=release_version)
        if expected_protocol is not None and manifest.protocol_version != expected_protocol:
            raise ValueError("release manifest protocol is incompatible with this zmem version")
        if expected_schema is not None and manifest.schema_version != expected_schema:
            raise ValueError("release manifest schema is incompatible with this zmem version")
        asset = manifest.asset_for(target)
        staging_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="download-", dir=staging_root) as temporary:
            destination = Path(temporary) / asset.name
            with opener(f"{release_url}/{asset.name}", timeout=60) as response:
                copy_verified(response, destination, asset)
            destination.chmod(destination.stat().st_mode | 0o111)
            yield destination
    except (OSError, URLError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(f"could not acquire zmem service release {release_version}: {exc}") from exc
