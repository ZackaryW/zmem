from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from zmem.utils.release import ReleaseAsset, ReleaseManifest, copy_verified, platform_target
from zmem.utils.runtime import find_service_binary


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("win32", "AMD64", "x86_64-pc-windows-msvc"),
        ("win32", "ARM64", "aarch64-pc-windows-msvc"),
        ("win32", "i686", "i686-pc-windows-msvc"),
        ("darwin", "x86_64", "x86_64-apple-darwin"),
        ("darwin", "arm64", "aarch64-apple-darwin"),
        ("linux", "x86_64", "x86_64-unknown-linux-musl"),
        ("linux", "aarch64", "aarch64-unknown-linux-musl"),
    ],
)
def test_platform_target_alias_matrix(system: str, machine: str, expected: str) -> None:
    assert platform_target(system, machine) == expected


def test_unsupported_platform_is_actionable() -> None:
    with pytest.raises(ValueError, match="plan9.*mips"):
        platform_target("plan9", "mips")


def _manifest(asset: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "manifest_version": 1,
        "release_version": "1.0.0",
        "protocol_version": 2,
        "schema_version": 2,
        "assets": [
            asset
            or {
                "target": "x86_64-pc-windows-msvc",
                "name": "zmem-svc-x86_64-pc-windows-msvc.exe",
                "size": 4,
                "sha256": hashlib.sha256(b"zmem").hexdigest(),
            }
        ],
    }


def test_release_manifest_is_strict_typed_and_version_matched() -> None:
    manifest = ReleaseManifest.from_mapping(_manifest(), expected_release="1.0.0")
    assert manifest.asset_for("x86_64-pc-windows-msvc").size == 4

    with pytest.raises(ValueError, match="unknown"):
        ReleaseManifest.from_mapping(_manifest() | {"unknown": True}, expected_release="1.0.0")
    with pytest.raises(ValueError, match="expected release"):
        ReleaseManifest.from_mapping(_manifest(), expected_release="0.2.0")
    with pytest.raises(ValueError, match="duplicate"):
        value = _manifest()
        value["assets"] = [value["assets"][0], value["assets"][0]]  # type: ignore[index]
        ReleaseManifest.from_mapping(value, expected_release="1.0.0")


@pytest.mark.parametrize("name", ["../zmem-svc", "folder/zmem-svc", ".", ""])
def test_release_asset_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(ValueError, match="name"):
        ReleaseAsset.from_mapping(
            {
                "target": "x86_64-unknown-linux-musl",
                "name": name,
                "size": 1,
                "sha256": "0" * 64,
            }
        )


def test_copy_verified_streams_and_rejects_integrity_failures(tmp_path: Path) -> None:
    data = b"zmem"
    asset = ReleaseAsset.from_mapping(
        {
            "target": "x86_64-unknown-linux-musl",
            "name": "zmem-svc-x86_64-unknown-linux-musl",
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    )
    destination = tmp_path / asset.name
    copy_verified(io.BytesIO(data), destination, asset)
    assert destination.read_bytes() == data

    with pytest.raises(ValueError, match="size"):
        copy_verified(io.BytesIO(data + b"!"), tmp_path / "oversize", asset)
    with pytest.raises(ValueError, match="SHA-256"):
        bad = ReleaseAsset(asset.target, asset.name, asset.size, "0" * 64)
        copy_verified(io.BytesIO(data), tmp_path / "bad", bad)


def test_local_discovery_can_report_absence_without_weakening_strict_sources(tmp_path: Path) -> None:
    assert find_service_binary(None, environ={}, package_root=tmp_path, which=lambda _: None) is None
    with pytest.raises(FileNotFoundError, match="ZMEM_SVC_SOURCE"):
        find_service_binary(
            None,
            environ={"ZMEM_SVC_SOURCE": str(tmp_path / "missing")},
            package_root=tmp_path,
            which=lambda _: None,
        )
