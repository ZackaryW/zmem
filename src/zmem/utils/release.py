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
DEFAULT_RELEASE_INVENTORY = "https://api.github.com/repos/ZackaryW/zmem-cache/releases?per_page=100"
MAX_RELEASE_MANIFEST_BYTES = 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
ASSET_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
STABLE_RELEASE_PATTERN = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
COMPATIBILITY_CANDIDATE_ERRORS = (OSError, URLError, json.JSONDecodeError, TypeError, ValueError)


def stable_release_version(tag: object) -> tuple[int, int, int] | None:
    if not isinstance(tag, str):
        return None
    match = STABLE_RELEASE_PATTERN.fullmatch(tag)
    return tuple(map(int, match.groups())) if match else None


def iter_release_inventory(
    opener: Callable[..., Any], url: str = DEFAULT_RELEASE_INVENTORY
) -> Iterator[Mapping[str, object]]:
    next_url: str | None = url
    while next_url is not None:
        try:
            with opener(next_url, timeout=30) as response:
                value = json.loads(_read_bounded(response, MAX_RELEASE_MANIFEST_BYTES))
                link = getattr(response, "headers", {}).get("Link")
        except (OSError, URLError, json.JSONDecodeError) as exc:
            raise ValueError(f"could not enumerate zmem service releases: {exc}") from exc
        if not isinstance(value, list):
            raise TypeError("zmem service release inventory must be an array")
        for release in value:
            if not isinstance(release, Mapping):
                raise TypeError("zmem service release inventory item must be an object")
            yield release
        next_url = None
        if isinstance(link, str):
            for part in link.split(","):
                match = re.fullmatch(r'\s*<([^>]+)>;\s*rel="([^"]+)"\s*', part)
                if match and match.group(2) == "next":
                    next_url = match.group(1)
                    break


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


@dataclass(frozen=True)
class SelectedRelease:
    version: str
    manifest: ReleaseManifest
    asset: ReleaseAsset
    release_url: str


@dataclass(frozen=True)
class AcquiredBinary:
    path: Path
    version: str


def select_compatible_release(
    releases: Iterator[Mapping[str, object]] | list[Mapping[str, object]],
    *,
    target: str,
    protocol: int,
    schema: int,
    opener: Callable[..., Any] = urlopen,
    release_root: str = DEFAULT_RELEASE_ROOT,
) -> SelectedRelease:
    candidates: list[tuple[tuple[int, int, int], str]] = []
    for release in releases:
        tag = release.get("tag_name")
        version = stable_release_version(tag)
        if version is None or release.get("draft") is not False or release.get("prerelease") is not False:
            continue
        candidates.append((version, str(tag)))
    for numeric, tag in sorted(candidates, reverse=True):
        version = ".".join(map(str, numeric))
        release_url = f"{release_root.rstrip('/')}/{tag}"
        try:
            with opener(f"{release_url}/release-manifest.json", timeout=30) as response:
                value = json.loads(_read_bounded(response, MAX_RELEASE_MANIFEST_BYTES))
            manifest = ReleaseManifest.from_mapping(value, expected_release=version)
            if manifest.protocol_version != protocol or manifest.schema_version != schema:
                continue
            asset = manifest.asset_for(target)
        except COMPATIBILITY_CANDIDATE_ERRORS:
            continue
        return SelectedRelease(version, manifest, asset, release_url)
    raise ValueError("no compatible zmem service release is available for this platform")


@contextmanager
def acquire_compatible_release_binary(
    staging_root: Path,
    *,
    expected_protocol: int,
    expected_schema: int,
    releases: Iterator[Mapping[str, object]],
    environ: Mapping[str, str] = os.environ,
    system: str | None = None,
    machine: str | None = None,
    opener: Callable[..., Any] = urlopen,
) -> Iterator[AcquiredBinary]:
    target = platform_target(system or sys.platform, machine or platform.machine())
    root = environ.get("ZMEM_SVC_RELEASE_ROOT", DEFAULT_RELEASE_ROOT).rstrip("/")
    selected = select_compatible_release(
        releases,
        target=target,
        protocol=expected_protocol,
        schema=expected_schema,
        opener=opener,
        release_root=root,
    )
    staging_root.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="download-", dir=staging_root) as temporary:
            destination = Path(temporary) / selected.asset.name
            with opener(f"{selected.release_url}/{selected.asset.name}", timeout=60) as response:
                copy_verified(response, destination, selected.asset)
            destination.chmod(destination.stat().st_mode | 0o111)
            yield AcquiredBinary(destination, selected.version)
    except (OSError, URLError, TypeError, ValueError) as exc:
        raise ValueError(f"could not acquire compatible zmem service release: {exc}") from exc


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
